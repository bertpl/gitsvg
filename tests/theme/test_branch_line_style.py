"""Resolution tests for `theme.branch_line_style`."""

from gitsvg.theme import BranchLineStyle, DefaultTheme


def test_default_branch_line_style_is_rounded() -> None:
    # --- arrange / act ----------------
    theme = DefaultTheme.build({})

    # --- assert -----------------------
    assert theme.branch_line_style is BranchLineStyle.ROUNDED


def test_explicit_branch_line_style_overrides_default() -> None:
    # --- arrange / act ----------------
    theme = DefaultTheme.build({"branch_line_style": BranchLineStyle.STRAIGHT})

    # --- assert -----------------------
    assert theme.branch_line_style is BranchLineStyle.STRAIGHT
