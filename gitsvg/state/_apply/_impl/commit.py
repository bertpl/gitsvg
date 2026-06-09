"""Apply a `commit` op to state — branch existence, parents, replaces, id uniqueness."""

from typing import cast

from gitsvg.errors import ValidationReport
from gitsvg.file_format.ops import CommitOp
from gitsvg.parse import ParsedOp
from gitsvg.state._apply._checks import check_replaces_rules
from gitsvg.state._apply._errors import add_branch_not_declared, add_commit_id_already_used
from gitsvg.state._auto_hash import compute_auto_hash
from gitsvg.state._state import CommitState, State
from gitsvg.theme import ThemeBuilder


def apply_commit_op(state: State, builder: ThemeBuilder, parsed: ParsedOp, report: ValidationReport) -> None:
    """Apply a `commit` op.

    Validation order (no state mutation until everything passes):

    1. The branch reference must exist (E200).
    2. If `replaces:` is set, the rule check must pass.
    3. The commit id (explicit or auto-generated) must be unique in
       current state, except when an explicit id is being vacated by
       `replaces:` (E203).

    On success, replaced commits are removed and the new commit is
    appended to the branch's commit list. Its parents are resolved
    structurally: a commit op contributes exactly its chain parent
    (the branch's tip after any `replaces:` removal, or the branch's
    rooted-on commit when it is the branch's first commit), so the
    stored list is the single canonical parent set every downstream
    consumer reads. Multi-parent commits come only from the `merge` op.
    """
    op = cast("CommitOp", parsed.op)
    file = parsed.file
    line = parsed.line

    # --- Branch reference -----------------------
    if not state.has_branch(op.branch):
        add_branch_not_declared(report, file=file, line=line, branch=op.branch, field="branch")
        return

    # --- Replaces rules -------------------------
    if op.replaces and not check_replaces_rules(state, parsed, report):
        return

    replaced_set: set[str] = set(op.replaces or [])

    # --- Resolve commit id ----------------------
    explicit_id = op.id
    commit_id = explicit_id if explicit_id is not None else _generate_auto_commit_id(state)
    if explicit_id is not None and explicit_id in state.commits and explicit_id not in replaced_set:
        add_commit_id_already_used(report, file=file, line=line, commit_id=explicit_id, field="id")
        return

    # --- Resolve `gap` (replaces inheritance) ---
    resolved_gap = _resolve_gap(state, op)

    # --- Apply replaces removals ----------------
    for rid in op.replaces or []:
        state.remove_commit(rid)

    # --- Resolve canonical parents --------------
    # Read after removal and before the append below, so the chain parent is
    # the post-removal ref target and never points at the new commit itself.
    chain_parent = state.branch_tip(op.branch)
    parents = [chain_parent] if chain_parent is not None else []

    # --- Add the commit -------------------------
    state.commits[commit_id] = CommitState(
        id=commit_id,
        branch=op.branch,
        msg=op.msg,
        hash=op.hash,
        parents=parents,
        replaces=list(op.replaces or []),
        highlight=bool(op.highlight),
        gap=resolved_gap,
        declaration_file=file,
        declaration_line=line,
    )
    state.branches[op.branch].commit_ids.append(commit_id)

    # --- Resolve `hash: "auto"` -----------------
    if op.hash == "auto":
        state.commits[commit_id].hash = compute_auto_hash(commit_id, parents)


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
