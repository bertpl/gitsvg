"""The `gitsvg validate` CLI command.

Runs the full single-file validator pipeline: parse → import resolution →
per-op schema → per-op semantic → end-of-file cross-reference check.

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

from gitsvg.cli._bulk import print_report_errors
from gitsvg.cli._pipeline import run_validate_pipeline
from gitsvg.errors import ValidationReport


# ==================================================================================================
#  Click command
# ==================================================================================================
@click.command(name="validate")
@click.argument("path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--json", "json_output", is_flag=True, help="Emit a structured JSON report instead of plain text.")
def validate_command(path: Path, json_output: bool) -> None:
    """Validate a `.gitsvg.jsonl` input file.

    Runs JSONL parsing, import resolution, per-op schema validation,
    per-op semantic validation, and end-of-file cross-reference
    validation. Prints any errors and exits non-zero when validation
    fails.
    """
    _state, report, _theme = run_validate_pipeline(path)
    if json_output:
        click.echo(_render_json(report))
    else:
        _print_plain(report)
    sys.exit(0 if report.is_clean() else 1)


# ==================================================================================================
#  Output rendering
# ==================================================================================================
def _print_plain(report: ValidationReport) -> None:
    """Print the report as plain text to stdout, one error per line."""
    print_report_errors(report, err=False)


def _render_json(report: ValidationReport) -> str:
    """Render the report as a JSON string with structure `{ok, errors}`."""
    payload = {
        "ok": report.is_clean(),
        "errors": [dataclasses.asdict(err) for err in report.errors],
    }
    return json.dumps(payload, indent=2)
