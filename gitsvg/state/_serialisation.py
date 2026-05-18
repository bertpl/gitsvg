"""JSON serialisation of resolved state.

`state_to_json` produces a dict matching `gitsvg state`'s public
output schema:

- `branches` — one entry per declared branch, in declaration order,
  with the branch name and the id of its head commit (or `null` for
  empty branches).
- `commits` — one entry per surviving commit, in addition order,
  with the resolved hash (the `"auto"` sentinel has been resolved by
  the state pipeline), the message, the highlight flag, the branch
  the commit lives on (by name), and its effective parents.
- `pull_requests` — one entry per open pull request, in declaration
  order.

Branch references throughout use **names**, matching the JSONL input
vocabulary. The opaque internal branch ids (`BranchState.id`,
`"b0"` / `"b1"` / …) are intentionally never exposed: they exist
only for cross-stage handoff between the state engine, the layout
engine, and the renderer.

Effective parents are the union of the commit's chain parent (the
previous commit on the same branch, or the branch's source commit
for the first commit) and the commit's explicit `parents` list, with
duplicates removed and the chain parent placed first. The result is
the graph-level parent set the agent reasons about; raw
`CommitState.parents` (declared parents only) would push that
inference onto the consumer.
"""

from typing import Any

from gitsvg.state._state import CommitState, State


def state_to_json(state: State) -> dict[str, Any]:
    """Convert a resolved `State` to a JSON-serialisable dict.

    Args:
        state: The state produced by `apply_ops` (and validated end-to-end
            — the caller is responsible for skipping this when the
            validation report is dirty).

    Returns:
        A nested dict with `branches`, `commits`, and `pull_requests`
        top-level keys. The dict is `json.dumps`-able with no custom
        encoder.
    """
    chain_parents = _compute_chain_parents(state)
    return {
        "branches": [
            {
                "name": state.branches[name].name,
                "head_commit_id": _head_commit_id(state, name),
            }
            for name in state.branch_order
        ],
        "commits": [
            {
                "id": commit.id,
                "branch": commit.branch,
                "hash": commit.hash,
                "msg": commit.msg,
                "highlight": commit.highlight,
                "parents": _effective_parents(commit, chain_parents),
            }
            for commit in state.commits.values()
        ],
        "pull_requests": [
            {
                "id": pr.id,
                "from_branch": pr.from_branch,
                "into_branch": pr.into_branch,
                "title": pr.title,
            }
            for pr in state.pull_requests.values()
        ],
    }


def _head_commit_id(state: State, branch_name: str) -> str | None:
    """Return the id of the latest commit on `branch_name`, or None when empty."""
    commit_ids = state.branches[branch_name].commit_ids
    return commit_ids[-1] if commit_ids else None


def _compute_chain_parents(state: State) -> dict[str, str | None]:
    """Build a `{commit_id: chain-parent-id-or-None}` map.

    The chain parent of a commit is the previous commit on the same
    branch, or the branch's `rooted_on_commit` for the first commit
    on a non-root branch. The first commit on the first (root)
    branch has no chain parent.

    Args:
        state: Resolved state.

    Returns:
        A dict keyed by commit id; the value is the chain parent's
        commit id, or `None` for root commits.
    """
    chain_parent: dict[str, str | None] = {}
    for branch in state.branches.values():
        previous: str | None = branch.rooted_on_commit
        for cid in branch.commit_ids:
            chain_parent[cid] = previous
            previous = cid
    return chain_parent


def _effective_parents(
    commit: CommitState,
    chain_parents: dict[str, str | None],
) -> list[str]:
    """Merge the chain parent with the commit's declared parents.

    Args:
        commit: The commit whose effective parents to compute.
        chain_parents: The map from `_compute_chain_parents`.

    Returns:
        Parent commit ids, chain parent first, declared parents in
        their original order, duplicates removed. Empty when the
        commit is the first on the root branch with no declared
        parents.
    """
    parents: list[str] = []
    chain = chain_parents.get(commit.id)
    if chain is not None:
        parents.append(chain)
    for declared in commit.parents:
        if declared not in parents:
            parents.append(declared)
    return parents
