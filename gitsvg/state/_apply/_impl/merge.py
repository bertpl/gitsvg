"""Apply a `merge` op to state — emits a two-parent commit on `into`."""

from typing import cast

from gitsvg.errors import ValidationError, ValidationReport
from gitsvg.file_format.ops import MergeOp
from gitsvg.parse import ParsedOp
from gitsvg.state._apply._errors import add_branch_not_declared, add_commit_id_already_used
from gitsvg.state._auto_hash import compute_auto_hash
from gitsvg.state._state import CommitState, State
from gitsvg.theme import ThemeBuilder

from .commit import _generate_auto_commit_id


def apply_merge_op(state: State, builder: ThemeBuilder, parsed: ParsedOp, report: ValidationReport) -> None:
    """Apply a `merge` op.

    A merge produces a commit on `into` whose parents are the into
    branch's chain parent (its prior tip, or its rooted-on commit when
    empty) first and the current tip of `from` second — the single
    canonical, chain-first parent list every downstream consumer reads.
    When the optional `as` field is set, the new commit takes that id;
    otherwise it is auto-generated.

    Validation:

    1. `from` must reference an existing branch (E200).
    2. `into` must reference an existing branch (E200).
    3. No open pull-request may have the same `(from, into)` pair
       (E213) — explicit close-before-merge keeps the lifecycle
       legible and prevents silent PR consumption.
    4. When `as:` is set, the id must not already be used (E203).
    """
    op = cast(MergeOp, parsed.op)
    file = parsed.file
    line = parsed.line

    if not state.has_branch(op.from_):
        add_branch_not_declared(report, file=file, line=line, branch=op.from_, field="from")
        return

    if not state.has_branch(op.into):
        add_branch_not_declared(report, file=file, line=line, branch=op.into, field="into")
        return

    for pr in state.pull_requests.values():
        if pr.from_branch == op.from_ and pr.into_branch == op.into:
            report.add(
                ValidationError(
                    file=file,
                    line=line,
                    code="E213",
                    message=(
                        f"cannot merge {op.from_!r} into {op.into!r}: open pull_request {pr.id!r} "
                        f"matches this pair; close it via 'remove' first"
                    ),
                )
            )
            return

    explicit_id = op.as_
    merge_id = explicit_id if explicit_id is not None else _generate_auto_commit_id(state)
    if explicit_id is not None and explicit_id in state.commits:
        add_commit_id_already_used(report, file=file, line=line, commit_id=explicit_id, field="as")
        return

    parents: list[str] = []
    for parent_id in (state.chain_parent(op.into), state.branch_tip(op.from_)):
        if parent_id is not None and parent_id not in parents:
            parents.append(parent_id)

    state.commits[merge_id] = CommitState(
        id=merge_id,
        branch=op.into,
        msg=op.msg,
        hash=op.hash,
        parents=parents,
        # Merge deliberately skips `_resolve_gap` (used by `commit:`): it never
        # squashes, so there is no `replaces` gap to inherit.
        gap=op.gap or 0,
        declaration_file=file,
        declaration_line=line,
    )
    state.branches[op.into].commit_ids.append(merge_id)

    # --- Resolve `hash: "auto"` -----------------
    if op.hash == "auto":
        state.commits[merge_id].hash = compute_auto_hash(merge_id, parents)
