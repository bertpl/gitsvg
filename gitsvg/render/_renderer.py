"""Rendering orchestration — turn a `Layout` plus `Theme` into an SVG drawing.

The renderer is purely "Layout + Theme → SVG primitives." It never
imports `State`. Layout supplies integer-grid positions and semantic
identifiers; theme supplies every pixel, color, font, stroke, and
dash decision. `compute_canvas(layout, theme)` resolves the pixel-space
canvas the coordinate transform reads from.

Z-order (back to front):

0. Canvas background (a filled rect when `theme.background_color` is a
   visible, non-transparent color; nothing otherwise — the SVG stays
   transparent).
1. Commit-row bands (zebra stripes on alternate commit-axis rows when
   `theme.commit_row_band_color` is visible; nothing otherwise). Span
   the full canvas, just above the background and below the guides.
2. Branch guides (faint dashed verticals at every occupied lane).
3. Per-branch line band — looping branches in declaration order, each
   branch's connectors and line are drawn as one color-coherent group
   before the next branch's: its branch-off / merge arcs, then its
   branch line, then its pull-request arcs (dashed). Every element in
   the band is colored by exactly one branch (the arc color resolver
   attributes each connector to its branch point), so grouping keeps a
   branch's colored strokes contiguous along the z-axis. Crossings
   between branches resolve by declaration order — a later-declared
   branch paints over an earlier one.
4. Commit dots (ordinary commits in branch color with white outline;
   merge commits per `merge_commit_style`; enlarged when highlighted).
   Above the line band, below every text element.
5. Branch-name pills (colored rounded rectangles + branch name).
   Skipped in `table` mode — the branch name moves to a tip pill in the
   table's message column.
6. Pull-request title pills (anchored half a row back from the
   projected merge row on the source branch line; only when the PR has
   a `title`).
7. Commit labels (`msg` primary lines + optional `hash` secondary
   line, on the side indicated by `label_side`; bold msg when
   highlighted). In `table` mode this layer is replaced by the table
   region — message + hash columns beside the graph, with each branch's
   name as a tip pill in its ref-target commit's message cell.
"""

import copy
from collections import defaultdict

import drawsvg as draw

from gitsvg._shared.color import is_color_visible
from gitsvg.layout import GridSlot, Layout, LayoutArc, LayoutBranch, LayoutPullRequest
from gitsvg.render._canvas import compute_canvas, is_table_active
from gitsvg.render._colors import resolve_branch_color
from gitsvg.render._primitives.arc import draw_arc
from gitsvg.render._primitives.branch_guide import draw_branch_guide
from gitsvg.render._primitives.branch_line import draw_branch_line
from gitsvg.render._primitives.branch_pill import draw_branch_pill
from gitsvg.render._primitives.commit_dot import draw_commit_dot
from gitsvg.render._primitives.commit_label import draw_commit_label
from gitsvg.render._primitives.commit_row_band import draw_commit_row_band
from gitsvg.render._primitives.commit_table import draw_commit_table
from gitsvg.render._primitives.pull_request_pill import draw_pull_request_pill
from gitsvg.render._renderer_settings import RendererSettings
from gitsvg.render._table import compute_table_columns
from gitsvg.theme import DEFAULT_THEME


def _branch_through_point(layout: Layout, point: GridSlot) -> LayoutBranch:
    """Return the branch whose line passes through `point`.

    A connector takes its color from the branch at its branch point —
    the new branch for a branch-off (the point is that branch's start),
    or the merged-in / source branch for a merge or pull request (the
    point is a row within that branch's life). Matched against each
    branch's lane segments: some segment must sit on the point's lane and
    cover its row.

    Args:
        layout: The resolved layout.
        point: The grid slot to resolve — a connector's branch point.

    Returns:
        The `LayoutBranch` whose color the renderer should use.

    Raises:
        LookupError: If no branch matches — should never happen for a
            valid layout, so the error is a defensive guard.
    """
    for branch in layout.branches:
        for segment in branch.segments:
            if segment.lane == point.branch_pos and segment.start <= point.commit_pos <= segment.end:
                return branch
    raise LookupError(f"no branch passes through {point!r}")


def _get_occupied_lanes(layout: Layout) -> list[int]:
    """Return the sorted, deduplicated lane indices occupied by any branch segment."""
    return sorted({segment.lane for branch in layout.branches for segment in branch.segments})


def render(layout: Layout, theme: RendererSettings | None = None) -> draw.Drawing:
    """Render a `Layout` to an SVG drawing.

    Args:
        layout: A complete render-ready intermediate representation —
            produced by `gitsvg.layout.compute_layout(state)`.
        theme: The renderer's slice of the resolved theme. Production
            callers split the apply pass's `Theme` output via
            `theme.split()` and pass the second element. Defaults to
            the renderer slice of `DEFAULT_THEME` when omitted (useful
            for tests).

    Returns:
        A `drawsvg.Drawing`. Callers persist with `.save_svg(path)` or
        convert with `.as_svg()`.
    """
    if theme is None:
        _, theme = DEFAULT_THEME.split()
    theme = copy.deepcopy(theme)
    canvas = compute_canvas(layout, theme)
    d = draw.Drawing(canvas.width, canvas.height)

    # Table layout (when active) is computed once for the table draw.
    table_active = is_table_active(theme)
    table_columns = (
        compute_table_columns(theme.table_msg_width, theme.table_hash_width, gutter=0) if table_active else None
    )

    # --- Branch id → declaration index map ------
    # Used by the color resolver. Layout.branches is in declaration
    # order, matching state.branch_order.
    declaration_index_by_id: dict[str, int] = {b.id: i for i, b in enumerate(layout.branches)}

    def color_for(branch_id: str) -> str:
        """Resolve `branch_id` to its rendered color using the closed-over index map and theme."""
        return resolve_branch_color(branch_id, declaration_index_by_id.get(branch_id, 0), theme)

    # --- Canvas background ----------------------
    if is_color_visible(theme.background_color):
        d.append(
            draw.Rectangle(
                0,
                0,
                canvas.width,
                canvas.height,
                fill=theme.background_color,
            )
        )

    # --- Commit-row bands -----------------------
    # Zebra stripes on alternate commit-axis rows (odd index → row 0 bare),
    # spanning the full canvas just above the background. Skipped entirely
    # when the band color is unset / fully transparent, so default output
    # stays byte-identical.
    band_color = theme.commit_row_band_color
    if is_color_visible(band_color):
        for commit_pos in range(1, canvas.n_commits, 2):
            draw_commit_row_band(d, commit_pos, band_color, canvas)

    # --- Branch guides --------------------------
    for lane in _get_occupied_lanes(layout):
        draw_branch_guide(d, lane, canvas, theme)

    # --- Per-branch line band -------------------
    # Bucket every connector under the branch whose color it carries
    # (its branch point), so each branch's arcs + line + PR arcs draw as
    # one contiguous color-coherent group, in declaration order.
    arcs_by_branch: dict[str, list[LayoutArc]] = defaultdict(list)
    for arc in layout.arcs:
        arcs_by_branch[_branch_through_point(layout, arc.branch_point).id].append(arc)

    prs_by_branch: dict[str, list[LayoutPullRequest]] = defaultdict(list)
    for pr in layout.pull_requests:
        prs_by_branch[_branch_through_point(layout, pr.branch_point).id].append(pr)

    for branch in layout.branches:
        color = color_for(branch.id)
        for arc in arcs_by_branch[branch.id]:
            draw_arc(
                d,
                trunk_point=arc.trunk_point,
                branch_point=arc.branch_point,
                canvas=canvas,
                theme=theme,
                color=color,
                kind=arc.kind,
            )
        draw_branch_line(d, branch, color, canvas, theme)
        for pr in prs_by_branch[branch.id]:
            draw_arc(
                d,
                trunk_point=pr.trunk_point,
                branch_point=pr.branch_point,
                canvas=canvas,
                theme=theme,
                color=color,
                stroke_dasharray=theme.pull_request_dash,
            )

    # --- Commit dots ----------------------------
    for commit in layout.commits.values():
        draw_commit_dot(d, commit, color_for(commit.branch_id), canvas, theme)

    # --- Branch-name pills ----------------------
    # In table mode the branch name moves to a tip pill in the table's
    # message column, so the branch-start pill is skipped.
    if not table_active:
        for branch in layout.branches:
            draw_branch_pill(d, branch, color_for(branch.id), canvas, theme)

    # --- Pull-request title pills ---------------
    for pr in layout.pull_requests:
        draw_pull_request_pill(d, pr, color_for(_branch_through_point(layout, pr.branch_point).id), canvas, theme)

    # --- Commit labels / table ------------------
    # Inline mode draws free-floating labels beside each dot; table mode
    # replaces them with the right-half table (message + hash columns + tip
    # pills).
    if table_active and table_columns is not None:
        draw_commit_table(d, layout, table_columns, canvas.table_x_origin, canvas, theme, color_for)
    else:
        for commit in layout.commits.values():
            draw_commit_label(d, commit, canvas, theme)

    return d
