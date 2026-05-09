"""The `gitsvg errors` CLI command.

Three forms, mirroring `schema` for agent-friendly progressive disclosure:

- `gitsvg errors`              - index of all error codes
- `gitsvg errors <code>`       - long-form catalog entry for one code
- `gitsvg errors --list-codes` - bare list of codes, one per line
"""

import sys

import click

from gitsvg.errors import all_codes, find_error_code, load_catalog_entry


# ==================================================================================================
#  Click command
# ==================================================================================================
@click.command(name="errors")
@click.argument("code", required=False)
@click.option("--list-codes", "list_codes", is_flag=True, help="Print bare error codes, one per line.")
def errors_command(code: str | None, list_codes: bool) -> None:
    """Print the gitsvg validator error code catalog.

    With no arguments, prints an index of all registered error codes
    with one-line summaries. Pass an error code (e.g. `errors E210`)
    to print that code's full long-form catalog entry. Pass
    `--list-codes` to print only the bare list of codes.
    """
    if list_codes:
        for entry in all_codes():
            click.echo(entry.code)
        return

    if code is None:
        click.echo(_render_index())
        return

    entry = find_error_code(code)
    if entry is None:
        click.echo(f"Unknown error code: {code!r}", err=True)
        sys.exit(2)

    body = load_catalog_entry(code)
    if body is None:
        click.echo(f"[{entry.code}] {entry.summary}")
        click.echo()
        click.echo("(no detailed catalog entry yet)")
        return

    click.echo(body)


# ==================================================================================================
#  Index rendering
# ==================================================================================================
def _render_index() -> str:
    """Render the prose-form error code index for `gitsvg errors` with no arguments.

    Returns:
        A multi-line string with the code table, suitable for printing
        directly to stdout. When no codes are registered yet, the
        output explains the registry is empty rather than printing a
        blank table.
    """
    entries = all_codes()
    lines: list[str] = ["gitsvg validation - error codes", ""]

    if not entries:
        lines += [
            "(no error codes registered yet)",
            "",
            "Codes are added as features land. Run `gitsvg errors --list-codes` once the registry is populated.",
        ]
    else:
        width = max(len(e.code) for e in entries)
        for entry in entries:
            lines.append(f"  {entry.code.ljust(width)}  {entry.summary}")

    lines += [
        "",
        "Run `gitsvg errors <code>` for a code's full explanation.",
        "Run `gitsvg errors --list-codes` for a bare code list.",
    ]
    return "\n".join(lines)
