"""Gui theme — mimics a desktop git GUI (Fork) in table layout.

`GuiTheme` reproduces the look of a desktop git client: the graph sits
on the left, a table of per-commit metadata (message + hash columns)
runs beside it, and each branch's name rides as a colored pill at its
tip commit. The branch palette is Fork's own graph-lane colors (Apple
system colors), extracted from the app's asset catalog.

Two of the GUI-defining traits are already `DefaultTheme` values and
inherit unchanged — the checkmark merge dots (`merge_commit_style`) and
the single flowing bezier connector (`branch_line_style`). They are
*deliberately* not overridden here; the GUI look depends on them, but
the default already supplies them.

The graph is packed tight: `auto_lane_change` compacts live branches
into the lowest lanes, and the spacings are smaller than every other
named theme, since table mode moves the labels out of the graph region
so the lanes no longer need to clear free-floating text.
"""

from gitsvg.theme._commit_label_layout import CommitLabelLayout
from gitsvg.theme._default_theme import DefaultTheme
from gitsvg.theme._orientation import Orientation


class GuiTheme(DefaultTheme):
    """Desktop-git-GUI look (Fork) — table layout with the Fork palette.

    Overrides the layout policy (`_resolve_commit_label_layout` →
    `table`, `_resolve_auto_lane_change` → on), the spacings
    (`_resolve_branch_spacing` / `_resolve_commit_spacing`, tighter than
    every other theme), the hash typography (`_resolve_hash_font_size` /
    `_resolve_hash_color`, matched to the commit-message line), and the
    palette (`_resolve_colors` / `_resolve_default_branch_color_cycle`,
    Fork's graph-lane colors). Checkmark merge dots and the bezier
    connector inherit from `DefaultTheme`. Stays vertical — table mode
    forbids horizontal orientations (E223).
    """

    # --------------------------------------------------------------------------
    #  Layout policy
    # --------------------------------------------------------------------------
    @classmethod
    def _resolve_commit_label_layout(cls) -> CommitLabelLayout:
        """Table layout — the GUI look: graph left, metadata table right, branch names as tip pills."""
        return CommitLabelLayout.TABLE

    @classmethod
    def _resolve_auto_lane_change(cls) -> bool:
        """Compact the graph — live branches migrate into the lowest free lanes, as a desktop GUI does."""
        return True

    # --------------------------------------------------------------------------
    #  Spacings
    # --------------------------------------------------------------------------
    @classmethod
    def _resolve_branch_spacing(cls, orientation: Orientation) -> int:
        """Per-orientation `branch_spacing` (px) — `15`, tighter than every other theme.

        Table mode moves branch pills and commit labels out of the graph
        region, so the lanes carry only dots and connectors and can pack
        far closer than the label-clearing widths the other themes need.
        Only the vertical orientations are reachable (table mode rejects
        horizontal via E223); the horizontal value is inherited and
        never resolved for this theme.
        """
        return 15 if orientation.is_vertical else super()._resolve_branch_spacing(orientation)

    @classmethod
    def _resolve_commit_spacing(cls, orientation: Orientation) -> int:
        """Per-orientation `commit_spacing` (px) — `25`, a row pitch the metadata table and its bands read well at."""
        return 25 if orientation.is_vertical else super()._resolve_commit_spacing(orientation)

    # --------------------------------------------------------------------------
    #  Table region — message column + row bands
    # --------------------------------------------------------------------------
    @classmethod
    def _resolve_table_msg_width(cls) -> int:
        """Message-column width (px) — `240`, half the default; messages here are short branch-summary lines."""
        return 240

    @classmethod
    def _resolve_commit_row_band_color(cls) -> str | None:
        """Faint mid-gray zebra stripe on alternate commit rows — `#808080` at `0.05` alpha (`0x0D`), barely-there row tracking."""
        return "#8080800D"

    # --------------------------------------------------------------------------
    #  Commit dots
    # --------------------------------------------------------------------------
    @classmethod
    def _resolve_commit_stroke_width(cls) -> float:
        """No dot outline — flat filled dots, the desktop-GUI look (the default `1.5` white ring is dropped)."""
        return 0

    @classmethod
    def _resolve_commit_radius(cls) -> int:
        """Small ordinary-commit dots (`3`, down from the default `5`) — keeps the dense graph from feeling heavy."""
        return 3

    @classmethod
    def _resolve_merge_commit_radius(cls, commit_radius: int) -> int:
        """Merge dots stay at `5` (independent of the smaller ordinary-dot `commit_radius`) so merges read as the structural anchors."""
        return 5

    @classmethod
    def _resolve_highlight_radius(cls) -> int:
        """Highlighted-dot radius `4` (down from the default `7`) — a modest bump over the `3` ordinary dot, not a jump."""
        return 4

    # --------------------------------------------------------------------------
    #  Branch guides
    # --------------------------------------------------------------------------
    @classmethod
    def _resolve_branch_guide_color(cls) -> str:
        """The default guide gray at half opacity (`#b8b8b880`) — the dense lanes read better with fainter guides."""
        return "#b8b8b880"

    # --------------------------------------------------------------------------
    #  Hash typography — matched to the commit-message line
    # --------------------------------------------------------------------------
    @classmethod
    def _resolve_hash_font_size(cls) -> float:
        """Hash-column font size — equal to the commit-message size, so the two table columns share one type scale."""
        return cls._resolve_label_font_size()

    @classmethod
    def _resolve_hash_color(cls) -> str:
        """Hash-column color — equal to the commit-message color, dropping the secondary-line de-emphasis in table layout."""
        return cls._resolve_label_color()

    # --------------------------------------------------------------------------
    #  Palette — Fork's graph-lane colors
    # --------------------------------------------------------------------------
    @classmethod
    def _resolve_colors(cls) -> dict[str, str]:
        """Fork's graph-lane palette (Apple system colors).

        Lifted from the Fork app's asset catalog — the saturated
        graph-lane colors it draws ref labels and lanes in. `main` takes
        the first lane color; the twelve `branch*` slots carry the rest
        in Fork's index order, cycled by
        `_resolve_default_branch_color_cycle` in branch-declaration
        order.
        """
        return {
            "main": "#FF9502",  # orange
            "branch1": "#FFCC00",  # yellow
            "branch2": "#FF3B30",  # red
            "branch3": "#A2845E",  # brown
            "branch4": "#64DA38",  # green
            "branch5": "#1CADF8",  # blue
            "branch6": "#CB73E1",  # purple
            "branch7": "#8E8E91",  # gray
            "branch8": "#FF2968",  # pink
            "branch9": "#30D5C8",  # teal
            "branch10": "#5856D6",  # indigo
            "branch11": "#B4D435",  # lime
            "branch12": "#FF6F61",  # coral
        }

    @classmethod
    def _resolve_default_branch_color_cycle(cls) -> list[str]:
        """Cycle the twelve non-`main` Fork colors in index order across non-main branches."""
        return [f"branch{i}" for i in range(1, 13)]
