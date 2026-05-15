"""Compute the renderer's pixel-space canvas from the layout grid + theme.

The renderer needs concrete pixel dimensions for the SVG it emits:
canvas `width` / `height` and the effective spacings / margins the
coordinate transform multiplies into grid indices. `compute_canvas`
takes the grid extent (from `Layout.grid`, i.e. `LayoutGrid`) plus
the resolved theme, and walks the same auto-fit rule the layout engine
used to: keep the canvas just big enough to contain the longest visible
labels, the branch-name pills, and any open pull-request's projected
merge-commit row.

This module lives in `render/` because it's purely pixel work. The
layout engine never reads it.
"""

from dataclasses import dataclass

from gitsvg.layout import Layout, LayoutBranch, LayoutCommit
from gitsvg.render._label_widths import commit_label_width, pill_width
from gitsvg.theme import Theme

# Auto-fit safety margin between content (pill / outward label) and the canvas
# edge — keeps the rendered geometry from butting right up against the SVG
# bounding box. Deliberately not a `Theme` field: when a user wants more
# breathing room, the relevant `margin_*` theme field is the right knob to
# turn — this internal perceptual pad just prevents zero-margin clipping in
# the auto-fit path, and never needs per-diagram tuning.
_AUTO_FIT_EDGE_PAD_PX = 4.0  # axis-symmetric (perceptual)


@dataclass(slots=True)
class RenderCanvas:
    """Computed pixel-space canvas the renderer's coordinate transform reads from.

    Spacings and margins flow from the resolved theme; slot counts
    flow from `Layout.grid` (the `LayoutGrid`, populated from
    `state.grid` if pinned, otherwise auto-fit).

    Margin attributes name visual sides of the canvas, not axis-index
    sides. The renderer's coordinate transform maps grid indices to
    pixel coordinates per `theme.orientation` (currently bottom-to-top
    only); the four margins always refer to the same screen edge
    regardless of orientation.

    Attributes:
        width: SVG canvas width in pixels.
        height: SVG canvas height in pixels.
        n_commits: Effective commit-axis slot count (pinned via `grid.n_commits`
            or auto-fit from content). Needed by the coordinate transform
            because the bottom-to-top orientation places index 0 at the
            largest y.
        n_branches: Effective branch-axis slot count.
        branch_spacing: Effective pixel distance between adjacent branch-axis slots.
        commit_spacing: Effective pixel distance between adjacent commit-axis slots.
        margin_left: Effective pixel margin at the visually-left canvas edge.
        margin_right: Effective pixel margin at the visually-right canvas edge.
        margin_bottom: Effective pixel margin at the visually-bottom canvas edge.
        margin_top: Effective pixel margin at the visually-top canvas edge.
    """

    width: float  # axis-bound: branch-axis
    height: float  # axis-bound: commit-axis
    n_commits: int  # axis-bound: commit-axis (slot count)
    n_branches: int  # axis-bound: branch-axis (slot count)
    branch_spacing: float  # axis-bound: branch-axis
    commit_spacing: float  # axis-bound: commit-axis
    margin_left: float  # axis-symmetric (visual-side, px)
    margin_right: float  # axis-symmetric (visual-side, px)
    margin_bottom: float  # axis-symmetric (visual-side, px)
    margin_top: float  # axis-symmetric (visual-side, px)


def compute_canvas(layout: Layout, theme: Theme) -> RenderCanvas:
    """Compute the effective `RenderCanvas` for `layout` under `theme`.

    Margins auto-fit to the longest visible labels and pills; spacings
    and default margins come from the resolved theme (the `theme:` op
    is the only source for those, per invariant #6).

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
    branches = layout.branches
    commit_layouts = layout.commits
    pull_requests = layout.pull_requests
    grid = layout.grid

    branch_spacing = theme.branch_spacing
    commit_spacing = theme.commit_spacing

    n_commits = grid.n_commits
    n_branches = grid.n_branches
    max_branch_pos = max((b.branch_pos for b in branches), default=0)

    margin_left = _auto_fit_margin_branch_axis(branches, commit_layouts, theme, branch_pos_filter=0, side="left")
    margin_right = _auto_fit_margin_branch_axis(
        branches, commit_layouts, theme, branch_pos_filter=max_branch_pos, side="right"
    )
    margin_bottom = _auto_fit_margin_commit_axis_lower(branches, theme)
    # `margin_top` is the one margin always promoted to float — the
    # coordinate transform's `y = margin_top + ...` propagates the type
    # into every y attribute drawsvg emits, and the rendered baseline
    # expects float y formatting throughout.
    margin_top = float(theme.margin_top)

    width = margin_left + (n_branches - 1) * branch_spacing + margin_right
    height = margin_top + (n_commits - 1) * commit_spacing + margin_bottom
    return RenderCanvas(
        width=width,
        height=height,
        n_commits=n_commits,
        n_branches=n_branches,
        branch_spacing=branch_spacing,
        commit_spacing=commit_spacing,
        margin_left=margin_left,
        margin_right=margin_right,
        margin_bottom=margin_bottom,
        margin_top=margin_top,
    )


def _auto_fit_margin_branch_axis(
    branches: list[LayoutBranch],
    commit_layouts: dict[str, LayoutCommit],
    theme: Theme,
    *,
    branch_pos_filter: int,
    side: str,
) -> float:
    """Compute the auto-fit margin for one branch-axis end (left or right).

    Considers the half-pill-width of any pill on the edge lane plus the
    width of any commit label whose `label_side` points outward from
    that lane.

    Args:
        branches: All layout branches; the edge-lane filter walks this
            list to find pills on `branch_pos_filter`.
        commit_layouts: All layout commits, walked the same way to find
            outward-pointing labels on the edge lane.
        theme: Supplies the default margin for the side, the
            `label_offset`, and the font sizes used to estimate label
            widths.
        branch_pos_filter: Lane index that counts as the "edge" — 0 on
            the left, max lane on the right.
        side: `"left"` or `"right"` — picks the matching default margin
            and the outward label-side value.

    Returns:
        The wider of the default margin and the computed need from the
        widest pill / outward label on the edge lane.
    """
    if side == "left":
        default = theme.margin_left
        outward_label_side = "before"
    else:
        default = theme.margin_right
        outward_label_side = "after"

    needed: float = 0.0
    for branch in branches:
        if branch.branch_pos == branch_pos_filter:
            needed = max(needed, pill_width(branch.name, theme) / 2 + _AUTO_FIT_EDGE_PAD_PX)
    for commit in commit_layouts.values():
        if commit.branch_pos == branch_pos_filter and commit.label_side == outward_label_side:
            needed = max(needed, theme.label_offset + commit_label_width(commit, theme) + _AUTO_FIT_EDGE_PAD_PX)
    return max(default, needed)


def _auto_fit_margin_commit_axis_lower(branches: list[LayoutBranch], theme: Theme) -> float:
    """Compute the auto-fit lower margin on the commit axis.

    The pill of any branch with `start = min(start)` sits closest to the
    canvas bottom. Reserve enough room for it: the absolute pixel
    distance from the branch's start row to the pill centre, plus half
    the pill height, plus a small edge pad.

    Args:
        branches: All layout branches; only their `start` values and the
            theme's pill geometry feed the computation.
        theme: Supplies the default lower margin, the pill offset, and
            the font size used to estimate pill height.

    Returns:
        The wider of the default lower margin and the room needed to
        keep the lowest pill inside the canvas.
    """
    if not branches:
        return theme.margin_bottom
    pill_height = theme.branch_label_font_size + theme.pill_padding_y
    # Bottom-to-top-orientation-only: the branch-name pill sits at a negative
    # commit-axis offset by default — i.e. below the anchor in screen y. The
    # bottom-margin auto-fit asks how far below the anchor the pill extends;
    # that's the absolute screen-y offset (= negation of the signed offset
    # converted to pixels).
    pill_screen_y_offset = -theme.branch_name_pill_offset_commit_axis_in_rows * theme.commit_spacing
    pill_room = pill_screen_y_offset + pill_height / 2 + _AUTO_FIT_EDGE_PAD_PX
    return max(theme.margin_bottom, pill_room)
