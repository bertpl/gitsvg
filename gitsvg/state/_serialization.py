"""JSON serialization of resolved state.

`state_to_json` produces a dict matching `gitsvg state`'s public
output schema:

- `branches` — one entry per declared branch, in declaration order,
  with the branch name and the id of its head commit (or `null` for
  empty branches).
- `commits` — one entry per surviving commit, in addition order,
  with the resolved hash (the `"auto"` sentinel has been resolved by
  the state pipeline), the message, the highlight flag, the branch
  the commit lives on (by name), and its canonical parent list.
- `pull_requests` — one entry per open pull request, in declaration
  order.

Branch references throughout use **names**, matching the JSONL input
vocabulary. The opaque internal branch ids (`BranchState.id`,
`"b0"` / `"b1"` / …) are intentionally never exposed: they exist
only for cross-stage handoff between the state engine, the layout
engine, and the renderer.

Parents are read straight off `CommitState.parents`, which the state
engine resolved once when the commit was applied — chain parent first,
plus the merged-in tip for `merge` commits. The graph-level parent set
the agent reasons about is exactly that stored list; no re-derivation
happens here.
"""

from typing import Any

from ._state import State


def state_to_json(state: State) -> dict[str, Any]:
    """Convert a resolved `State` to a JSON-serializable dict.

    Args:
        state: The state produced by `apply_ops` (and validated end-to-end
            — the caller is responsible for skipping this when the
            validation report is dirty).

    Returns:
        A nested dict with `branches`, `commits`, and `pull_requests`
        top-level keys. The dict is `json.dumps`-able with no custom
        encoder.
    """
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
                "parents": list(commit.parents),
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
