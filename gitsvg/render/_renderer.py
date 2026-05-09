"""Rendering orchestration — turn a `Layout` into an SVG drawing.

The renderer is purely "Layout dataclass tree → SVG primitives." It never
imports `State`. Every visual decision (resolved colours, label sides,
which arcs/guides to draw, canvas dimensions, …) was made in the layout
engine and is already encoded in the `Layout` it receives.

Z-order (back to front):

1. Branch guides (faint dashed verticals at every occupied lane).
2. Arcs (branch-off + merge), in the order produced by the layout
   engine.
3. Branch lines (vertical, in branch colour).
4. Branch-name pills (coloured rounded rectangles + branch name).
5. Commit dots (in branch colour, with white outline; enlarged when
   highlighted).
6. Commit labels (`msg` primary lines + optional `hash` secondary
   line, on the side indicated by `label_side`; bold msg when
   highlighted).
"""

import drawsvg as draw

from gitsvg.layout import Layout
from gitsvg.render._primitives._arc import draw_arc
from gitsvg.render._primitives._branch_guide import draw_branch_guide
from gitsvg.render._primitives._branch_line import draw_branch_line
from gitsvg.render._primitives._branch_pill import draw_branch_pill
from gitsvg.render._primitives._commit_dot import draw_commit_dot
from gitsvg.render._primitives._commit_label import draw_commit_label


def render(layout: Layout) -> draw.Drawing:
    """Render a `Layout` to an SVG drawing.

    Args:
        layout: A complete render-ready intermediate representation —
            produced by `gitsvg.layout.compute_layout(state)`.

    Returns:
        A `drawsvg.Drawing`. Callers persist with `.save_svg(path)` or
        convert with `.as_svg()`.
    """
    canvas = layout.canvas
    d = draw.Drawing(canvas.width, canvas.height)
    n_commits = canvas.n_commits

    # --- Branch guides ----------------
    for guide in layout.guides:
        draw_branch_guide(d, guide.branch_pos, canvas.height)

    # --- Arcs (branch-off + merge) -----
    for arc in layout.arcs:
        draw_arc(
            d,
            from_branch_pos=arc.from_branch_pos,
            from_commit_pos=arc.from_commit_pos,
            to_branch_pos=arc.to_branch_pos,
            to_commit_pos=arc.to_commit_pos,
            n_commits=n_commits,
            color=arc.color,
            vertical_first=arc.vertical_first,
        )

    # --- Branch lines -----------------
    for branch in layout.branches:
        draw_branch_line(d, branch, branch.color, n_commits)

    # --- Branch-name pills ------------
    for branch in layout.branches:
        draw_branch_pill(d, branch, n_commits)

    # --- Commit dots ------------------
    for commit in layout.commits.values():
        draw_commit_dot(d, commit, commit.color, n_commits)

    # --- Commit labels ----------------
    for commit in layout.commits.values():
        draw_commit_label(d, commit, n_commits)

    return d
