"""The `gitsvg schema` CLI command.

Supports agent-friendly progressive disclosure of the input format:

- `gitsvg schema`                   - index of all ops + file-level constraints
- `gitsvg schema <op>`              - JSON Schema for one op
- `gitsvg schema --list-ops`        - bare op names, one per line
- `gitsvg schema themes`            - bare list of registered named-theme names
- `gitsvg schema theme <name>`      - resolved field values for the named theme
"""

import json
import sys

import click

from gitsvg.file_format import list_op_names, op_one_liner, op_schema
from gitsvg.file_format.ops import OP_BY_NAME
from gitsvg.theme._apply import NAMED_THEMES


# ==================================================================================================
#  Click command
# ==================================================================================================
@click.command(name="schema")
@click.argument("op_name", required=False)
@click.argument("theme_name", required=False)
@click.option("--list-ops", "list_ops", is_flag=True, help="Print bare op names, one per line.")
def schema_command(op_name: str | None, theme_name: str | None, list_ops: bool) -> None:
    """Print JSON Schema for the gitsvg input format.

    With no arguments, prints an index of all ops with one-line
    descriptions. Pass an op name (e.g. `schema commit`) to print that
    op's full JSON Schema. Pass `--list-ops` to print the bare list of
    op names, one per line. Pass `themes` to list the registered named
    themes, or `theme <name>` to print the resolved field values for
    one of them at the default orientation.
    """
    if list_ops:
        for name in list_op_names():
            click.echo(name)
        return

    if op_name == "themes":
        for name in sorted(NAMED_THEMES):
            click.echo(name)
        return

    if op_name == "theme" and theme_name is not None:
        _emit_resolved_theme(theme_name)
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
#  Resolved-theme inspection
# ==================================================================================================
def _emit_resolved_theme(theme_name: str) -> None:
    """Print the resolved field values for `theme_name` at the default orientation.

    Unknown name exits non-zero with the list of registered names.

    Args:
        theme_name: Name of a registered theme (one of `NAMED_THEMES`).
    """
    if theme_name not in NAMED_THEMES:
        known = ", ".join(sorted(NAMED_THEMES))
        click.echo(f"Unknown theme: {theme_name!r}", err=True)
        click.echo(f"Known themes: {known}", err=True)
        sys.exit(2)

    theme_cls = NAMED_THEMES[theme_name]
    resolved = theme_cls.build({})
    click.echo(json.dumps(resolved.model_dump(mode="json"), indent=2))


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
        "Run `gitsvg schema themes` for the list of registered named themes.",
        "Run `gitsvg schema theme <name>` to inspect a named theme's resolved values.",
    ]

    return "\n".join(lines)
