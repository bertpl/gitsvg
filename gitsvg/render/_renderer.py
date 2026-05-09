"""Main rendering orchestration — turn state + layout into an SVG drawing.

PR4 scope (no labels, no arcs, no guides):

- Canvas dimensions auto-fit from layout extent.
- Branch lines (vertical, in branch colour).
- Commit dots (in branch colour, with white outline).

Subsequent PRs add: branch-off and merge arcs (PR5), branch guides
(PR5), commit labels and branch-name pills and the highlight visual
(PR6), and `canvas:` op overrides plus auto-fit margins (PR7).
"""

import drawsvg as draw

from gitsvg.layout import Layout
from gitsvg.render._canvas import compute_canvas_size
from gitsvg.render._colors import resolve_branch_color
from gitsvg.render._primitives._branch_line import draw_branch_line
from gitsvg.render._primitives._commit_dot import draw_commit_dot
from gitsvg.state import State


def render(state: State, layout: Layout) -> draw.Drawing:
    """Render a validated state + layout to an SVG drawing.

    Args:
        state: The state engine's output, holding entity data
            (colors, parent chains, declaration order, …).
        layout: The layout engine's output, holding axis positions.

    Returns:
        A `drawsvg.Drawing`. Callers can `.save_svg(path)` to write to
        disk or `.as_svg()` to obtain the SVG text.
    """
    width, height, n_commits = compute_canvas_size(layout)
    d = draw.Drawing(width, height)

    # --- Branch lines -----------------
    for branch_name in state.branch_order:
        branch_layout = layout.branches.get(branch_name)
        if branch_layout is None:
            continue
        color = resolve_branch_color(state, branch_name)
        draw_branch_line(d, branch_layout, color, n_commits)

    # --- Commit dots ------------------
    for commit_id, commit_state in state.commits.items():
        commit_layout = layout.commits.get(commit_id)
        if commit_layout is None:
            continue
        color = resolve_branch_color(state, commit_state.branch)
        draw_commit_dot(d, commit_layout, color, n_commits)

    return d
