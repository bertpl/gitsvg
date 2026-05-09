"""Deterministic resolution of `hash: "auto"` on commits.

When a commit op (or merge op) sets `hash: "auto"`, the renderer needs
a stable 7-character hex string that mirrors real-git rebase semantics:

- Determinism — the same commit, with the same id and the same
  immediate parents, always produces the same string. This is what
  keeps animation frames visually stable across re-renders.
- Sensitivity to parent-chain changes — when a commit's parent set
  changes (e.g. a downstream commit after an upstream id rename), the
  auto-hash changes. Authors who keep ids stable across frames for
  unchanged commits get stable hashes for free; authors who give a
  rebased commit a new id (the recommended convention) get the
  cascade correctly.

The hash is the lower-cased hex of
`sha256(id + "\\n" + "\\n".join(sorted(immediate_parent_ids)))[:7]`.
Sorting the parent ids before hashing makes the hash insensitive to
declaration order on merge parents (a merge of `from=A into=B` and a
merge of `from=B into=A` would describe different operations, but the
resulting commit has the same parent *set*, hence the same auto-hash).

Resolution is eager — performed inside the op-apply hook the moment
the commit lands on state. The function below returns the immediate
parent ids by walking the state engine's bookkeeping; each apply hook
calls `compute_auto_hash` with that result and stores it back on the
commit.
"""

import hashlib

from gitsvg.state._state import State


def compute_auto_hash(commit_id: str, parent_ids: list[str]) -> str:
    """Return the 7-character deterministic auto-hash for a commit.

    Args:
        commit_id: The commit's id (explicit or auto-generated).
        parent_ids: The commit's immediate parent ids. Order is
            irrelevant — the function sorts before hashing.

    Returns:
        The lower-cased hex of the first 7 chars of sha256 over a
        canonical encoding of `(id, sorted parents)`.
    """
    canonical = commit_id + "\n" + "\n".join(sorted(parent_ids))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return digest[:7]


def effective_parent_ids(state: State, commit_id: str, branch_name: str) -> list[str]:
    """Return the immediate parent ids of a commit as seen by auto-hash.

    "Immediate parents" means the commit's effective parent set at the
    moment its hash is resolved — not transitive ancestors:

    - When the commit has explicit `parents:` (set by the author or
      auto-resolved by a `merge` op into both branch tips), those are
      the immediate parents.
    - Otherwise, the implicit chain parent is used: the commit
      preceding this one on its branch's commit list, or the branch's
      `rooted_on_commit` when this is the branch's first commit, or
      the empty list when no rooted_on_commit exists (the first commit
      on the very first branch).

    Args:
        state: The state engine after the commit has been added.
        commit_id: The id of the commit whose parents are being
            resolved.
        branch_name: The name of the branch the commit lives on.

    Returns:
        A possibly-empty list of parent commit ids.
    """
    commit = state.commits[commit_id]
    if commit.parents:
        return list(commit.parents)
    branch = state.branches[branch_name]
    idx = branch.commit_ids.index(commit_id)
    if idx == 0:
        return [branch.rooted_on_commit] if branch.rooted_on_commit else []
    return [branch.commit_ids[idx - 1]]
