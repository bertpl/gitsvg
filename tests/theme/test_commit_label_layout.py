"""Resolution / split-routing / apply tests for `theme.commit_label_layout`.

Table mode forces `commit_row_mode → unique` at the `Theme.split()`
boundary; the layout engine never sees `commit_label_layout` itself.
"""

from gitsvg._shared.value_types import CommitLabelLayout, CommitRowMode
from gitsvg.parse import parse_jsonl_text
from gitsvg.state import apply_ops
from gitsvg.theme import DefaultTheme


def test_default_commit_label_layout_is_inline() -> None:
    # --- arrange / act ----------------
    theme = DefaultTheme.build({})

    # --- assert -----------------------
    assert theme.commit_label_layout is CommitLabelLayout.INLINE


def test_explicit_commit_label_layout_overrides_default() -> None:
    # --- arrange / act ----------------
    theme = DefaultTheme.build({"commit_label_layout": CommitLabelLayout.TABLE})

    # --- assert -----------------------
    assert theme.commit_label_layout is CommitLabelLayout.TABLE


def test_table_mode_forces_unique_row_mode_at_split() -> None:
    """With no `commit_row_mode` set, table mode resolves the layout slice to `unique`."""
    # --- arrange ----------------------
    theme = DefaultTheme.build({"commit_label_layout": CommitLabelLayout.TABLE})

    # --- act --------------------------
    layout_settings, _renderer_settings = theme.split()

    # --- assert -----------------------
    assert layout_settings.commit_row_mode is CommitRowMode.UNIQUE


def test_table_mode_forces_unique_even_over_explicit_shared() -> None:
    """Table mode overrides an explicit `shared` at the layout boundary (the conflict is flagged separately by E224)."""
    # --- arrange ----------------------
    theme = DefaultTheme.build(
        {"commit_label_layout": CommitLabelLayout.TABLE, "commit_row_mode": CommitRowMode.SHARED}
    )

    # --- act --------------------------
    layout_settings, _renderer_settings = theme.split()

    # --- assert -----------------------
    assert layout_settings.commit_row_mode is CommitRowMode.UNIQUE


def test_inline_mode_leaves_row_mode_untouched_at_split() -> None:
    """Outside table mode, `split()` passes `commit_row_mode` through unchanged."""
    # --- arrange ----------------------
    theme = DefaultTheme.build({})  # inline default, commit_row_mode default shared

    # --- act --------------------------
    layout_settings, _renderer_settings = theme.split()

    # --- assert -----------------------
    assert layout_settings.commit_row_mode is CommitRowMode.SHARED


def test_commit_label_layout_resolves_through_apply() -> None:
    """A `theme:` op with `commit_label_layout` ends up on the resolved theme."""
    # --- arrange / act ----------------
    parsed, report = parse_jsonl_text('{"op": "theme", "commit_label_layout": "table"}\n', file="x.jsonl")
    _, theme = apply_ops(parsed, report)

    # --- assert -----------------------
    assert report.is_clean()
    assert theme.commit_label_layout is CommitLabelLayout.TABLE
