"""Shared validation-error emitters for the per-op state-apply handlers.

Several handlers raise the same code with the same message shape: `E200`
(branch not declared) across `commit` / `merge` / `pull_request` /
`remove` / `branch`, and `E203` (commit id already used) across `commit`
and `merge`. These helpers single-source the wording so it can't drift
between sites; the caller supplies only what varies — the offending name
and the op field that named it.
"""

from gitsvg.errors import ValidationError, ValidationReport


def add_branch_not_declared(
    report: ValidationReport,
    *,
    file: str,
    line: int,
    branch: str,
    field: str,
    hint: str = "",
) -> None:
    """Add an `E200` (branch not declared) error to `report`.

    Args:
        report: Receives the error.
        file: Source file of the offending op.
        line: 1-based line of the offending op.
        branch: The undeclared branch name.
        field: The op field that named the branch (e.g. `"branch"`,
            `"from"`, `"into"`, `"from_branch"`, `"branches.0"`).
        hint: Optional clarification appended to the message (e.g. the
            `branch` op's "did you mean 'from_commit'?" nudge).
    """
    report.add(
        ValidationError(
            file=file,
            line=line,
            code="E200",
            message=f"branch {branch!r} is not declared{hint}",
            field=field,
        )
    )


def add_commit_id_already_used(
    report: ValidationReport,
    *,
    file: str,
    line: int,
    commit_id: str,
    field: str,
) -> None:
    """Add an `E203` (commit id already used) error to `report`.

    Args:
        report: Receives the error.
        file: Source file of the offending op.
        line: 1-based line of the offending op.
        commit_id: The duplicate commit id.
        field: The op field that named the id (`"id"` for `commit`,
            `"as"` for `merge`).
    """
    report.add(
        ValidationError(
            file=file,
            line=line,
            code="E203",
            message=f"commit id {commit_id!r} is already used",
            field=field,
        )
    )
