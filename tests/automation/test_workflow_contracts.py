"""Tests for repository workflow contracts."""

from pathlib import Path
from typing import Final

_ROOT: Final[Path] = Path(__file__).parents[2]


def test_draft_release_uses_locked_just() -> None:
    # Given
    project = (_ROOT / "pyproject.toml").read_text()
    workflow = (_ROOT / ".github/workflows/create-draft-release.yml").read_text()

    # When
    has_locked_just = '"rust-just>=1.56.0,<2"' in project
    uses_locked_just = "uv run --no-sync just release-check" in workflow

    # Then
    assert has_locked_just
    assert uses_locked_just


def test_draft_release_manual_retry_is_default_branch_only() -> None:
    # Given
    workflow = (_ROOT / ".github/workflows/create-draft-release.yml").read_text()

    # When
    has_manual_trigger = "  workflow_dispatch:\n" in workflow
    restricts_default_branch = (
        "github.ref_name == github.event.repository.default_branch" in workflow
    )
    binds_target_to_workflow_sha = (
        "github.event_name == 'workflow_dispatch' && github.sha" in workflow
    )

    # Then
    assert has_manual_trigger
    assert restricts_default_branch
    assert binds_target_to_workflow_sha
