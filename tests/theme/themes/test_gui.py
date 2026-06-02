"""Tests for `GuiTheme` — desktop-git-GUI look: table layout + Fork palette."""

from gitsvg.parse import parse_jsonl_text
from gitsvg.state import apply_ops
from gitsvg.theme import BranchLineStyle, CommitLabelLayout, MergeCommitStyle, Orientation
from gitsvg.theme.themes import GuiTheme


# ==================================================================================================
#  Resolved field values
# ==================================================================================================
def test_gui_theme_build_resolves_table_layout_and_tight_spacing() -> None:
    """`GuiTheme.build({})` resolves the GUI-defining layout policy and the tight spacings."""
    # --- arrange / act ----------------
    theme = GuiTheme.build({})

    # --- assert -----------------------
    assert theme.orientation == Orientation.BT
    assert theme.commit_label_layout is CommitLabelLayout.TABLE
    assert theme.auto_lane_change is True
    assert theme.branch_spacing == 15
    assert theme.commit_spacing == 25


def test_gui_theme_tunes_table_region() -> None:
    """The message column is halved and a faint mid-gray row band is enabled."""
    # --- arrange / act ----------------
    theme = GuiTheme.build({})

    # --- assert -----------------------
    assert theme.table_msg_width == 240  # half the default 480
    assert theme.commit_row_band_color == "#8080800D"  # mid-gray at 0.05 alpha
    assert theme.commit_stroke_width == 0  # flat dots, no white ring
    assert theme.commit_radius == 3  # small ordinary dots
    assert theme.merge_commit_radius == 5  # merges stay prominent
    assert theme.highlight_radius == 4  # modest bump over the ordinary dot
    assert theme.branch_guide_color == "#b8b8b880"  # default gray at half opacity


def test_gui_theme_matches_hash_typography_to_message() -> None:
    """The hash column shares the commit-message size and color — no secondary-line de-emphasis."""
    # --- arrange / act ----------------
    theme = GuiTheme.build({})

    # --- assert -----------------------
    assert theme.hash_font_size == theme.label_font_size
    assert theme.hash_color == theme.label_color


def test_gui_theme_inherits_bezier_and_checkmark() -> None:
    """The two other GUI-defining traits are `DefaultTheme` values, inherited not overridden."""
    # --- arrange / act ----------------
    theme = GuiTheme.build({})

    # --- assert -----------------------
    assert theme.branch_line_style is BranchLineStyle.BEZIER
    assert theme.merge_commit_style is MergeCommitStyle.CHECKMARK


def test_gui_theme_uses_fork_palette() -> None:
    """`main` takes Fork's first lane color; the cycle carries the twelve `branch*` slots in order."""
    # --- arrange / act ----------------
    theme = GuiTheme.build({})

    # --- assert -----------------------
    assert theme.colors["main"] == "#FF9502"  # Fork lane 0 (orange)
    assert theme.colors["branch1"] == "#FFCC00"  # yellow
    assert theme.colors["branch12"] == "#FF6F61"  # coral
    assert GuiTheme._resolve_default_branch_color_cycle() == [f"branch{i}" for i in range(1, 13)]


# ==================================================================================================
#  Cascade — `{name: "gui"}` selects GuiTheme and validates cleanly in table mode
# ==================================================================================================
def test_theme_op_name_gui_resolves_through_apply_without_table_errors() -> None:
    """A `theme:` op with `name: "gui"` resolves through `GuiTheme` and raises no table-mode error.

    Table mode forbids horizontal orientations (E223) and an explicit
    `commit_row_mode: shared` (E224); `gui` is vertical and leaves the
    row mode to `split()`, so a clean diagram validates.
    """
    # --- arrange ----------------------
    source = (
        '{"op": "theme", "name": "gui"}\n'
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "first"}\n'
    )

    # --- act --------------------------
    parsed, report = parse_jsonl_text(source, file="x.jsonl")
    _, theme = apply_ops(parsed, report)

    # --- assert -----------------------
    assert report.is_clean()
    assert theme.commit_label_layout is CommitLabelLayout.TABLE
    assert theme.colors["main"] == "#FF9502"
