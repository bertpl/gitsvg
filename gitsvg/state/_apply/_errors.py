"""Shared validation-error emitters for the per-op state-apply handlers.

Several handlers raise the same code with the same message shape: `E200`
(branch not declared) across `commit` / `merge` / `pull_request` /
`remove` / `branch`, `E201` (commit not declared) across `highlight` /
`remove` / the `replaces` checks, and `E203` (commit id already used)
across `commit` and `merge`. These helpers single-source the wording so
it can't drift between sites; the caller supplies only what varies —
the offending name, the op field that named it, and the names declared
so far (from which the not-declared emitters compute a did-you-mean
`suggestion`).
"""

from collections.abc import Collection
from difflib import get_close_matches

from gitsvg.errors import ValidationError, ValidationReport

# difflib's own default cutoff. Anything stricter silently drops typos in
# short names ("dev" vs. "div" scores 0.67), and branch names are often
# short; an occasional imperfect suggestion is cheap since it renders as
# a question.
_SUGGESTION_CUTOFF = 0.6


def _closest_declared(name: str, declared: Collection[str]) -> str | None:
    """Return the declared name closest to `name`, or None when nothing is close."""
    matches = get_close_matches(name, declared, n=1, cutoff=_SUGGESTION_CUTOFF)
    return matches[0] if matches else None


def add_branch_not_declared(
    report: ValidationReport,
    *,
    file: str,
    line: int,
    branch: str,
    field: str,
    declared: Collection[str],
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
        declared: Branch names declared so far; the closest one (if
            any) becomes the error's `suggestion`.
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
            suggestion=_closest_declared(branch, declared),
        )
    )


def add_commit_not_declared(
    report: ValidationReport,
    *,
    file: str,
    line: int,
    commit_id: str,
    field: str,
    declared: Collection[str],
) -> None:
    """Add an `E201` (commit not declared) error to `report`.

    Args:
        report: Receives the error.
        file: Source file of the offending op.
        line: 1-based line of the offending op.
        commit_id: The undeclared commit id.
        field: The op field that named the commit (e.g. `"commit"`,
            `"replaces"`, `"commits.0"`).
        declared: Commit ids declared so far; the closest one (if any)
            becomes the error's `suggestion`.
    """
    report.add(
        ValidationError(
            file=file,
            line=line,
            code="E201",
            message=f"commit {commit_id!r} is not declared",
            field=field,
            suggestion=_closest_declared(commit_id, declared),
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
