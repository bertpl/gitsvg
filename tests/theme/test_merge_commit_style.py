"""Resolution tests for `theme.merge_commit_style`."""

from gitsvg.theme import DefaultTheme, MergeCommitStyle


def test_default_merge_commit_style_is_circle() -> None:
    # --- arrange / act ----------------
    theme = DefaultTheme.build({})

    # --- assert -----------------------
    assert theme.merge_commit_style is MergeCommitStyle.CIRCLE


def test_explicit_merge_commit_style_overrides_default() -> None:
    # --- arrange / act ----------------
    theme = DefaultTheme.build({"merge_commit_style": MergeCommitStyle.CHECKMARK})

    # --- assert -----------------------
    assert theme.merge_commit_style is MergeCommitStyle.CHECKMARK
