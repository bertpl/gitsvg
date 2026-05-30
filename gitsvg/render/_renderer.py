"""Rendering orchestration — turn a `Layout` plus `Theme` into an SVG drawing.

The renderer is purely "Layout + Theme → SVG primitives." It never
imports `State`. Layout supplies integer-grid positions and semantic
identifiers; theme supplies every pixel, colour, font, stroke, and
dash decision. `compute_canvas(layout, theme)` resolves the pixel-space
canvas the coordinate transform reads from.

Z-order (back to front):

0. Canvas background (a filled rect when `theme.background_color` is
   not None; nothing otherwise — the SVG stays transparent).
1. Branch guides (faint dashed verticals at every occupied lane).
2. Arcs (branch-off + merge), in the order produced by the layout
   engine.
3. Pull-request arcs (dashed mirror of merge arcs), one per open PR.
4. Branch lines (vertical, in branch colour).
5. Branch-name pills (coloured rounded rectangles + branch name).
6. Pull-request title pills (anchored at source-tip commits; only
   when the PR has a `title`).
7. Commit dots (in branch colour, with white outline; enlarged when
   highlighted).
8. Commit labels (`msg` primary lines + optional `hash` secondary
   line, on the side indicated by `label_side`; bold msg when
   highlighted).
"""

import copy

import drawsvg as draw

from gitsvg.layout import GridSlot, Layout, LayoutBranch
from gitsvg.render._canvas import compute_canvas
from gitsvg.render._colors import resolve_branch_color
from gitsvg.render._primitives.arc import draw_arc
from gitsvg.render._primitives.branch_guide import draw_branch_guide
from gitsvg.render._primitives.branch_line import draw_branch_line
from gitsvg.render._primitives.branch_pill import draw_branch_pill
from gitsvg.render._primitives.commit_dot import draw_commit_dot
from gitsvg.render._primitives.commit_label import draw_commit_label
from gitsvg.render._primitives.pull_request_pill import draw_pull_request_pill
from gitsvg.render._renderer_settings import RendererSettings
from gitsvg.theme import DEFAULT_THEME


def _branch_through_point(layout: Layout, point: GridSlot) -> LayoutBranch:
    """Return the branch whose line passes through `point`.

    A connector takes its colour from the branch at its branch point —
    the new branch for a branch-off (the point is that branch's start),
    or the merged-in / source branch for a merge or pull request (the
    point is a row within that branch's life). Matched by lane plus a
    row inside the branch's `[start, end]` span.

    Args:
        layout: The resolved layout.
        point: The grid slot to resolve — a connector's branch point.

    Returns:
        The `LayoutBranch` whose colour the renderer should use.

    Raises:
        LookupError: If no branch matches — should never happen for a
            valid layout, so the error is a defensive guard.
    """
    for branch in layout.branches:
        if branch.branch_pos == point.branch_pos and branch.start <= point.commit_pos <= branch.end:
            return branch
    raise LookupError(f"no branch passes through {point!r}")


def _get_occupied_lanes(layout: Layout) -> list[int]:
    """Return the sorted, deduplicated lane indices occupied by any branch."""
    return sorted({branch.branch_pos for branch in layout.branches})


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

    # --- Branch id → declaration index map ------
    # Used by the colour resolver. Layout.branches is in declaration
    # order, matching state.branch_order.
    declaration_index_by_id: dict[str, int] = {b.id: i for i, b in enumerate(layout.branches)}

    def color_for(branch_id: str) -> str:
        """Resolve `branch_id` to its rendered colour using the closed-over index map and theme."""
        return resolve_branch_color(branch_id, declaration_index_by_id.get(branch_id, 0), theme)

    # --- Canvas background ----------------------
    if theme.background_color is not None:
        d.append(
            draw.Rectangle(
                0,
                0,
                canvas.width,
                canvas.height,
                fill=theme.background_color,
            )
        )

    # --- Branch guides --------------------------
    for lane in _get_occupied_lanes(layout):
        draw_branch_guide(d, lane, canvas, theme)

    # --- Arcs (branch-off + merge) --------------
    for arc in layout.arcs:
        arc_branch = _branch_through_point(layout, arc.branch_point)
        draw_arc(
            d,
            trunk_point=arc.trunk_point,
            branch_point=arc.branch_point,
            canvas=canvas,
            theme=theme,
            color=color_for(arc_branch.id),
        )

    # --- Pull-request arcs (dashed) -------------
    for pr in layout.pull_requests:
        draw_arc(
            d,
            trunk_point=pr.trunk_point,
            branch_point=pr.branch_point,
            canvas=canvas,
            theme=theme,
            color=color_for(_branch_through_point(layout, pr.branch_point).id),
            stroke_dasharray=theme.pull_request_dash,
        )

    # --- Branch lines ---------------------------
    for branch in layout.branches:
        draw_branch_line(d, branch, color_for(branch.id), canvas, theme)

    # --- Branch-name pills ----------------------
    for branch in layout.branches:
        draw_branch_pill(d, branch, color_for(branch.id), canvas, theme)

    # --- Pull-request title pills ---------------
    for pr in layout.pull_requests:
        draw_pull_request_pill(d, pr, color_for(_branch_through_point(layout, pr.branch_point).id), canvas, theme)

    # --- Commit dots ----------------------------
    for commit in layout.commits.values():
        draw_commit_dot(d, commit, color_for(commit.branch_id), canvas, theme)

    # --- Commit labels --------------------------
    for commit in layout.commits.values():
        draw_commit_label(d, commit, canvas, theme)

    return d
