"""The `gitsvg validate` CLI command.

Runs parse + per-op shape validation + per-op semantic validation against
an input file and reports any errors found. Import-resolution and
end-of-file cross-reference checks land in subsequent versions of the
validator.

Output:

- Default: plain text, one error per line, format
  `path:line: [code] field: message`. Exit non-zero on any error.
- `--json`: structured JSON `{ "ok": bool, "errors": [...] }` with all
  fields of `ValidationError` preserved.
"""

import dataclasses
import json
import sys
from pathlib import Path

import click

from gitsvg.parse import parse_jsonl_file
from gitsvg.state import apply_ops


# ==================================================================================================
#  Click command
# ==================================================================================================
@click.command(name="validate")
@click.argument("path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--json", "json_output", is_flag=True, help="Emit a structured JSON report instead of plain text.")
def validate_command(path: Path, json_output: bool) -> None:
    """Validate a `.gitsvg.jsonl` input file.

    Runs JSONL parsing, per-op shape validation, and per-op semantic
    validation. Prints any errors and exits non-zero when validation
    fails.
    """
    parsed_ops, report = parse_jsonl_file(path)
    apply_ops(parsed_ops, report)
    if json_output:
        click.echo(_render_json(report))
    else:
        _print_plain(report)
    sys.exit(0 if report.is_clean() else 1)


# ==================================================================================================
#  Output rendering
# ==================================================================================================
def _print_plain(report) -> None:
    """Print the report as plain text, one error per line."""
    for err in report.errors:
        click.echo(err.format())


def _render_json(report) -> str:
    """Render the report as a JSON string with shape `{ok, errors}`."""
    payload = {
        "ok": report.is_clean(),
        "errors": [dataclasses.asdict(err) for err in report.errors],
    }
    return json.dumps(payload, indent=2)
