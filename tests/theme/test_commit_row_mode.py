"""Resolution + split-routing tests for `theme.commit_row_mode`."""

from gitsvg._shared.value_types import CommitRowMode
from gitsvg.parse import parse_jsonl_text
from gitsvg.state import apply_ops
from gitsvg.theme import DefaultTheme


def test_default_commit_row_mode_is_shared() -> None:
    # --- arrange / act ----------------
    theme = DefaultTheme.build({})

    # --- assert -----------------------
    assert theme.commit_row_mode is CommitRowMode.SHARED


def test_explicit_commit_row_mode_overrides_default() -> None:
    # --- arrange / act ----------------
    theme = DefaultTheme.build({"commit_row_mode": CommitRowMode.UNIQUE})

    # --- assert -----------------------
    assert theme.commit_row_mode is CommitRowMode.UNIQUE


def test_commit_row_mode_routes_into_layout_settings() -> None:
    """`Theme.split()` carries `commit_row_mode` onto the layout slice, not just the renderer slice."""
    # --- arrange ----------------------
    theme = DefaultTheme.build({"commit_row_mode": CommitRowMode.UNIQUE})

    # --- act --------------------------
    layout_settings, _renderer_settings = theme.split()

    # --- assert -----------------------
    assert layout_settings.commit_row_mode is CommitRowMode.UNIQUE


def test_commit_row_mode_resolves_through_apply() -> None:
    """A `theme:` op with `commit_row_mode` ends up on the resolved theme."""
    # --- arrange / act ----------------
    parsed, report = parse_jsonl_text('{"op": "theme", "commit_row_mode": "unique"}\n', file="x.jsonl")
    _, theme = apply_ops(parsed, report)

    # --- assert -----------------------
    assert report.is_clean()
    assert theme.commit_row_mode is CommitRowMode.UNIQUE
