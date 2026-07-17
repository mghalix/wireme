"""Prepare and validate releases for a standard uv Python project."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tomllib
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Final, Literal, cast

type Bump = Literal["major", "minor", "patch"]

_DEFAULT_PROJECT_FILE: Final = Path("pyproject.toml")
_CHANGELOG_CANDIDATES: Final = (Path("CHANGELOG.md"), Path("release-notes.md"))
_DEFAULT_TAG_PREFIX: Final = "v"
_SEMVER_PATTERN: Final = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
_HEADING_PATTERN: Final = re.compile(r"(?m)^## (?P<title>[^\r\n]+?)[ \t]*$")
_PLAIN_RELEASE_PATTERN: Final = re.compile(r"^\d+\.\d+\.\d+ - \d{4}-\d{2}-\d{2}$")
_BRACKETED_RELEASE_PATTERN: Final = re.compile(
    r"^\[\d+\.\d+\.\d+\] - \d{4}-\d{2}-\d{2}$"
)


class _ReleaseError(RuntimeError):
    """Raised when repository release state is invalid."""


@dataclass(frozen=True)
class _Section:
    """A second-level changelog section."""

    title: str
    start: int
    body_start: int
    end: int


def _parse_version(version: str) -> tuple[int, int, int]:
    match = _SEMVER_PATTERN.fullmatch(version)
    if match is None:
        message = f"Invalid version {version!r}; expected X.Y.Z"
        raise _ReleaseError(message)
    major, minor, patch = match.groups()
    return int(major), int(minor), int(patch)


def _bump_version(version: str, bump: Bump) -> str:
    major, minor, patch = _parse_version(version)
    if bump == "major":
        return f"{major + 1}.0.0"
    if bump == "minor":
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"


def _read_project_version(project_file: Path) -> str:
    data = cast(dict[str, object], tomllib.loads(project_file.read_text()))
    project = data.get("project")
    if not isinstance(project, dict):
        message = f"{project_file} has no [project] table"
        raise _ReleaseError(message)

    project_data = cast(dict[str, object], project)
    version = project_data.get("version")
    if not isinstance(version, str):
        message = f"{project_file} has no static [project].version"
        raise _ReleaseError(message)

    _parse_version(version)
    return version


def _sections(content: str) -> list[_Section]:
    matches = list(_HEADING_PATTERN.finditer(content))
    return [
        _Section(
            title=match.group("title"),
            start=match.start(),
            body_start=match.end(),
            end=matches[index + 1].start()
            if index + 1 < len(matches)
            else len(content),
        )
        for index, match in enumerate(matches)
    ]


def _default_changelog() -> Path:
    return next(
        (path for path in _CHANGELOG_CANDIDATES if path.is_file()),
        _CHANGELOG_CANDIDATES[0],
    )


def _unreleased_section(content: str) -> _Section:
    matches = [
        section for section in _sections(content) if section.title == "Unreleased"
    ]
    if len(matches) != 1:
        message = "CHANGELOG.md must contain exactly one '## Unreleased' section"
        raise _ReleaseError(message)
    return matches[0]


def _version_section(content: str, version: str) -> _Section:
    escaped_version = re.escape(version)
    title_pattern = re.compile(
        rf"^(?:{escaped_version}|\[{escaped_version}\]) - \d{{4}}-\d{{2}}-\d{{2}}$"
    )
    matches = [
        section
        for section in _sections(content)
        if title_pattern.fullmatch(section.title)
    ]
    if len(matches) != 1:
        message = f"CHANGELOG.md must contain exactly one release section for {version}"
        raise _ReleaseError(message)
    return matches[0]


def _release_title(content: str, version: str, release_date: date) -> str:
    for section in _sections(content):
        if _BRACKETED_RELEASE_PATTERN.fullmatch(section.title):
            return f"[{version}] - {release_date.isoformat()}"
        if _PLAIN_RELEASE_PATTERN.fullmatch(section.title):
            break
    return f"{version} - {release_date.isoformat()}"


def _prepare_changelog(content: str, version: str, release_date: date) -> str:
    unreleased = _unreleased_section(content)
    changes = content[unreleased.body_start : unreleased.end].strip()
    if not changes:
        raise _ReleaseError("CHANGELOG.md has no Unreleased changes")

    if any(
        section.title in {version, f"[{version}]"}
        or section.title.startswith((f"{version} - ", f"[{version}] - "))
        for section in _sections(content)
    ):
        message = f"CHANGELOG.md already contains a section for {version}"
        raise _ReleaseError(message)

    title = _release_title(content, version, release_date)
    prepared = f"## Unreleased\n\n## {title}\n\n{changes}\n\n"
    return f"{content[: unreleased.start]}{prepared}{content[unreleased.end :]}"


def _release_notes(content: str, version: str) -> str:
    section = _version_section(content, version)
    notes = content[section.body_start : section.end].strip()
    if not notes:
        message = f"CHANGELOG.md release section for {version} is empty"
        raise _ReleaseError(message)
    return f"{notes}\n"


def _prepare_release(
    project_file: Path,
    changelog: Path,
    bump: Bump,
    release_date: date,
) -> str:
    if project_file.name != "pyproject.toml":
        raise _ReleaseError("uv projects must use a pyproject.toml project file")

    current_version = _read_project_version(project_file)
    next_version = _bump_version(current_version, bump)
    prepared_changelog = _prepare_changelog(
        changelog.read_text(), next_version, release_date
    )

    uv = shutil.which("uv")
    if uv is None:
        raise _ReleaseError("uv is required to prepare a release")

    # The version is constrained to numeric SemVer before it reaches uv.
    subprocess.run(  # noqa: S603
        [
            uv,
            "version",
            next_version,
            "--no-sync",
            "--project",
            str(project_file.parent),
        ],
        check=True,
    )
    actual_version = _read_project_version(project_file)
    if actual_version != next_version:
        message = f"uv wrote version {actual_version}, expected {next_version}"
        raise _ReleaseError(message)

    changelog.write_text(prepared_changelog)
    return next_version


def _verify_tag(project_file: Path, changelog: Path, prefix: str, tag: str) -> None:
    version = _read_project_version(project_file)
    expected_tag = f"{prefix}{version}"
    if tag != expected_tag:
        message = f"Release tag {tag!r} does not match expected tag {expected_tag!r}"
        raise _ReleaseError(message)
    _release_notes(changelog.read_text(), version)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prepare and validate a uv project's release metadata."
    )
    parser.add_argument(
        "--project-file",
        type=Path,
        default=_DEFAULT_PROJECT_FILE,
        help="project metadata file (default: pyproject.toml)",
    )
    parser.add_argument(
        "--changelog",
        type=Path,
        default=_default_changelog(),
        help="changelog file (default: CHANGELOG.md or release-notes.md)",
    )
    parser.add_argument(
        "--tag-prefix",
        default=_DEFAULT_TAG_PREFIX,
        help="release tag prefix (default: v)",
    )

    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser(
        "prepare", help="bump the version and move Unreleased changes into a release"
    )
    prepare.add_argument("bump", choices=("patch", "minor", "major"))
    prepare.add_argument(
        "--date",
        default=date.today().isoformat(),
        help="release date in YYYY-MM-DD format (default: today)",
    )
    commands.add_parser("current-version", help="print the project version")
    commands.add_parser("release-tag", help="print the expected release tag")
    notes = commands.add_parser("release-notes", help="print one release's notes")
    notes.add_argument("--version", help="version to read (default: current version)")
    verify = commands.add_parser(
        "verify-tag", help="verify a tag against project metadata and the changelog"
    )
    verify.add_argument("tag")
    return parser


def main(arguments: Sequence[str] | None = None) -> int:
    """Run the release helper command.

    Args:
        arguments: Command arguments without the executable name. Uses
            ``sys.argv`` when omitted.

    Returns:
        Zero on success, or one when release state is invalid.
    """
    namespace = _parser().parse_args(arguments)
    project_file = cast(Path, namespace.project_file)
    changelog = cast(Path, namespace.changelog)
    tag_prefix = cast(str, namespace.tag_prefix)
    command = cast(str, namespace.command)

    try:
        if command == "prepare":
            bump = cast(Bump, namespace.bump)
            release_date = date.fromisoformat(cast(str, namespace.date))
            print(
                _prepare_release(
                    project_file,
                    changelog,
                    bump,
                    release_date,
                )
            )
        elif command == "current-version":
            print(_read_project_version(project_file))
        elif command == "release-tag":
            print(f"{tag_prefix}{_read_project_version(project_file)}")
        elif command == "release-notes":
            requested_version = cast(str | None, namespace.version)
            version = requested_version or _read_project_version(project_file)
            print(_release_notes(changelog.read_text(), version), end="")
        elif command == "verify-tag":
            _verify_tag(
                project_file,
                changelog,
                tag_prefix,
                cast(str, namespace.tag),
            )
        else:  # pragma: no cover - argparse constrains command names.
            raise _ReleaseError(f"Unknown command {command!r}")
    except (OSError, ValueError, subprocess.CalledProcessError, _ReleaseError) as error:
        print(f"release: error: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
