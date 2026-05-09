"""Layout output dataclasses — pure axis positions for branches and commits.

These are produced by `gitsvg.layout.compute_layout` and consumed by
the renderer. They live alongside (not on) `State`, so the renderer
can read positions without touching state-engine internals — and so
the layout engine can be replaced with a smarter one later without
churning the state engine.

Both axis positions are non-negative integers. The mapping from
position to pixel coordinates lives in the renderer.
"""

from dataclasses import dataclass, field


@dataclass(slots=True)
class LayoutCommit:
    """Computed axis position of one commit.

    Attributes:
        id: The commit's id (matching `CommitState.id` in state).
        branch_pos: Slot index along the branch axis (the lane the
            commit sits on).
        commit_pos: Slot index along the commit axis (where on the
            commit timeline the commit sits, with 0 = oldest).
    """

    id: str
    branch_pos: int
    commit_pos: int


@dataclass(slots=True)
class LayoutBranch:
    """Computed axis positions of one branch.

    Attributes:
        name: The branch's name (matching `BranchState.name` in state).
        branch_pos: Slot index along the branch axis.
        start: Commit-axis position where the branch begins (the
            branch-off point — for non-root branches this is one slot
            above the parent commit's `commit_pos`).
        end: Commit-axis position of the latest commit on this branch,
            or `start` when the branch has no commits yet.
    """

    name: str
    branch_pos: int
    start: int
    end: int


@dataclass(slots=True)
class Layout:
    """Per-diagram layout: positions for every branch and commit.

    Attributes:
        branches: Branches by name.
        commits: Commits by id.
    """

    branches: dict[str, LayoutBranch] = field(default_factory=dict)
    commits: dict[str, LayoutCommit] = field(default_factory=dict)
