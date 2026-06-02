"""Canonical default theme — every field's default-resolution logic.

`DefaultTheme` is the concrete `Theme` subclass selected when no
`theme:` op chooses a different `name`. It supplies a `_resolve_*`
classmethod per field needing default-logic and an eager `build()`
classmethod that orchestrates resolution in dependency order.

Resolution is eager and single-pass: `build()` resolves
`orientation` first, then every field that depends on `orientation`
(or other already-resolved fields). Inter-field dependencies are
explicit method arguments at the call site. Subclasses override
individual `_resolve_*` methods to vary a field's default; `build()`
is inherited and picks the override via `cls.*` dispatch.

Static fields (orientation-invariant constants) still get a
`_resolve_*` method — the method-per-field uniformity makes overrides
in future subclasses syntactically identical regardless of whether
the original was orientation-dependent.
"""

from typing import Any, Self

from gitsvg.theme._box_anchor import BoxAnchor
from gitsvg.theme._branch_line_style import BranchLineStyle
from gitsvg.theme._commit_label_layout import CommitLabelLayout
from gitsvg.theme._commit_row_mode import CommitRowMode
from gitsvg.theme._merge_commit_style import MergeCommitStyle
from gitsvg.theme._orientation import Orientation
from gitsvg.theme._theme import Theme

# ==================================================================================================
#  Vertical-orientation set — used inside several `_resolve_*` methods.
# ==================================================================================================
_VERTICAL_ORIENTATIONS = frozenset({Orientation.BT, Orientation.TB})


class DefaultTheme(Theme):
    """The canonical default theme. Concrete `_resolve_*` methods + eager `build()`."""

    # --------------------------------------------------------------------------
    #  Orientation
    # --------------------------------------------------------------------------
    @classmethod
    def _resolve_orientation(cls) -> Orientation:
        """Default orientation — bottom-to-top."""
        return Orientation.BT

    # --------------------------------------------------------------------------
    #  Layout policy
    # --------------------------------------------------------------------------
    @classmethod
    def _resolve_commit_row_mode(cls) -> CommitRowMode:
        """Commit-row packing — `shared` (commits on different branches may share a row)."""
        return CommitRowMode.SHARED

    @classmethod
    def _resolve_auto_lane_change(cls) -> bool:
        """Branch-lane migration — off (each branch keeps its lane for its whole life)."""
        return False

    @classmethod
    def _resolve_merge_lane_clearance(cls) -> int:
        """Rows a merged / PR'd source holds its lane past its line — one (reserve through the merge row)."""
        return 1

    # --------------------------------------------------------------------------
    #  Spacings
    # --------------------------------------------------------------------------
    @classmethod
    def _resolve_branch_spacing(cls, orientation: Orientation) -> int:
        """Per-orientation `branch_spacing` default (px).

        Vertical orientations (`bt`, `tb`) get the wider `100` —
        branches stack horizontally, each lane needs horizontal room
        for labels. Horizontal orientations (`lr`, `rl`) use `75` —
        symmetric with `commit_spacing`, since commit labels sit
        above/below the branch line.
        """
        return 100 if orientation in _VERTICAL_ORIENTATIONS else 75

    @classmethod
    def _resolve_commit_spacing(cls, orientation: Orientation) -> int:
        """Per-orientation `commit_spacing` default (px).

        Vertical orientations get `50`; horizontal orientations get
        `75` (symmetric with `branch_spacing` — see
        `_resolve_branch_spacing`).
        """
        return 50 if orientation in _VERTICAL_ORIENTATIONS else 75

    # --------------------------------------------------------------------------
    #  Margins (depend on orientation + resolved spacings)
    # --------------------------------------------------------------------------
    @classmethod
    def _resolve_margin_left(cls, orientation: Orientation, branch_spacing: int, commit_spacing: int) -> int | float:
        """Per-orientation `margin_left` default (px).

        Vertical orientations anchor to `branch_spacing × 1.0`.
        Horizontal orientations anchor to `commit_spacing` — `lr`
        uses `×1.5` (timeline starts on the left; widened to fit the
        branch pill), `rl` uses `×1.0`.
        """
        if orientation in _VERTICAL_ORIENTATIONS:
            return _resolve_int_or_float(1.0 * branch_spacing)
        if orientation == Orientation.LR:
            return _resolve_int_or_float(1.5 * commit_spacing)
        return _resolve_int_or_float(1.0 * commit_spacing)

    @classmethod
    def _resolve_margin_right(cls, orientation: Orientation, branch_spacing: int, commit_spacing: int) -> int | float:
        """Per-orientation `margin_right` default (px).

        Mirror of `_resolve_margin_left`: vertical anchors to
        `branch_spacing × 1.0`; horizontal uses `commit_spacing` —
        `lr` uses `×1.0`, `rl` uses `×1.5` (timeline starts on the
        right; widened to fit the branch pill).
        """
        if orientation in _VERTICAL_ORIENTATIONS:
            return _resolve_int_or_float(1.0 * branch_spacing)
        if orientation == Orientation.RL:
            return _resolve_int_or_float(1.5 * commit_spacing)
        return _resolve_int_or_float(1.0 * commit_spacing)

    @classmethod
    def _resolve_margin_top(cls, orientation: Orientation, branch_spacing: int, commit_spacing: int) -> int | float:
        """Per-orientation `margin_top` default (px).

        Vertical anchors to `commit_spacing × 0.5`; horizontal anchors
        to `branch_spacing × 1.0`.
        """
        if orientation in _VERTICAL_ORIENTATIONS:
            return _resolve_int_or_float(0.5 * commit_spacing)
        return _resolve_int_or_float(1.0 * branch_spacing)

    @classmethod
    def _resolve_margin_bottom(cls, orientation: Orientation, branch_spacing: int, commit_spacing: int) -> int | float:
        """Per-orientation `margin_bottom` default (px). Mirror of `_resolve_margin_top`."""
        if orientation in _VERTICAL_ORIENTATIONS:
            return _resolve_int_or_float(0.5 * commit_spacing)
        return _resolve_int_or_float(1.0 * branch_spacing)

    # --------------------------------------------------------------------------
    #  Strokes & geometry (mostly static)
    # --------------------------------------------------------------------------
    @classmethod
    def _resolve_branch_line_width(cls) -> int:
        """Stroke width (px) of branch lines and arcs."""
        return 2

    @classmethod
    def _resolve_commit_radius(cls) -> int:
        """Commit-dot radius (px)."""
        return 5

    @classmethod
    def _resolve_commit_stroke_width(cls) -> float:
        """Stroke width (px) of the white outline around a commit dot."""
        return 1.5

    @classmethod
    def _resolve_highlight_radius(cls) -> int:
        """Highlighted-commit-dot radius (px)."""
        return 7

    @classmethod
    def _resolve_merge_commit_radius(cls, commit_radius: int) -> int:
        """Merge-commit-dot radius (px) — defaults to the resolved `commit_radius` (including a theme-overridden value), so merge and ordinary dots match unless `merge_commit_radius` is set explicitly."""
        return commit_radius

    @classmethod
    def _resolve_arc_corner_radius_in_grid_units(cls) -> float:
        """Corner radius for branch-off / merge arcs, as a multiple of `min(branch_spacing, commit_spacing)`."""
        return 0.4

    @classmethod
    def _resolve_branch_line_style(cls) -> BranchLineStyle:
        """Connector shape between lanes — the single flowing bezier curve."""
        return BranchLineStyle.BEZIER

    @classmethod
    def _resolve_merge_commit_style(cls) -> MergeCommitStyle:
        """Merge-commit dot style — a checkmark inside the dot."""
        return MergeCommitStyle.CHECKMARK

    @classmethod
    def _resolve_label_offset_branch_axis_in_lanes(cls, orientation: Orientation) -> float:
        """Per-orientation label offset along the branch axis (as a multiple of `branch_spacing`).

        Vertical orientations use `0.12`; horizontal orientations use
        `0.24` — twice the lane ratio compensates for the smaller
        horizontal `branch_spacing`, so the resolved pixel offset stays
        close to the vertical default.
        """
        return 0.12 if orientation in _VERTICAL_ORIENTATIONS else 0.24

    @classmethod
    def _resolve_branch_guide_width(cls) -> float:
        """Stroke width (px) of the faint per-lane vertical guides."""
        return 0.7

    @classmethod
    def _resolve_branch_guide_dash(cls) -> str:
        """SVG `stroke-dasharray` for the branch guides."""
        return "4,4"

    @classmethod
    def _resolve_guide_overshoot_in_rows(cls, orientation: Orientation) -> float:
        """Per-orientation guide-overshoot ratio (as a multiple of `commit_spacing`).

        Vertical orientations use `0.25`; horizontal orientations use
        `0.5` — the larger reach covers the branch-pill area in the
        asymmetrically-wider start-side margin.
        """
        return 0.25 if orientation in _VERTICAL_ORIENTATIONS else 0.5

    # --------------------------------------------------------------------------
    #  Typography
    # --------------------------------------------------------------------------
    @classmethod
    def _resolve_label_font_family(cls) -> str:
        """Default CSS `font-family` chain for all text elements."""
        return "'Inter', 'Helvetica Neue', Helvetica, Arial, sans-serif"

    @classmethod
    def _resolve_label_font_family_small(cls) -> str:
        """Compact font-family chain emitted under `--small`."""
        return "Inter, sans-serif"

    @classmethod
    def _resolve_label_font_size(cls) -> float:
        """Font size (px) for commit-message labels."""
        return 11

    @classmethod
    def _resolve_branch_label_font_size(cls) -> float:
        """Font size (px) for branch-name pills and PR title pills."""
        return 11

    @classmethod
    def _resolve_hash_font_size(cls) -> float:
        """Font size (px) for the secondary hash line on commit labels."""
        return 9

    @classmethod
    def _resolve_branch_name_pill_offset_commit_axis_in_rows(cls, orientation: Orientation) -> float:
        """Per-orientation branch-pill commit-axis offset (signed).

        Vertical: `-0.5` rows below the branch start (pill sits below
        the start commit). Horizontal: `-0.25` rows back along the
        commit axis from the start (the pill is edge-anchored on its
        near side, so this is the minimum gap; the pill extends
        further into the start-side margin).
        """
        return -0.5 if orientation in _VERTICAL_ORIENTATIONS else -0.25

    @classmethod
    def _resolve_branch_name_pill_offset_branch_axis_in_lanes(cls, orientation: Orientation) -> float:
        """Per-orientation branch-pill branch-axis offset (signed).

        `0.0` in every orientation — centered on the branch lane.
        """
        del orientation  # not orientation-dependent today; the signature accepts it for future overrides
        return 0.0

    @classmethod
    def _resolve_pill_padding_x_in_font_sizes(cls) -> float:
        """Extra pill width beyond rendered text, as a multiple of `branch_label_font_size`."""
        return 12 / 11

    @classmethod
    def _resolve_pill_padding_y_in_font_sizes(cls) -> float:
        """Extra pill height beyond font size, as a multiple of `branch_label_font_size`."""
        return 8 / 11

    @classmethod
    def _resolve_pill_corner_radius_in_font_sizes(cls) -> float:
        """Pill rounded-corner radius, as a multiple of `branch_label_font_size`."""
        return 4 / 11

    @classmethod
    def _resolve_label_line_padding_in_font_sizes(cls) -> float:
        """Extra height per line in a multi-line stack, as a multiple of `label_font_size`."""
        return 4 / 11

    # --------------------------------------------------------------------------
    #  Pull-request visuals
    # --------------------------------------------------------------------------
    @classmethod
    def _resolve_pull_request_dash(cls) -> str:
        """SVG `stroke-dasharray` for pull-request arcs."""
        return "2,6"

    @classmethod
    def _resolve_pull_request_pill_offset_commit_axis_in_rows(cls, orientation: Orientation) -> float:
        """Per-orientation PR-pill commit-axis offset (signed).

        Anchor is the phantom point on the source branch line at the
        projected merge target's commit-axis position. Vertical:
        `-0.5` — pill sits half a row back from the merge row toward
        the source tip. Horizontal: `0.0` — pill stays on the merge
        row, offset along the branch axis instead (see
        `_resolve_pull_request_pill_offset_branch_axis_in_lanes`).
        """
        return -0.5 if orientation in _VERTICAL_ORIENTATIONS else 0.0

    @classmethod
    def _resolve_pull_request_pill_offset_branch_axis_in_lanes(cls, orientation: Orientation) -> float:
        """Per-orientation PR-pill branch-axis offset (signed).

        Vertical: `0.0` — centered on the source branch's lane.
        Horizontal: `-0.5` — pill sits half a lane above the source
        branch line at the merge column.
        """
        return 0.0 if orientation in _VERTICAL_ORIENTATIONS else -0.5

    # --------------------------------------------------------------------------
    #  Label angles
    # --------------------------------------------------------------------------
    @classmethod
    def _resolve_branch_label_angle(cls, orientation: Orientation) -> float:
        """Per-orientation branch-pill rotation default (degrees).

        `0°` across all orientations today — labels always horizontally
        readable. Subclasses may pair non-zero defaults with anchor
        choices that read well together.
        """
        del orientation
        return 0.0

    @classmethod
    def _resolve_commit_label_angle(cls, orientation: Orientation) -> float:
        """Per-orientation commit-label-stack rotation default (degrees). `0°` today."""
        del orientation
        return 0.0

    @classmethod
    def _resolve_pull_request_label_angle(cls, orientation: Orientation) -> float:
        """Per-orientation PR-pill rotation default (degrees). `0°` today."""
        del orientation
        return 0.0

    # --------------------------------------------------------------------------
    #  Box anchors (text-bearing primitives)
    # --------------------------------------------------------------------------
    @classmethod
    def _resolve_branch_pill_anchor(cls, orientation: Orientation) -> BoxAnchor:
        """Per-orientation branch-pill `(u, v)`.

        Vertical orientations (`bt`, `tb`): pill centered on the world
        point — `(0.5, 0.5)`. Horizontal orientations: pill anchored on
        its edge nearest the start commit, so the resolved offset
        becomes a minimum gap and a long branch name extends further
        into the start-side margin without crowding the start commit
        dot. `lr` → right-edge anchored (`(1.0, 0.5)`); `rl` → left-
        edge anchored (`(0.0, 0.5)`).
        """
        if orientation == Orientation.LR:
            return (1.0, 0.5)
        if orientation == Orientation.RL:
            return (0.0, 0.5)
        return (0.5, 0.5)

    @classmethod
    def _resolve_pull_request_pill_anchor(cls, orientation: Orientation) -> BoxAnchor:
        """Per-orientation PR-pill `(u, v)`.

        Always `(0.5, 0.5)` — the PR pill's offset point lives away
        from the start-side margin concern the branch pill addresses,
        so it centers on the offset point in every orientation.
        """
        del orientation
        return (0.5, 0.5)

    @classmethod
    def _resolve_commit_label_anchor_before(cls, orientation: Orientation) -> BoxAnchor:
        """Per-orientation commit-label `(u, v)` for the `before` (lower-index) side.

        Vertical orientations (`bt`, `tb`): stack extends to the left
        of the commit dot, vertically centered — `(1.0, 0.5)` puts the
        stack's right-middle at the world point. Horizontal
        orientations (`lr`, `rl`): stack extends below the dot,
        horizontally centered — `(0.5, 1.0)` puts the stack's bottom-
        middle at the world point.
        """
        if orientation in _VERTICAL_ORIENTATIONS:
            return (1.0, 0.5)
        return (0.5, 1.0)

    @classmethod
    def _resolve_commit_label_anchor_after(cls, orientation: Orientation) -> BoxAnchor:
        """Per-orientation commit-label `(u, v)` for the `after` (higher-index) side.

        Mirror of `_resolve_commit_label_anchor_before`. Vertical:
        stack extends to the right, vertically centered — `(0.0, 0.5)`.
        Horizontal: stack extends above the dot, horizontally centered
        — `(0.5, 0.0)`.
        """
        if orientation in _VERTICAL_ORIENTATIONS:
            return (0.0, 0.5)
        return (0.5, 0.0)

    # --------------------------------------------------------------------------
    #  Colors
    # --------------------------------------------------------------------------
    @classmethod
    def _resolve_colors(cls) -> dict[str, str]:
        """Default branch-color palette.

        Soft but not gray: `main` is a darkened blue-gray spine, and the
        four `branch*` slots are gently saturated green / blue / mauve /
        purple that stay legible without shouting. Hue is held across the
        whole palette relative to the `muted` named theme (the
        pre-refresh look); only `main`'s lightness and the four branches'
        saturation differ.
        """
        return {
            "main": "#4a4f5a",
            "branch1": "#56b393",
            "branch2": "#6b8bc2",
            "branch3": "#c06b8b",
            "branch4": "#977fc2",
        }

    @classmethod
    def _resolve_default_branch_color_cycle(cls) -> list[str]:
        """Default cycle of palette keys used to color non-main branches in declaration order."""
        return ["branch1", "branch2", "branch3", "branch4"]

    @classmethod
    def _resolve_label_color(cls) -> str:
        """Fill color for commit-message labels."""
        return "#383838"

    @classmethod
    def _resolve_hash_color(cls) -> str:
        """Fill color for the secondary hash line on commit labels."""
        return "#707070"

    @classmethod
    def _resolve_branch_guide_color(cls) -> str:
        """Stroke color for the faint per-lane vertical guides."""
        return "#b8b8b8"

    @classmethod
    def _resolve_commit_stroke_color(cls) -> str:
        """Stroke color for the outline around commit dots.

        Visually separates the dot from any branch line passing
        through it. `"white"` works for the default theme's
        transparent (or white-rendered) background; dark themes
        should override to their background color so the outline
        reads as a "carved out" gap rather than a bright halo.

        Under `merge_commit_style: checkmark` this color is also
        reused as the merge dot's fill (fill and stroke swap), so a
        dark theme's override flows through to the hollow merge dot.
        """
        return "white"

    @classmethod
    def _resolve_branch_label_bg_opacity(cls) -> float:
        """Background opacity for branch-name and PR title pills."""
        return 0.85

    # --------------------------------------------------------------------------
    #  Background
    # --------------------------------------------------------------------------
    @classmethod
    def _resolve_background_color(cls) -> str | None:
        """Full-canvas background color default — `None` keeps the SVG transparent."""
        return None

    # --------------------------------------------------------------------------
    #  Row banding
    # --------------------------------------------------------------------------
    @classmethod
    def _resolve_commit_row_band_color(cls) -> str | None:
        """Commit-row zebra-stripe fill default — `None` paints no bands."""
        return None

    # --------------------------------------------------------------------------
    #  Table layout
    # --------------------------------------------------------------------------
    @classmethod
    def _resolve_commit_label_layout(cls) -> CommitLabelLayout:
        """Label-placement default — `inline` (free-floating beside each dot)."""
        return CommitLabelLayout.INLINE

    @classmethod
    def _resolve_table_msg_width(cls) -> int:
        """Default message-column width (px) in table mode."""
        return 480

    @classmethod
    def _resolve_table_hash_width(cls) -> int:
        """Default hash-column width (px) in table mode."""
        return 64

    @classmethod
    def _resolve_table_cell_padding_x_in_font_sizes(cls) -> float:
        """Default table horizontal spacing unit — half a label font size."""
        return 0.5

    # --------------------------------------------------------------------------
    #  Factory
    # --------------------------------------------------------------------------
    @classmethod
    def build(cls, user_set: dict[str, Any]) -> Self:
        """Resolve a fully-populated `DefaultTheme` from explicitly-set fields.

        Resolution order honors field dependencies: orientation
        first, spacings next (depend on orientation), margins (depend
        on orientation + resolved spacings), then every other field —
        with any field other resolvers depend on hoisted ahead of its
        dependents (e.g. `commit_radius` is resolved early because
        `merge_commit_radius` defaults to it).

        Args:
            user_set: Mapping from field name to the value the user
                explicitly supplied. Fields absent from `user_set`
                fall through to the corresponding `_resolve_<field>`
                classmethod.

        Returns:
            A fully-populated `DefaultTheme` instance.
        """

        def pick(name: str, default_fn, *args) -> Any:
            """Return the user-set value for `name` if present, else `default_fn(*args)`."""
            return user_set[name] if name in user_set else default_fn(*args)

        # Dependency-ordered resolution.
        orientation = pick("orientation", cls._resolve_orientation)
        branch_spacing = pick("branch_spacing", cls._resolve_branch_spacing, orientation)
        commit_spacing = pick("commit_spacing", cls._resolve_commit_spacing, orientation)
        commit_radius = pick("commit_radius", cls._resolve_commit_radius)

        return cls(
            orientation=orientation,
            commit_row_mode=pick("commit_row_mode", cls._resolve_commit_row_mode),
            auto_lane_change=pick("auto_lane_change", cls._resolve_auto_lane_change),
            merge_lane_clearance=pick("merge_lane_clearance", cls._resolve_merge_lane_clearance),
            branch_spacing=branch_spacing,
            commit_spacing=commit_spacing,
            margin_left=pick("margin_left", cls._resolve_margin_left, orientation, branch_spacing, commit_spacing),
            margin_right=pick("margin_right", cls._resolve_margin_right, orientation, branch_spacing, commit_spacing),
            margin_top=pick("margin_top", cls._resolve_margin_top, orientation, branch_spacing, commit_spacing),
            margin_bottom=pick(
                "margin_bottom", cls._resolve_margin_bottom, orientation, branch_spacing, commit_spacing
            ),
            branch_line_width=pick("branch_line_width", cls._resolve_branch_line_width),
            commit_radius=commit_radius,
            commit_stroke_width=pick("commit_stroke_width", cls._resolve_commit_stroke_width),
            highlight_radius=pick("highlight_radius", cls._resolve_highlight_radius),
            merge_commit_radius=pick("merge_commit_radius", cls._resolve_merge_commit_radius, commit_radius),
            arc_corner_radius_in_grid_units=pick(
                "arc_corner_radius_in_grid_units", cls._resolve_arc_corner_radius_in_grid_units
            ),
            branch_line_style=pick("branch_line_style", cls._resolve_branch_line_style),
            merge_commit_style=pick("merge_commit_style", cls._resolve_merge_commit_style),
            label_offset_branch_axis_in_lanes=pick(
                "label_offset_branch_axis_in_lanes", cls._resolve_label_offset_branch_axis_in_lanes, orientation
            ),
            branch_guide_width=pick("branch_guide_width", cls._resolve_branch_guide_width),
            branch_guide_dash=pick("branch_guide_dash", cls._resolve_branch_guide_dash),
            guide_overshoot_in_rows=pick("guide_overshoot_in_rows", cls._resolve_guide_overshoot_in_rows, orientation),
            label_font_family=pick("label_font_family", cls._resolve_label_font_family),
            label_font_family_small=pick("label_font_family_small", cls._resolve_label_font_family_small),
            label_font_size=pick("label_font_size", cls._resolve_label_font_size),
            branch_label_font_size=pick("branch_label_font_size", cls._resolve_branch_label_font_size),
            hash_font_size=pick("hash_font_size", cls._resolve_hash_font_size),
            branch_name_pill_offset_commit_axis_in_rows=pick(
                "branch_name_pill_offset_commit_axis_in_rows",
                cls._resolve_branch_name_pill_offset_commit_axis_in_rows,
                orientation,
            ),
            branch_name_pill_offset_branch_axis_in_lanes=pick(
                "branch_name_pill_offset_branch_axis_in_lanes",
                cls._resolve_branch_name_pill_offset_branch_axis_in_lanes,
                orientation,
            ),
            pill_padding_x_in_font_sizes=pick(
                "pill_padding_x_in_font_sizes", cls._resolve_pill_padding_x_in_font_sizes
            ),
            pill_padding_y_in_font_sizes=pick(
                "pill_padding_y_in_font_sizes", cls._resolve_pill_padding_y_in_font_sizes
            ),
            pill_corner_radius_in_font_sizes=pick(
                "pill_corner_radius_in_font_sizes", cls._resolve_pill_corner_radius_in_font_sizes
            ),
            label_line_padding_in_font_sizes=pick(
                "label_line_padding_in_font_sizes", cls._resolve_label_line_padding_in_font_sizes
            ),
            pull_request_dash=pick("pull_request_dash", cls._resolve_pull_request_dash),
            pull_request_pill_offset_commit_axis_in_rows=pick(
                "pull_request_pill_offset_commit_axis_in_rows",
                cls._resolve_pull_request_pill_offset_commit_axis_in_rows,
                orientation,
            ),
            pull_request_pill_offset_branch_axis_in_lanes=pick(
                "pull_request_pill_offset_branch_axis_in_lanes",
                cls._resolve_pull_request_pill_offset_branch_axis_in_lanes,
                orientation,
            ),
            branch_label_angle=pick("branch_label_angle", cls._resolve_branch_label_angle, orientation),
            commit_label_angle=pick("commit_label_angle", cls._resolve_commit_label_angle, orientation),
            pull_request_label_angle=pick(
                "pull_request_label_angle", cls._resolve_pull_request_label_angle, orientation
            ),
            branch_pill_anchor=pick("branch_pill_anchor", cls._resolve_branch_pill_anchor, orientation),
            pull_request_pill_anchor=pick(
                "pull_request_pill_anchor", cls._resolve_pull_request_pill_anchor, orientation
            ),
            commit_label_anchor_before=pick(
                "commit_label_anchor_before", cls._resolve_commit_label_anchor_before, orientation
            ),
            commit_label_anchor_after=pick(
                "commit_label_anchor_after", cls._resolve_commit_label_anchor_after, orientation
            ),
            colors=pick("colors", cls._resolve_colors),
            default_branch_color_cycle=pick("default_branch_color_cycle", cls._resolve_default_branch_color_cycle),
            label_color=pick("label_color", cls._resolve_label_color),
            hash_color=pick("hash_color", cls._resolve_hash_color),
            branch_guide_color=pick("branch_guide_color", cls._resolve_branch_guide_color),
            commit_stroke_color=pick("commit_stroke_color", cls._resolve_commit_stroke_color),
            branch_label_bg_opacity=pick("branch_label_bg_opacity", cls._resolve_branch_label_bg_opacity),
            background_color=pick("background_color", cls._resolve_background_color),
            commit_row_band_color=pick("commit_row_band_color", cls._resolve_commit_row_band_color),
            commit_label_layout=pick("commit_label_layout", cls._resolve_commit_label_layout),
            table_msg_width=pick("table_msg_width", cls._resolve_table_msg_width),
            table_hash_width=pick("table_hash_width", cls._resolve_table_hash_width),
            table_cell_padding_x_in_font_sizes=pick(
                "table_cell_padding_x_in_font_sizes", cls._resolve_table_cell_padding_x_in_font_sizes
            ),
        )


def _resolve_int_or_float(value: float) -> int | float:
    """Cast a whole-number float to int; return float otherwise.

    Used by the margin resolvers so the SVG attribute formatting stays
    stable across whole-number cases (drawsvg writes integer values
    without a decimal point and float values with one).
    """
    return int(value) if value == int(value) else value
