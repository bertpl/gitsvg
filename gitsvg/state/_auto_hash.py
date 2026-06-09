r"""Deterministic resolution of `hash: "auto"` on commits.

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
the commit lands on state. Each apply hook resolves the commit's
canonical parent list (the chain parent for a `commit` op, the
chain parent plus the merged-in tip for a `merge` op) and calls
`compute_auto_hash` with it, storing the result back on the commit.
"""

import hashlib


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
