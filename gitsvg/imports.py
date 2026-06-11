"""Import resolution — expand `import` ops into the imported file's op stream.

Pipeline-stage module sitting between the parser and the state engine:

    parse → resolve_imports → state-apply → end-of-file checks

The state engine never touches the filesystem; everything import-related
is finished by the time `apply_ops` runs. The resolver takes a list of
`ParsedOp` records (already schema-validated) for one file and returns a
flat expanded list with the same structure — the state engine sees no
`import` ops, only the underlying op stream.

Each `ParsedOp` carries its `(file, line)` source location from the
parser, so downstream errors point at the original location regardless
of how deeply the file was imported.

Import paths are sandboxed: every import in a chain must resolve inside
the top-level input file's directory tree (`E305` otherwise), and input
with no filesystem location (an in-memory string) cannot import at all
(`E306`). Both guards reject before touching the filesystem.
"""

from pathlib import Path

from .errors import ValidationError, ValidationReport
from .file_format.ops import ImportOp
from .parse import ParsedOp, parse_jsonl_text

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
    allow_imports: bool = True,
) -> list[ParsedOp]:
    """Expand any leading `import` op in `parsed_ops` recursively.

    Import paths are confined to the top-level file's directory tree:
    a path that is absolute, or that resolves outside that tree (via
    `..` or a symlink), is rejected with `E305` before any filesystem
    read. Input with no filesystem location (an in-memory string)
    has no such tree, so callers handling it pass
    `allow_imports=False` and any `import` op is rejected with `E306`.

    Args:
        parsed_ops: Schema-validated ops parsed from `file`.
        file: Path of the file the ops were parsed from. Used as the
            base directory for resolving relative import paths, as the
            containment root for them, and as the first entry in the
            cycle stack.
        report: Report to which import-resolution errors are appended.
        depth_limit: Maximum nesting depth. Default 1000.
        allow_imports: When False, any `import` op is rejected with
            `E306` instead of resolved — for input that has no
            filesystem location to resolve against.

    Returns:
        The expanded op stream, with all imports resolved. When
        resolution fails (cycle, depth, escaping path, missing file,
        malformed position), the corresponding ops are dropped and an
        error is appended; the resolver returns the best partial
        expansion it could produce so downstream phases still see the
        bulk of the input.
    """
    resolved_file = file.resolve()
    return _expand(
        parsed_ops,
        current_file=resolved_file,
        root=resolved_file.parent,
        allow_imports=allow_imports,
        cycle_stack=[resolved_file],
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
    root: Path,
    allow_imports: bool,
    cycle_stack: list[Path],
    depth: int,
    depth_limit: int,
    report: ValidationReport,
) -> list[ParsedOp]:
    """Expand the import in `parsed_ops` (if any) within the current call.

    Returns the expanded stream for this file. The `cycle_stack` is the
    chain of resolved absolute paths from the top-level file down to
    (but not including) any file we recurse into. `root` is the
    top-level file's directory — the containment root every import in
    the chain must stay inside.
    """
    parsed_ops, proceed = _gate_leading_import(parsed_ops, report)
    if not proceed:
        return parsed_ops

    # First op is import — resolve it.
    import_parsed = parsed_ops[0]
    import_op = import_parsed.op
    assert isinstance(import_op, ImportOp)
    rest = list(parsed_ops[1:])

    # --- No-root input --------------------------
    if not allow_imports:
        report.add(
            ValidationError(
                file=import_parsed.file,
                line=import_parsed.line,
                code="E306",
                message="`import` is not available for in-memory input; inline the imported ops instead",
                field="path",
            )
        )
        return rest

    # --- Containment ----------------------------
    # Both guards fire before any filesystem read, so a rejected path
    # leaks no existence or content information. The absolute-path check
    # precedes the join: joining a base with an absolute path silently
    # discards the base. Error messages name only the requested path,
    # never the resolved target.
    if Path(import_op.path).is_absolute():
        report.add(
            ValidationError(
                file=import_parsed.file,
                line=import_parsed.line,
                code="E305",
                message=(
                    f"import path {import_op.path!r} is absolute; "
                    f"only relative paths inside the top-level file's directory are allowed"
                ),
                field="path",
            )
        )
        return rest

    target = (current_file.parent / import_op.path).resolve()

    if not target.is_relative_to(root):
        report.add(
            ValidationError(
                file=import_parsed.file,
                line=import_parsed.line,
                code="E305",
                message=f"import path {import_op.path!r} escapes the top-level file's directory",
                field="path",
            )
        )
        return rest

    # --- Cycle check ----------------------------
    if target in cycle_stack:
        chain = " -> ".join(str(p) for p in [*cycle_stack, target])
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
        # `exc.strerror` keeps the useful OS diagnostic ("No such file or
        # directory") without echoing the resolved absolute path that the
        # full exception text would carry.
        report.add(
            ValidationError(
                file=import_parsed.file,
                line=import_parsed.line,
                code="E302",
                message=f"cannot read imported file {import_op.path!r}: {exc.strerror or exc}",
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
        root=root,
        allow_imports=allow_imports,
        cycle_stack=[*cycle_stack, target],
        depth=depth + 1,
        depth_limit=depth_limit,
        report=report,
    )

    return expanded + rest


def _gate_leading_import(parsed_ops: list[ParsedOp], report: ValidationReport) -> tuple[list[ParsedOp], bool]:
    """Normalize `parsed_ops` to a single leading `import`, flagging violations.

    Enforces the "at most one `import`, and it must be first" rule before the
    resolver touches the filesystem. Returns `(ops, proceed)`:

    - `(ops, False)` — terminal: nothing to expand. Either no `import` is
      present, or the sole `import` was misplaced (E304) and dropped. The caller
      returns `ops` unchanged.
    - `(ops, True)` — `ops` has exactly one `import` at position 0. Any extra
      `import` ops were flagged (E303) and dropped; the caller resolves the
      survivor.

    Args:
        parsed_ops: The file's ops.
        report: Receives any E303 / E304 errors.
    """
    import_indices = [i for i, p in enumerate(parsed_ops) if isinstance(p.op, ImportOp)]

    # No imports — nothing to expand.
    if not import_indices:
        return list(parsed_ops), False

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
        extras = set(import_indices[1:])
        parsed_ops = [p for i, p in enumerate(parsed_ops) if i not in extras]
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
        return [p for i, p in enumerate(parsed_ops) if i != first_import_index], False

    return parsed_ops, True
