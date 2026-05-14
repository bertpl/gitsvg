"""Import resolver — expand a top-level file's leading `import` op into the
imported file's ops, recursively, with cycle detection and a depth cap.

The resolver sits between the parser and the state engine. It takes a list
of `ParsedOp` records (already schema-validated) for one file and returns a
flat expanded list with the same structure — the state engine sees no `import`
ops, only the underlying op stream.

Each `ParsedOp` already carries `(file, line)` provenance from the parser,
so downstream errors point at the original location regardless of how
deeply the file was imported.
"""

from pathlib import Path

from gitsvg.errors import ValidationError, ValidationReport
from gitsvg.file_format.ops import ImportOp
from gitsvg.parse import ParsedOp, parse_jsonl_text

# Maximum depth of an import chain — guards against pathological inputs
# (cycles are caught separately and earlier). Documented as a user-facing
# limit in the `import` section of the format spec.
DEFAULT_DEPTH_LIMIT = 1000


def resolve_imports(
    parsed_ops: list[ParsedOp],
    *,
    file: Path,
    report: ValidationReport,
    depth_limit: int = DEFAULT_DEPTH_LIMIT,
) -> list[ParsedOp]:
    """Expand any leading `import` op in `parsed_ops` recursively.

    Args:
        parsed_ops: Schema-validated ops parsed from `file`.
        file: Path of the file the ops were parsed from. Used as the
            base directory for resolving relative import paths and as
            the first entry in the cycle stack.
        report: Report to which import-resolution errors are appended.
        depth_limit: Maximum nesting depth. Default 1000.

    Returns:
        The expanded op stream, with all imports resolved. When
        resolution fails (cycle, depth, missing file, malformed
        position), the corresponding ops are dropped and an error is
        appended; the resolver returns the best partial expansion it
        could produce so downstream phases still see the bulk of the
        input.
    """
    resolved_root = file.resolve()
    return _expand(
        parsed_ops,
        current_file=resolved_root,
        cycle_stack=[resolved_root],
        depth=0,
        depth_limit=depth_limit,
        report=report,
    )


# ==================================================================================================
#  Internal recursion
# ==================================================================================================
def _expand(
    parsed_ops: list[ParsedOp],
    *,
    current_file: Path,
    cycle_stack: list[Path],
    depth: int,
    depth_limit: int,
    report: ValidationReport,
) -> list[ParsedOp]:
    """Expand the import in `parsed_ops` (if any) within the current call.

    Returns the expanded stream for this file. The `cycle_stack` is the
    chain of resolved absolute paths from the top-level file down to
    (but not including) any file we recurse into.
    """
    import_indices = [i for i, p in enumerate(parsed_ops) if isinstance(p.op, ImportOp)]

    # No imports — nothing to expand.
    if not import_indices:
        return list(parsed_ops)

    # Multiple imports — flag every one after the first; keep going with the first.
    if len(import_indices) > 1:
        for extra_index in import_indices[1:]:
            extra = parsed_ops[extra_index]
            report.add(
                ValidationError(
                    file=extra.file,
                    line=extra.line,
                    code="E303",
                    message="multiple `import` ops in one file (only one is allowed)",
                )
            )
        # Drop the extra import ops and continue with the first one only.
        keep = {i for i in range(len(parsed_ops)) if i not in import_indices[1:]}
        parsed_ops = [p for i, p in enumerate(parsed_ops) if i in keep]
        import_indices = [import_indices[0]]

    first_import_index = import_indices[0]

    # Import not at position 0 — flag it and drop the import op.
    if first_import_index != 0:
        misplaced = parsed_ops[first_import_index]
        report.add(
            ValidationError(
                file=misplaced.file,
                line=misplaced.line,
                code="E304",
                message="`import` must be the first op in the file",
            )
        )
        return [p for i, p in enumerate(parsed_ops) if i != first_import_index]

    # First op is import — resolve it.
    import_parsed = parsed_ops[0]
    import_op = import_parsed.op
    assert isinstance(import_op, ImportOp)
    rest = list(parsed_ops[1:])

    target = (current_file.parent / import_op.path).resolve()

    # --- Cycle check ----------------------------
    if target in cycle_stack:
        chain = " -> ".join(str(p) for p in cycle_stack + [target])
        report.add(
            ValidationError(
                file=import_parsed.file,
                line=import_parsed.line,
                code="E300",
                message=f"import cycle detected: {chain}",
                field="path",
            )
        )
        return rest

    # --- Depth check ----------------------------
    if depth + 1 > depth_limit:
        report.add(
            ValidationError(
                file=import_parsed.file,
                line=import_parsed.line,
                code="E301",
                message=f"import depth exceeds limit of {depth_limit}",
                field="path",
            )
        )
        return rest

    # --- Read + parse the imported file ---------
    try:
        text = target.read_text(encoding="utf-8")
    except (FileNotFoundError, IsADirectoryError, PermissionError, OSError) as exc:
        report.add(
            ValidationError(
                file=import_parsed.file,
                line=import_parsed.line,
                code="E302",
                message=f"cannot read imported file {str(target)!r}: {exc}",
                field="path",
            )
        )
        return rest

    imported_parsed, imported_report = parse_jsonl_text(text, file=str(target))
    for err in imported_report.errors:
        report.add(err)

    # --- Recurse --------------------------------
    expanded = _expand(
        imported_parsed,
        current_file=target,
        cycle_stack=cycle_stack + [target],
        depth=depth + 1,
        depth_limit=depth_limit,
        report=report,
    )

    return expanded + rest
