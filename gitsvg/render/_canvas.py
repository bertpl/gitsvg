"""Compute the renderer's pixel-space canvas from the layout grid + theme.

The renderer needs concrete pixel dimensions for the SVG it emits:
canvas `width` / `height` and the effective spacings / margins the
coordinate transform multiplies into grid indices. `compute_canvas`
takes the grid extent (from `Layout.canvas`, i.e. `LayoutGrid`) plus
the resolved theme, and walks the same auto-fit rule the layout engine
used to: keep the canvas just big enough to contain the longest visible
labels, the branch-name pills, and any open pull-request's projected
merge-commit row.

This module lives in `render/` because it's purely pixel work. The
layout engine never reads it.
"""

from dataclasses import dataclass

from gitsvg.layout import Layout, LayoutBranch, LayoutCommit
from gitsvg.render._metrics import commit_label_width, pill_width
from gitsvg.render._theme import Theme


@dataclass(slots=True)
class RenderCanvas:
    """Computed pixel-space canvas the renderer's coordinate transform reads from.

    Effective values come from theme defaults; user pins on the
    `canvas:` op already flowed into `theme` via `build_theme`.

    Attributes:
        width: SVG canvas width in pixels.
        height: SVG canvas height in pixels.
        n_commits: Effective commit-axis slot count (pinned via `canvas.n_commits`
            or auto-fit from content). Needed by the coordinate transform
            because the bottom-to-top orientation places index 0 at the
            largest y.
        n_branches: Effective branch-axis slot count.
        branch_spacing: Effective pixel distance between adjacent branch-axis slots.
        commit_spacing: Effective pixel distance between adjacent commit-axis slots.
        margin_branch_axis_lower: Effective branch-axis margin at the lower end (lane 0 side).
        margin_branch_axis_upper: Effective branch-axis margin at the upper end (highest-lane side).
        margin_commit_axis_lower: Effective commit-axis margin at the lower end (oldest-commit side).
        margin_commit_axis_upper: Effective commit-axis margin at the upper end (newest-commit side).
    """

    width: float
    height: float
    n_commits: int
    n_branches: int
    branch_spacing: float
    commit_spacing: float
    margin_branch_axis_lower: float
    margin_branch_axis_upper: float
    margin_commit_axis_lower: float
    margin_commit_axis_upper: float


def compute_canvas(layout: Layout, theme: Theme) -> RenderCanvas:
    """Compute the effective `RenderCanvas` for `layout` under `theme`.

    Margins auto-fit to the longest visible labels and pills; spacing /
    margin overrides from a `canvas:` op live on the resolved theme
    (folded in by `build_theme`).
    """
    branches = layout.branches
    commit_layouts = layout.commits
    pull_requests = layout.pull_requests
    grid = layout.canvas

    branch_spacing = theme.branch_spacing
    commit_spacing = theme.commit_spacing

    n_commits = grid.n_commits
    n_branches = grid.n_branches
    max_branch_pos = max((b.branch_pos for b in branches), default=0)

    margin_branch_axis_lower = _auto_fit_margin_branch_axis(
        branches, commit_layouts, theme, branch_pos_filter=0, side="left"
    )
    margin_branch_axis_upper = _auto_fit_margin_branch_axis(
        branches, commit_layouts, theme, branch_pos_filter=max_branch_pos, side="right"
    )
    margin_commit_axis_lower = _auto_fit_margin_commit_axis_lower(branches, theme)
    # `margin_commit_axis_upper` is the one margin always promoted to
    # float — the coordinate transform's `y = margin_commit_axis_upper +
    # ...` propagates this into every y attribute. v0.1.3 did the same.
    margin_commit_axis_upper = float(theme.margin_commit_axis_upper)

    width = margin_branch_axis_lower + (n_branches - 1) * branch_spacing + margin_branch_axis_upper
    height = margin_commit_axis_upper + (n_commits - 1) * commit_spacing + margin_commit_axis_lower
    return RenderCanvas(
        width=width,
        height=height,
        n_commits=n_commits,
        n_branches=n_branches,
        branch_spacing=branch_spacing,
        commit_spacing=commit_spacing,
        margin_branch_axis_lower=margin_branch_axis_lower,
        margin_branch_axis_upper=margin_branch_axis_upper,
        margin_commit_axis_lower=margin_commit_axis_lower,
        margin_commit_axis_upper=margin_commit_axis_upper,
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
    """
    if side == "left":
        default = theme.margin_branch_axis_lower
        outward_label_side = "left"
    else:
        default = theme.margin_branch_axis_upper
        outward_label_side = "right"

    needed: float = 0.0
    pad = 4.0
    for branch in branches:
        if branch.branch_pos == branch_pos_filter:
            needed = max(needed, pill_width(branch.name, theme) / 2 + pad)
    for commit in commit_layouts.values():
        if commit.branch_pos == branch_pos_filter and commit.label_side == outward_label_side:
            needed = max(needed, theme.label_offset + commit_label_width(commit, theme) + pad)
    return max(default, needed)


def _auto_fit_margin_commit_axis_lower(branches: list[LayoutBranch], theme: Theme) -> float:
    """Compute the auto-fit lower margin on the commit axis.

    The pill of any branch with `start = min(start)` sits closest to the
    canvas bottom. Reserve enough room for it: `branch_name_pill_offset`
    (centre offset) + half the pill height + a small pad.
    """
    if not branches:
        return theme.margin_commit_axis_lower
    pill_height = theme.branch_label_font_size + 8  # matches `_branch_pill._PILL_PADDING_Y`
    pill_room = theme.branch_name_pill_offset + pill_height / 2 + 4.0
    return max(theme.margin_commit_axis_lower, pill_room)
