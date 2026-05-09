"""In-memory state built up by applying ops in order.

State holds three namespaces — commits, branches, and (reserved) tags —
along with branch declaration order and an optional pinned canvas. Each
op mutates state when it applies cleanly; the state engine is the
producer, downstream layers (layout, rendering) are consumers.
"""

from dataclasses import dataclass, field


@dataclass(slots=True)
class CanvasState:
    """Pinned canvas dimensions captured from a `canvas` op.

    All fields are independently optional — setting one and leaving
    the others at None is meaningful (e.g. pin slot count, leave
    spacing auto). Margin fields default to renderer auto-fit when
    unset; set them explicitly only when stable per-frame margins
    matter (animation series).
    """

    n_commits: int | None = None
    n_branches: int | None = None
    commit_spacing: float | None = None
    branch_spacing: float | None = None
    margin_commit_axis_lower: float | None = None
    margin_commit_axis_upper: float | None = None
    margin_branch_axis_lower: float | None = None
    margin_branch_axis_upper: float | None = None


@dataclass(slots=True)
class BranchState:
    """One branch as it currently exists in state.

    Attributes:
        name: Unique branch name.
        color: Optional hex color override from the declaration.
        label_side: Optional label-side hint from the declaration.
        from_branch: Source-branch name captured at declaration time
            (or None for the first branch).
        from_commit: Source-commit id captured at declaration time
            (or None when `from_branch` is used or this is the first branch).
        rooted_on_commit: Resolved commit the branch is rooted on at
            declaration time. None when the source branch was empty
            or this is the first branch.
        declaration_file: Source file the `branch` op was parsed from.
        declaration_line: 1-based source line of the `branch` op for error attribution.
        commit_ids: Ordered list of commit ids appended to this branch.
    """

    name: str
    color: str | None = None
    label_side: str | None = None
    from_branch: str | None = None
    from_commit: str | None = None
    rooted_on_commit: str | None = None
    declaration_file: str = ""
    declaration_line: int = 0
    commit_ids: list[str] = field(default_factory=list)


@dataclass(slots=True)
class CommitState:
    """One commit as it currently exists in state.

    Attributes:
        id: Unique commit id (explicit or auto-generated).
        branch: Name of the branch the commit lives on.
        msg: Optional commit message.
        hash: Optional hash string (literal `"auto"` allowed; deterministic resolution lands in v0.0.3).
        parents: Explicit parents (empty list = the commit is a normal append).
        replaces: Commit ids this commit conceptually squashes (empty list = no squash).
        highlight: True when the commit is marked for visual highlight.
        gap: Number of empty commit-axis slots to leave between the branch's
            tip and this commit's landing position. Always 0 when the op did
            not set `gap`.
        declaration_file: Source file the op that introduced the commit was parsed from.
        declaration_line: 1-based source line of the op that introduced the commit.
    """

    id: str
    branch: str
    msg: str | None = None
    hash: str | None = None
    parents: list[str] = field(default_factory=list)
    replaces: list[str] = field(default_factory=list)
    highlight: bool = False
    gap: int = 0
    declaration_file: str = ""
    declaration_line: int = 0


class State:
    """Mutable container for diagram state during op application.

    Each op handler mutates this in-place. Lookup helpers cover the
    common cases (`has_branch`, `has_commit`, `branch_tip`,
    `is_first_branch`); deeper queries inspect the public dicts
    directly.
    """

    def __init__(self) -> None:
        """Initialise an empty state — no branches, no commits, no canvas."""
        self.branches: dict[str, BranchState] = {}
        self.commits: dict[str, CommitState] = {}
        self.branch_order: list[str] = []
        self.canvas: CanvasState | None = None

    def is_first_branch(self) -> bool:
        """Return True when no branch has been declared yet."""
        return not self.branches

    def has_branch(self, name: str) -> bool:
        """Return True when `name` is a declared branch."""
        return name in self.branches

    def has_commit(self, commit_id: str) -> bool:
        """Return True when `commit_id` exists in current state."""
        return commit_id in self.commits

    def branch_tip(self, name: str) -> str | None:
        """Return the id of the latest commit on `name`, or None when empty.

        Raises no error for unknown branches — callers that need a
        bound check use `has_branch` first.
        """
        branch = self.branches.get(name)
        return branch.commit_ids[-1] if branch and branch.commit_ids else None
