"""Compute the renderer's pixel-space canvas from the layout grid + theme.

The renderer needs concrete pixel dimensions for the SVG it emits:
canvas `width` / `height` and the effective spacings / margins the
coordinate transform multiplies into grid indices. `compute_canvas`
takes the grid extent (from `Layout.grid`, i.e. `LayoutGrid`) plus
the resolved theme, and walks an axis-relative auto-fit pass: four
helpers compute the pixel allowance along each axis edge
(branch-axis lower/upper, commit-axis lower/upper), then a single
visual-side mapping table converts those to (margin_left,
margin_right, margin_top, margin_bottom) per orientation.

This module lives in `render/` because it's purely pixel work. The
layout engine never reads it.
"""

from dataclasses import dataclass
from typing import Literal

from gitsvg.file_format import LabelSide
from gitsvg.layout import Layout
from gitsvg.render._label_widths import commit_label_width, pill_height, pill_width
from gitsvg.render._renderer_settings import RendererSettings
from gitsvg.render._table import compute_table_columns
from gitsvg.theme import CommitLabelLayout, Orientation

# Auto-fit safety margin between content (pill / outward label) and the canvas
# edge — keeps the rendered geometry from butting right up against the SVG
# bounding box. Deliberately not a `Theme` field: when a user wants more
# breathing room, the relevant `margin_*` theme field is the right knob to
# turn — this internal perceptual pad just prevents zero-margin clipping in
# the auto-fit path, and never needs per-diagram tuning.
_AUTO_FIT_EDGE_PAD_PX = 4.0  # axis-symmetric (perceptual)

_AxisEdge = Literal["lower", "upper"]

# Maps each orientation to the visual side each axis edge corresponds
# to. Mirrors the `label_side` axis-index → pixel-side mapping pattern
# from invariant #7 (`docs/architecture.md`): axis-relative reasoning
# everywhere; orientation enters once at the boundary.
_AXIS_TO_VISUAL: dict[Orientation, dict[str, str]] = {
    Orientation.BT: {"branch_lower": "left", "branch_upper": "right", "commit_lower": "bottom", "commit_upper": "top"},
    Orientation.TB: {"branch_lower": "left", "branch_upper": "right", "commit_lower": "top", "commit_upper": "bottom"},
    Orientation.LR: {"branch_lower": "top", "branch_upper": "bottom", "commit_lower": "left", "commit_upper": "right"},
    Orientation.RL: {"branch_lower": "top", "branch_upper": "bottom", "commit_lower": "right", "commit_upper": "left"},
}


@dataclass(slots=True)
class RenderCanvas:
    """Computed pixel-space canvas the renderer's coordinate transform reads from.

    Spacings, margins, and orientation flow from the resolved theme;
    slot counts flow from `Layout.grid` (the `LayoutGrid`, populated
    from `state.grid` if pinned, otherwise auto-fit).

    Margin attributes name visual sides of the canvas, not axis-index
    sides — they always refer to the same screen edge regardless of
    orientation. The geometry module reads `orientation` to map grid
    indices to pixel coordinates per the four-orientation rule.

    Attributes:
        width: SVG canvas width in pixels.
        height: SVG canvas height in pixels.
        n_commits: Effective commit-axis slot count (pinned via `grid.n_commits`
            or auto-fit from content).
        n_branches: Effective branch-axis slot count.
        branch_spacing: Effective pixel distance between adjacent branch-axis slots.
        commit_spacing: Effective pixel distance between adjacent commit-axis slots.
        margin_left: Effective pixel margin at the visually-left canvas edge.
        margin_right: Effective pixel margin at the visually-right canvas edge.
        margin_bottom: Effective pixel margin at the visually-bottom canvas edge.
        margin_top: Effective pixel margin at the visually-top canvas edge.
        orientation: Active orientation (`bt`, `tb`, `lr`, `rl`). Drives
            the geometry module's grid → pixel mapping.
        table_x_origin: Pixel x of the table region's left edge when table
            mode is active (right of the graph, past a fixed gap); `0` when
            no table region is present.
    """

    width: float  # axis-symmetric (visual)
    height: float  # axis-symmetric (visual)
    n_commits: int  # axis-bound: commit-axis (slot count)
    n_branches: int  # axis-bound: branch-axis (slot count)
    branch_spacing: float  # axis-bound: branch-axis
    commit_spacing: float  # axis-bound: commit-axis
    margin_left: float  # axis-symmetric (visual-side, px)
    margin_right: float  # axis-symmetric (visual-side, px)
    margin_bottom: float  # axis-symmetric (visual-side, px)
    margin_top: float  # axis-symmetric (visual-side, px)
    orientation: Orientation  # axis-symmetric (selector)
    table_x_origin: float = 0.0  # axis-symmetric (visual, px); 0 when no table region


def is_table_active(theme: RendererSettings) -> bool:
    """Return whether the table label layout is active and supported.

    Table mode draws only in vertical orientations (`bt` / `tb`); a
    horizontal orientation with `commit_label_layout: table` is a rejected
    combination (E223) and falls back to the inline layout here, so the
    renderer and canvas treat it as inactive.

    Args:
        theme: The resolved theme.

    Returns:
        True when `commit_label_layout` is `table` and the orientation is
        vertical.
    """
    return theme.commit_label_layout == CommitLabelLayout.TABLE and theme.orientation.is_vertical


def compute_canvas(layout: Layout, theme: RendererSettings) -> RenderCanvas:
    """Compute the effective `RenderCanvas` for `layout` under `theme`.

    Margins auto-fit to the longest visible labels and pills via four
    axis-relative helpers + a per-orientation visual-side mapping;
    spacings and default margins come from the resolved theme (the
    `theme:` op is the only source for those, per invariant #6).

    Args:
        layout: The completed layout, supplying the integer-grid extent
            (`n_commits`, `n_branches`) and the entities (branches,
            commits, PRs) that drive the auto-fit margin computation.
        theme: The resolved theme, supplying spacings and default
            margins plus the font sizes used in label-width estimation.

    Returns:
        A `RenderCanvas` carrying the pixel-space width / height and the
        effective spacing / margin values the coordinate transform reads.
    """
    grid = layout.grid
    orientation = theme.orientation

    branch_spacing = theme.branch_spacing
    commit_spacing = theme.commit_spacing

    n_commits = grid.n_commits
    n_branches = grid.n_branches

    # Axis-relative auto-fit needs (pure: no notion of visual sides).
    axis_needs: dict[str, float] = {
        "branch_lower": _auto_fit_branch_axis_edge(layout, theme, edge="lower"),
        "branch_upper": _auto_fit_branch_axis_edge(layout, theme, edge="upper"),
        "commit_lower": _auto_fit_commit_axis_edge(layout, theme, edge="lower"),
        "commit_upper": _auto_fit_commit_axis_edge(layout, theme, edge="upper"),
    }

    # Map axis-relative needs to visual sides per orientation; take the
    # wider of the theme default and the computed need on each side.
    # Force-cast to float so the coordinate transform's `y = margin_top
    # + ...` formula propagates float type into y attributes drawsvg
    # emits, keeping the SVG output stable across orientations.
    margins: dict[str, float] = {
        "left": float(theme.margin_left),
        "right": float(theme.margin_right),
        "top": float(theme.margin_top),
        "bottom": float(theme.margin_bottom),
    }
    for axis_edge, visual_side in _AXIS_TO_VISUAL[orientation].items():
        margins[visual_side] = max(margins[visual_side], axis_needs[axis_edge])

    is_vertical = orientation.is_vertical
    table_x_origin = 0.0
    if is_vertical:
        graph_extent = (n_branches - 1) * branch_spacing
        width = margins["left"] + graph_extent + margins["right"]
        height = margins["top"] + (n_commits - 1) * commit_spacing + margins["bottom"]
        # Table mode appends a self-bounded region to the right of the graph,
        # past a gap of half a branch-lane; the branch-axis margins stay at
        # their defaults (the relocated labels/pills are suppressed in the
        # auto-fit pass).
        if is_table_active(theme):
            table_width = compute_table_columns(theme.table_msg_width, theme.table_hash_width, gutter=0).width
            if table_width > 0:
                graph_table_gap = branch_spacing / 2
                table_x_origin = margins["left"] + graph_extent + graph_table_gap
                width = table_x_origin + table_width + margins["right"]
    else:
        width = margins["left"] + (n_commits - 1) * commit_spacing + margins["right"]
        height = margins["top"] + (n_branches - 1) * branch_spacing + margins["bottom"]
    return RenderCanvas(
        width=width,
        height=height,
        n_commits=n_commits,
        n_branches=n_branches,
        branch_spacing=branch_spacing,
        commit_spacing=commit_spacing,
        margin_left=margins["left"],
        margin_right=margins["right"],
        margin_bottom=margins["bottom"],
        margin_top=margins["top"],
        orientation=orientation,
        table_x_origin=table_x_origin,
    )


# ==================================================================================================
#  Branch-axis auto-fit
# ==================================================================================================
def _auto_fit_branch_axis_edge(layout: Layout, theme: RendererSettings, *, edge: _AxisEdge) -> float:
    """Pixel allowance for content protruding past a branch-axis edge.

    The branch-axis edges are perpendicular to the lane direction —
    `edge="lower"` is lane 0, `edge="upper"` is the maximum-index
    lane. Considers two sources:

    - Outward-pointing commit labels on the edge lane. Text extends
      along the branch axis from the label anchor, in the same
      direction the edge faces.
    - Edge-lane branch-name pills. The pill rect's extent along the
      branch axis depends on orientation: in vertical orientations
      the rect is centered horizontally over the lane line so the
      half-pill-width protrudes; in horizontal orientations the rect
      is anchored along the commit axis (rect width runs along the
      commit axis, height along the branch axis), so the half-pill-
      height protrudes along the branch axis.

    Args:
        layout: Supplies branches and commits to walk.
        theme: Supplies font sizes, label offset, and the orientation
            that drives the pill-extent branch.
        edge: Which branch-axis edge to compute.

    Returns:
        Pixel allowance needed past the edge; returns 0 if nothing
        on the edge protrudes.
    """
    # Table mode relocates the commit labels and branch pills into the table
    # region, so neither protrudes past a branch-axis edge — the margins stay
    # at their theme defaults and the table region (added by `compute_canvas`)
    # is the only right-side allowance.
    if is_table_active(theme):
        return 0.0

    branches = layout.branches
    commit_layouts = layout.commits
    max_branch_pos = max((seg.lane for b in branches for seg in b.segments), default=0)
    target_lane = 0 if edge == "lower" else max_branch_pos
    matching_label_side = LabelSide.BEFORE if edge == "lower" else LabelSide.AFTER

    is_vertical = theme.orientation.is_vertical
    pill_h = pill_height(theme)

    needed: float = 0.0
    for branch in branches:
        if branch.start_lane == target_lane:
            extent = (pill_width(branch.name, theme) / 2) if is_vertical else (pill_h / 2)
            needed = max(needed, extent + _AUTO_FIT_EDGE_PAD_PX)
    for commit in commit_layouts.values():
        if commit.branch_pos == target_lane and theme.branch_label_side(commit.branch_id) == matching_label_side:
            extent = theme.label_offset + commit_label_width(commit, theme)
            needed = max(needed, extent + _AUTO_FIT_EDGE_PAD_PX)
    return needed


# ==================================================================================================
#  Commit-axis auto-fit
# ==================================================================================================
def _auto_fit_commit_axis_edge(layout: Layout, theme: RendererSettings, *, edge: _AxisEdge) -> float:
    """Pixel allowance for content protruding past a commit-axis edge.

    The commit-axis edges run along the commit-axis direction —
    `edge="lower"` is commit row 0, `edge="upper"` is the maximum
    commit row. Considers two sources:

    - Branch-name pills at branch starts. Default offset is negative
      along the commit axis in every orientation, so branches with
      `start == 0` protrude past the lower edge; an override making
      the offset positive would shift the case to a branch with
      `start == max_commit_pos`.
    - PR-title pills at projected merge rows. Default offset is
      negative along the commit axis in vertical orientations and
      zero in horizontal orientations; positive overrides shift the
      case to the upper edge.

    The pill's extent past its anchor depends on orientation: in
    vertical orientations the rect is centered on the anchor so the
    half-pill-height extends along the commit axis; in horizontal
    orientations the rect's near-edge is anchored at the offset
    point so the full pill_width extends in the offset direction
    along the commit axis.

    Args:
        layout: Supplies branches and PRs to walk.
        theme: Supplies offset fields, font sizes, and the
            orientation that drives the pill-extent branch.
        edge: Which commit-axis edge to compute.

    Returns:
        Pixel allowance needed past the edge; returns 0 if nothing
        on the edge protrudes.
    """
    is_vertical = theme.orientation.is_vertical
    pill_h = pill_height(theme)
    max_commit_pos = layout.grid.n_commits - 1

    needed: float = 0.0

    # Branch-name pills. Skipped in table mode — branch names move to the
    # table's tip pills, so the branch-start pill no longer protrudes here.
    # PR-title pills (below) still render in table mode, so they stay.
    branch_offset_rows = theme.branch_name_pill_offset_commit_axis_in_rows
    if not is_table_active(theme) and branch_offset_rows != 0:
        protrudes_at = "lower" if branch_offset_rows < 0 else "upper"
        if edge == protrudes_at:
            target_start = 0 if edge == "lower" else max_commit_pos
            offset_px = abs(branch_offset_rows) * theme.commit_spacing
            for branch in layout.branches:
                if branch.start == target_start:
                    extent = offset_px + (pill_h / 2 if is_vertical else pill_width(branch.name, theme))
                    needed = max(needed, extent + _AUTO_FIT_EDGE_PAD_PX)

    # PR-title pills (only branches with a non-None title render a pill).
    pr_offset_rows = theme.pull_request_pill_offset_commit_axis_in_rows
    if pr_offset_rows != 0:
        protrudes_at = "lower" if pr_offset_rows < 0 else "upper"
        if edge == protrudes_at:
            target_pos = 0 if edge == "lower" else max_commit_pos
            offset_px = abs(pr_offset_rows) * theme.commit_spacing
            for pr in layout.pull_requests:
                if pr.title is None or pr.trunk_point.commit_pos != target_pos:
                    continue
                extent = offset_px + (pill_h / 2 if is_vertical else pill_width(pr.title, theme))
                needed = max(needed, extent + _AUTO_FIT_EDGE_PAD_PX)

    return needed
