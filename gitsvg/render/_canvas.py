"""Canvas dimension computation — auto-fit from layout extent.

PR4 ships only auto-fit (canvas size derived from the layout's furthest
positions). Honouring `canvas` op overrides (`n_commits`, `n_branches`,
spacing, margins) lands in PR7.
"""

from gitsvg.layout import Layout
from gitsvg.render._constants import (
    BRANCH_SPACING,
    COMMIT_SPACING,
    MARGIN_BRANCH_AXIS_LOWER,
    MARGIN_BRANCH_AXIS_UPPER,
    MARGIN_COMMIT_AXIS_LOWER,
    MARGIN_COMMIT_AXIS_UPPER,
)


def compute_canvas_size(layout: Layout) -> tuple[float, float, int]:
    """Compute auto-fit canvas dimensions from the layout extent.

    Args:
        layout: The fully-built layout for the diagram.

    Returns:
        `(width, height, n_commits)` triple. `n_commits` is the
        commit-axis slot count used by the renderer's coordinate
        transform — returned alongside the dimensions to avoid a second
        max-walk by callers.
    """
    max_branch_pos = max((b.branch_pos for b in layout.branches.values()), default=0)
    max_commit_pos_from_commits = max((c.commit_pos for c in layout.commits.values()), default=-1)
    max_commit_pos_from_branches = max((b.end for b in layout.branches.values()), default=-1)
    max_commit_pos = max(max_commit_pos_from_commits, max_commit_pos_from_branches)
    n_commits = max_commit_pos + 1 if max_commit_pos >= 0 else 1

    width = MARGIN_BRANCH_AXIS_LOWER + max_branch_pos * BRANCH_SPACING + MARGIN_BRANCH_AXIS_UPPER
    height = MARGIN_COMMIT_AXIS_UPPER + (n_commits - 1) * COMMIT_SPACING + MARGIN_COMMIT_AXIS_LOWER
    return width, height, n_commits
