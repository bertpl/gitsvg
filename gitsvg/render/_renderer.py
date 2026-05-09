"""Main rendering orchestration — turn state + layout into an SVG drawing.

Z-order (back to front):

1. Branch guides (faint dashed verticals at every occupied lane).
2. Branch-off arcs (curved connectors from a parent commit on one
   lane to the start of a child branch on another lane).
3. Merge arcs (curved connectors from the merging-from branch's tip
   to the merge commit on the merging-into branch's lane).
4. Branch lines (vertical, in branch colour).
5. Commit dots (in branch colour, with white outline).

Subsequent PRs add: commit labels and branch-name pills and the
highlight visual (PR6); `canvas:` op overrides plus auto-fit margins
(PR7).
"""

import drawsvg as draw

from gitsvg.layout import Layout, LayoutBranch, LayoutCommit
from gitsvg.render._canvas import compute_canvas_size
from gitsvg.render._colors import resolve_branch_color
from gitsvg.render._primitives._arc import draw_arc
from gitsvg.render._primitives._branch_guide import draw_branch_guide
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

    _draw_branch_guides(d, layout, height)
    _draw_branch_off_arcs(d, state, layout, n_commits)
    _draw_merge_arcs(d, state, layout, n_commits)
    _draw_branch_lines(d, state, layout, n_commits)
    _draw_commit_dots(d, state, layout, n_commits)

    return d


# ==================================================================================================
#  Per-element draw passes
# ==================================================================================================
def _draw_branch_guides(d: draw.Drawing, layout: Layout, canvas_height: float) -> None:
    """Draw one dashed vertical guide per occupied branch-axis lane."""
    occupied = sorted({b.branch_pos for b in layout.branches.values()})
    for branch_pos in occupied:
        draw_branch_guide(d, branch_pos, canvas_height)


def _draw_branch_off_arcs(d: draw.Drawing, state: State, layout: Layout, n_commits: int) -> None:
    """Draw a branch-off arc for every non-root branch with a resolved parent commit."""
    for branch_name in state.branch_order:
        branch_state = state.branches.get(branch_name)
        branch_layout = layout.branches.get(branch_name)
        if branch_state is None or branch_layout is None:
            continue
        parent_id = branch_state.rooted_on_commit
        if parent_id is None:
            continue
        parent_layout = layout.commits.get(parent_id)
        if parent_layout is None:
            continue
        color = resolve_branch_color(state, branch_name)
        draw_arc(
            d,
            from_branch_pos=parent_layout.branch_pos,
            from_commit_pos=parent_layout.commit_pos,
            to_branch_pos=branch_layout.branch_pos,
            to_commit_pos=branch_layout.start,
            n_commits=n_commits,
            color=color,
            vertical_first=False,
        )


def _draw_merge_arcs(d: draw.Drawing, state: State, layout: Layout, n_commits: int) -> None:
    """Draw a merge arc for every commit with a parent on a different lane.

    A "merge arc" connects the source-branch tip's position to the merge
    commit's position with a vertical-first quarter arc. The source
    parent is identified as the one whose branch-axis position differs
    from the merge commit's own — which covers both `merge:`-op products
    (where parents = [into.tip, from.tip]) and any future multi-parent
    `commit:` op that crosses lanes.
    """
    for commit_id, commit_state in state.commits.items():
        commit_layout = layout.commits.get(commit_id)
        if commit_layout is None or len(commit_state.parents) < 2:
            continue
        for parent_id in commit_state.parents:
            parent_layout = layout.commits.get(parent_id)
            if parent_layout is None or parent_layout.branch_pos == commit_layout.branch_pos:
                continue
            parent_state = state.commits.get(parent_id)
            from_branch_name = parent_state.branch if parent_state is not None else commit_state.branch
            color = resolve_branch_color(state, from_branch_name)
            draw_arc(
                d,
                from_branch_pos=parent_layout.branch_pos,
                from_commit_pos=parent_layout.commit_pos,
                to_branch_pos=commit_layout.branch_pos,
                to_commit_pos=commit_layout.commit_pos,
                n_commits=n_commits,
                color=color,
                vertical_first=True,
            )


def _draw_branch_lines(d: draw.Drawing, state: State, layout: Layout, n_commits: int) -> None:
    """Draw one branch line per declared branch."""
    for branch_name in state.branch_order:
        branch_layout: LayoutBranch | None = layout.branches.get(branch_name)
        if branch_layout is None:
            continue
        color = resolve_branch_color(state, branch_name)
        draw_branch_line(d, branch_layout, color, n_commits)


def _draw_commit_dots(d: draw.Drawing, state: State, layout: Layout, n_commits: int) -> None:
    """Draw one commit dot per commit, in its branch's colour."""
    for commit_id, commit_state in state.commits.items():
        commit_layout: LayoutCommit | None = layout.commits.get(commit_id)
        if commit_layout is None:
            continue
        color = resolve_branch_color(state, commit_state.branch)
        draw_commit_dot(d, commit_layout, color, n_commits)
