"""The `gitsvg schema` CLI command.

Three forms, supporting agent-friendly progressive disclosure:

- `gitsvg schema`             - index of all ops + file-level constraints
- `gitsvg schema <op>`        - JSON Schema for one op
- `gitsvg schema --list-ops`  - bare op names, one per line
"""

import json
import sys

import click

from gitsvg.file_format import list_op_names, op_one_liner, op_schema
from gitsvg.file_format.ops import OP_BY_NAME


# ==================================================================================================
#  Click command
# ==================================================================================================
@click.command(name="schema")
@click.argument("op_name", required=False)
@click.option("--list-ops", "list_ops", is_flag=True, help="Print bare op names, one per line.")
def schema_command(op_name: str | None, list_ops: bool) -> None:
    """Print JSON Schema for the gitsvg input format.

    With no arguments, prints an index of all ops with one-line
    descriptions. Pass an op name (e.g. `schema commit`) to print that
    op's full JSON Schema. Pass `--list-ops` to print the bare list of
    op names, one per line.
    """
    if list_ops:
        for name in list_op_names():
            click.echo(name)
        return

    if op_name is None:
        click.echo(_render_index())
        return

    if op_name not in OP_BY_NAME:
        click.echo(f"Unknown op: {op_name!r}", err=True)
        click.echo(f"Known ops: {', '.join(list_op_names())}", err=True)
        sys.exit(2)

    click.echo(json.dumps(op_schema(op_name), indent=2))


# ==================================================================================================
#  Index rendering
# ==================================================================================================
def _render_index() -> str:
    """Render the prose-form op index for `gitsvg schema` with no arguments.

    Returns:
        A multi-line string with the op table and the file-level
        constraints. Suitable for printing directly to stdout.
    """
    # --- header + op table ----------------------
    lines: list[str] = ["gitsvg input format - operations", ""]

    width = max(len(name) for name in list_op_names())
    for name in list_op_names():
        lines.append(f"  {name.ljust(width)}  {op_one_liner(name)}")

    # --- file-level constraints -----------------
    lines += [
        "",
        "File-level constraints:",
        "  - One operation per line; empty lines skipped.",
        "  - At most one `import` op per file.",
        "  - If present, `import` must be the first op in the file.",
        "",
        "Run `gitsvg schema <op>` for an op's full JSON Schema.",
        "Run `gitsvg schema --list-ops` for a bare op-name list.",
    ]

    return "\n".join(lines)
