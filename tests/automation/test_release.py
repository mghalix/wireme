"""Tests for repository release automation."""

from datetime import date
from pathlib import Path

import pytest

from scripts.release import (
    Bump,
    _bump_version,
    _default_changelog,
    _prepare_changelog,
    _prepare_release,
    _read_project_version,
    _release_notes,
    _ReleaseError,
    _verify_tag,
)


@pytest.mark.parametrize(
    ("bump", "expected"),
    [
        ("patch", "0.1.2"),
        ("minor", "0.2.0"),
        ("major", "1.0.0"),
    ],
)
def test_bump_version_uses_semver(bump: Bump, expected: str) -> None:
    # Given
    current = "0.1.1"

    # When
    actual = _bump_version(current, bump)

    # Then
    assert actual == expected


def test_prepare_changelog_moves_unreleased_changes() -> None:
    # Given
    changelog = "# Changelog\n\n## Unreleased\n\n- A change.\n\n## 0.1.1 - 2026-07-16\n"

    # When
    actual = _prepare_changelog(changelog, "0.1.2", date(2026, 7, 17))

    # Then
    assert actual == (
        "# Changelog\n\n"
        "## Unreleased\n\n"
        "## 0.1.2 - 2026-07-17\n\n"
        "- A change.\n\n"
        "## 0.1.1 - 2026-07-16\n"
    )


def test_prepare_changelog_rejects_empty_unreleased_section() -> None:
    # Given
    changelog = "# Changelog\n\n## Unreleased\n\n## 0.1.1 - 2026-07-16\n"

    # When / Then
    with pytest.raises(_ReleaseError, match="no Unreleased changes"):
        _prepare_changelog(changelog, "0.1.2", date(2026, 7, 17))


def test_prepare_changelog_preserves_bracketed_release_headings() -> None:
    # Given
    changelog = (
        "# Release Notes\n\n## Unreleased\n\n- A change.\n\n## [0.4.3] - 2026-07-17\n"
    )

    # When
    actual = _prepare_changelog(changelog, "0.4.4", date(2026, 7, 18))

    # Then
    assert "## [0.4.4] - 2026-07-18" in actual
    assert _release_notes(actual, "0.4.4") == "- A change.\n"


def test_default_changelog_supports_release_notes_name(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Given
    release_notes = tmp_path / "release-notes.md"
    release_notes.write_text("# Release Notes\n")
    monkeypatch.chdir(tmp_path)

    # When
    actual = _default_changelog()

    # Then
    assert actual == Path("release-notes.md")


def test_prepare_release_updates_uv_project_and_changelog(tmp_path: Path) -> None:
    # Given
    project = tmp_path / "pyproject.toml"
    project.write_text(
        '[project]\nname = "demo"\nversion = "0.1.1"\nrequires-python = ">=3.12"\n'
    )
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text("# Changelog\n\n## Unreleased\n\n- New release.\n")

    # When
    actual = _prepare_release(
        project,
        changelog,
        "patch",
        date(2026, 7, 17),
    )

    # Then
    assert actual == "0.1.2"
    assert _read_project_version(project) == "0.1.2"
    assert "## 0.1.2 - 2026-07-17" in changelog.read_text()
    assert (tmp_path / "uv.lock").is_file()


def test_release_notes_extracts_requested_version() -> None:
    # Given
    changelog = (
        "# Changelog\n\n"
        "## Unreleased\n\n"
        "## 0.1.2 - 2026-07-17\n\n"
        "- New release.\n\n"
        "## 0.1.1 - 2026-07-16\n\n"
        "- Previous release.\n"
    )

    # When
    actual = _release_notes(changelog, "0.1.2")

    # Then
    assert actual == "- New release.\n"


def test_verify_tag_checks_version_and_release_notes(tmp_path: Path) -> None:
    # Given
    project = tmp_path / "pyproject.toml"
    project.write_text('[project]\nname = "demo"\nversion = "0.1.2"\n')
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text(
        "# Changelog\n\n## Unreleased\n\n## 0.1.2 - 2026-07-17\n\n- New release.\n"
    )

    # When
    _verify_tag(project, changelog, "v", "v0.1.2")

    # Then
    assert _read_project_version(project) == "0.1.2"


def test_verify_tag_rejects_mismatched_tag(tmp_path: Path) -> None:
    # Given
    project = tmp_path / "pyproject.toml"
    project.write_text('[project]\nname = "demo"\nversion = "0.1.2"\n')
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text("# Changelog\n\n## Unreleased\n")

    # When / Then
    with pytest.raises(_ReleaseError, match="does not match expected tag"):
        _verify_tag(project, changelog, "v", "v0.2.0")
