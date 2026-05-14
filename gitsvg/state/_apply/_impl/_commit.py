"""Apply a `commit` op to state — branch existence, parents, replaces, id uniqueness."""

from typing import cast

from gitsvg.errors import ValidationError, ValidationReport
from gitsvg.file_format.ops import CommitOp
from gitsvg.parse import ParsedOp
from gitsvg.state._apply._checks import check_replaces_rules
from gitsvg.state._auto_hash import compute_auto_hash, effective_parent_ids
from gitsvg.state._state import CommitState, State
from gitsvg.theme import Theme


def apply_commit_op(state: State, theme: Theme, parsed: ParsedOp, report: ValidationReport) -> None:
    """Apply a `commit` op.

    Validation order (no state mutation until everything passes):

    1. The branch reference must exist (E200).
    2. If `replaces:` is set, the 7-rule check must pass.
    3. Each parent in `parents:` must exist in current state (E201).
       Rule 7 already excludes replaced ids from `parents`, so this
       check naturally covers post-removal state.
    4. The commit id (explicit or auto-generated) must be unique in
       current state, except when an explicit id is being vacated by
       `replaces:` (E203).

    On success, replaced commits are removed and the new commit is
    appended to the branch's commit list.
    """
    op = cast(CommitOp, parsed.op)
    file = parsed.file
    line = parsed.line

    # --- Branch reference -----------------------
    if not state.has_branch(op.branch):
        report.add(
            ValidationError(
                file=file,
                line=line,
                code="E200",
                message=f"branch {op.branch!r} is not declared",
                field="branch",
            )
        )
        return

    # --- Replaces rules -------------------------
    if op.replaces and not check_replaces_rules(state, parsed, report):
        return

    replaced_set: set[str] = set(op.replaces or [])

    # --- Parents existence ----------------------
    for index, parent_id in enumerate(op.parents or []):
        if parent_id in replaced_set:
            # Rule 7 in `_replaces.py` already caught this; defensive guard.
            return
        if not state.has_commit(parent_id):
            report.add(
                ValidationError(
                    file=file,
                    line=line,
                    code="E201",
                    message=f"parent commit {parent_id!r} is not declared",
                    field=f"parents.{index}",
                )
            )
            return

    # --- Resolve commit id ----------------------
    explicit_id = op.id
    commit_id = explicit_id if explicit_id is not None else _generate_auto_commit_id(state)
    if explicit_id is not None and explicit_id in state.commits and explicit_id not in replaced_set:
        report.add(
            ValidationError(
                file=file,
                line=line,
                code="E203",
                message=f"commit id {explicit_id!r} is already used",
                field="id",
            )
        )
        return

    # --- Resolve `gap` (replaces inheritance) ---
    resolved_gap = _resolve_gap(state, op)

    # --- Apply replaces removals ----------------
    for rid in op.replaces or []:
        _remove_commit(state, rid)

    # --- Add the commit -------------------------
    state.commits[commit_id] = CommitState(
        id=commit_id,
        branch=op.branch,
        msg=op.msg,
        hash=op.hash,
        parents=list(op.parents or []),
        replaces=list(op.replaces or []),
        highlight=bool(op.highlight),
        gap=resolved_gap,
        declaration_file=file,
        declaration_line=line,
    )
    state.branches[op.branch].commit_ids.append(commit_id)

    # --- Resolve `hash: "auto"` -----------------
    if op.hash == "auto":
        state.commits[commit_id].hash = compute_auto_hash(commit_id, effective_parent_ids(state, commit_id, op.branch))


# ==================================================================================================
#  Helpers
# ==================================================================================================
def _resolve_gap(state: State, op: CommitOp) -> int:
    """Resolve the `gap` value to store on a new commit.

    For ordinary commits, `op.gap` (default 0). For `replaces:` commits,
    when `op.gap` is unset, inherit the gap of the *earliest* replaced
    commit — the one appearing earliest in the branch's `commit_ids`
    list. This preserves whatever visual breathing room the original
    chain had: if the replaced segment started at a position with
    `gap=2`, the squash commit lands at the same position.
    """
    if op.gap is not None:
        return op.gap
    if not op.replaces:
        return 0
    branch = state.branches.get(op.branch)
    if branch is None:
        return 0
    replaced_set = set(op.replaces)
    for cid in branch.commit_ids:
        if cid in replaced_set:
            replaced = state.commits.get(cid)
            return replaced.gap if replaced is not None else 0
    return 0


def _generate_auto_commit_id(state: State) -> str:
    """Return the lowest `_c<N>` not already used by a commit in `state`.

    The leading underscore is the convention for auto-generated ids:
    user-supplied ids should not start with `_`, which keeps the two
    namespaces from colliding even when many ops in an import chain
    use auto-generation.
    """
    n = 1
    while f"_c{n}" in state.commits:
        n += 1
    return f"_c{n}"


def _remove_commit(state: State, commit_id: str) -> None:
    """Remove `commit_id` from state.

    Drops the commit from the global commits dict and from its branch's
    commit-ids list. Cross-references (parents, replaces, captured
    `from_branch` snapshots, etc.) are left untouched — `remove` is
    permissive about dangling references; `check_end_of_file` (in
    `gitsvg.state._eof`) catches any that aren't restored.
    """
    commit = state.commits.pop(commit_id, None)
    if commit is None:
        return
    branch = state.branches.get(commit.branch)
    if branch is not None and commit_id in branch.commit_ids:
        branch.commit_ids.remove(commit_id)
