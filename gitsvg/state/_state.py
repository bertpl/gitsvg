"""In-memory state built up by applying ops in order.

State holds the structural model — commits, branches, pull-requests,
branch declaration order, and the optional pinned grid extent — plus
the one per-entity layout hint that is still structural (the branch
lane override). Presentational data — colours, label sides, and
every other render-side decision — lives in a separate `Theme`,
produced alongside `State` by the apply stage. Each op mutates
state when it applies cleanly; the state engine is the producer,
downstream layers (layout, rendering) are consumers.
"""

from dataclasses import dataclass, field


@dataclass(slots=True)
class GridState:
    """Pinned grid extent captured from a `grid` op.

    Both fields are independently optional — pinning only one is
    meaningful (e.g. fix the lane count while letting the commit-axis
    auto-fit).
    """

    n_commits: int | None = None
    n_branches: int | None = None


@dataclass(slots=True)
class BranchState:
    """One branch as it currently exists in state.

    Attributes:
        id: Stable, opaque, internally-generated identifier for this
            branch. Unique across the lifetime of the state object
            (never reused), so it cleanly distinguishes a removed
            branch from a later branch declared with the same name.
            Format is `f"b{n}"` where `n` is a monotonic counter on
            `State`. Internal-only: does not appear in JSONL input,
            schema output, or user-facing error messages.
        name: Branch name as written in the JSONL. Unique among
            currently-live branches, but can be reused after `remove`
            — `id` is the stable handle.
        branch_pos: Optional explicit lane-index override from the
            declaration. Stored verbatim; the layout engine consumes it
            and bypasses the lane-reuse heuristic when set.
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

    id: str
    name: str
    branch_pos: int | None = None
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
        hash: Optional hash string (literal `"auto"` allowed; auto-resolution is deterministic).
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


@dataclass(slots=True)
class PullRequestState:
    """One open pull-request as it currently exists in state.

    Attributes:
        id: Unique pull-request id (explicit or auto-generated).
        from_branch: Name of the source branch the PR proposes to merge.
        into_branch: Name of the target branch the PR proposes merging into.
        title: Optional short headline label for the PR.
        declaration_file: Source file the `pull_request` op was parsed from.
        declaration_line: 1-based source line of the `pull_request` op for
            error attribution.
    """

    id: str
    from_branch: str
    into_branch: str
    title: str | None = None
    declaration_file: str = ""
    declaration_line: int = 0


class State:
    """Mutable container for diagram state during op application.

    Each op handler mutates this in-place. Lookup helpers cover the
    common cases (`has_branch`, `has_commit`, `has_pull_request`,
    `branch_tip`, `is_first_branch`); deeper queries inspect the public
    dicts directly.
    """

    def __init__(self) -> None:
        """Initialise an empty state — no branches, no commits, no pull-requests, no grid pin."""
        self.branches: dict[str, BranchState] = {}
        self.commits: dict[str, CommitState] = {}
        self.pull_requests: dict[str, PullRequestState] = {}
        self.branch_order: list[str] = []
        self.grid: GridState | None = None
        self._next_branch_seq: int = 0

    def next_branch_id(self) -> str:
        """Return a fresh opaque branch id (`b0`, `b1`, …).

        The counter is monotonic across the state's lifetime — removed
        branches never give their id back. Callers (the `branch` op
        apply step) take the returned id and assign it to the new
        `BranchState`.
        """
        new_id = f"b{self._next_branch_seq}"
        self._next_branch_seq += 1
        return new_id

    def is_first_branch(self) -> bool:
        """Return True when no branch has been declared yet."""
        return not self.branches

    def has_branch(self, name: str) -> bool:
        """Return True when `name` is a declared branch."""
        return name in self.branches

    def has_commit(self, commit_id: str) -> bool:
        """Return True when `commit_id` exists in current state."""
        return commit_id in self.commits

    def has_pull_request(self, pr_id: str) -> bool:
        """Return True when `pr_id` is the id of an open pull-request."""
        return pr_id in self.pull_requests

    def branch_tip(self, name: str) -> str | None:
        """Return the id of the latest commit on `name`, or None when empty.

        Raises no error for unknown branches — callers that need a
        bound check use `has_branch` first.
        """
        branch = self.branches.get(name)
        return branch.commit_ids[-1] if branch and branch.commit_ids else None
