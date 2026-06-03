"""Compact theme — denser layout for dashboards / inline use.

`CompactTheme` shrinks spacings and fonts to produce a visibly tighter
diagram while keeping the same visual vocabulary. Colors, anchors,
label angles, and pull-request visuals inherit unchanged — only the
metrics that govern density change.

The reduction is moderate (~25-30 % tighter spacing, ~10 % smaller fonts)
to keep text readable at the new scale. Font-anchored ratios
(pill padding, label line padding) automatically shrink with the
smaller fonts, so pill proportions stay coherent without separate
overrides. Margins anchor to spacings and shrink the same way.
"""

from gitsvg._shared.value_types import Orientation
from gitsvg.theme._default_theme import DefaultTheme


class CompactTheme(DefaultTheme):
    """Denser variant of `DefaultTheme`.

    Overrides the metric resolvers (`_resolve_branch_spacing`,
    `_resolve_commit_spacing`, the three font sizes, and the two pill
    offsets) plus the layout-policy resolvers that suit a dense layout:
    `_resolve_auto_lane_change` (on, so branches compact into the lowest
    lanes) and `_resolve_merge_lane_clearance` (`0`, the tightest packing).
    `_resolve_branch_line_style` keeps the same bezier connector as the
    default. Every other field, including the refreshed palette and the
    checkmark merge dots, inherits from `DefaultTheme`.
    """

    @classmethod
    def _resolve_auto_lane_change(cls) -> bool:
        """Compact the graph — branches migrate into the lowest free lanes (dense layouts want this on)."""
        return True

    @classmethod
    def _resolve_merge_lane_clearance(cls) -> int:
        """No clearance past a merge — the tightest packing; the bezier connector reads cleanly even so."""
        return 0

    @classmethod
    def _resolve_branch_spacing(cls, orientation: Orientation) -> int:
        """Per-orientation `branch_spacing` (px) — tighter than `DefaultTheme`.

        Vertical orientations: `75` (was `100`) — wide enough that a
        commit label clears the adjacent lane once `auto_lane_change`
        packs branches together. Horizontal orientations: `55` (was `75`)
        — kept equal to `commit_spacing` so the horizontal layout stays
        symmetric, matching the `DefaultTheme` invariant.
        """
        return 75 if orientation.is_vertical else 55

    @classmethod
    def _resolve_commit_spacing(cls, orientation: Orientation) -> int:
        """Per-orientation `commit_spacing` (px) — ~30 % tighter than `DefaultTheme`.

        Vertical: `35` (was `50`). Horizontal: `55` (was `75`,
        symmetric with `branch_spacing`).
        """
        return 35 if orientation.is_vertical else 55

    @classmethod
    def _resolve_label_font_size(cls) -> float:
        """Commit-message font size — `9.5`, the half-step below `DefaultTheme`'s `11` that keeps long messages from crowding the tighter rows."""
        return 9.5

    @classmethod
    def _resolve_branch_label_font_size(cls) -> float:
        """Branch-name / PR pill font size, one step down from `DefaultTheme`'s `11`."""
        return 10.0

    @classmethod
    def _resolve_hash_font_size(cls) -> float:
        """Hash-line font size, one step down from `DefaultTheme`'s `9`."""
        return 8.0

    @classmethod
    def _resolve_branch_name_pill_offset_commit_axis_in_rows(cls, orientation: Orientation) -> float:
        """Per-orientation branch-pill commit-axis offset (signed).

        Vertical: `-0.65` (was `-0.5`) — nudges the pill slightly
        further below the start commit so the smaller text breathes
        against the tighter rows. Horizontal: inherited `-0.25`
        (edge-anchored, no adjustment needed).
        """
        if orientation.is_vertical:
            return -0.65
        return -0.25

    @classmethod
    def _resolve_pull_request_pill_offset_commit_axis_in_rows(cls, orientation: Orientation) -> float:
        """Per-orientation PR-pill commit-axis offset (signed).

        Vertical: `-0.35` (was `-0.5`) — nudges the pill in the
        opposite direction so the title breathes away from the
        merge endpoint. Horizontal: inherited `0.0`.
        """
        if orientation.is_vertical:
            return -0.35
        return 0.0
