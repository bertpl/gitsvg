"""The `gitsvg layout` CLI command.

Emits the resolved layout (slot positions, lane assignments, arcs,
guides, open pull-request geometry) as a JSON document. The intended
consumer is a human or agent debugging visual placement — "why is
this branch in lane 3", "where does the merge arc land" — without
round-tripping through the rendered SVG.

Three invocation forms, mirroring `gitsvg state` and `gitsvg render`:

- *Single-file to stdout* — `gitsvg layout INPUT.jsonl`. Writes the
  JSON to stdout.
- *Single-file to file* — `gitsvg layout INPUT.jsonl -o OUTPUT.json`.
  Writes the JSON to the given file.
- *Bulk* — `gitsvg layout INPUT_DIR -o OUTPUT_DIR`. Recursively
  walks `INPUT_DIR` for `*.gitsvg.jsonl` files, writes one
  `<stem>.layout.json` per input under `OUTPUT_DIR`, mirroring
  subdirectory structure.

Validation errors print to stderr and exit non-zero; no JSON is
emitted for a failing input. Output format may change before
gitsvg 1.0 — pin a version when caching the schema.
"""

import json
import sys
from pathlib import Path

import click

from gitsvg.cli._bulk import process_input
from gitsvg.cli._pipeline import run_validate_pipeline
from gitsvg.errors import ValidationReport
from gitsvg.layout import compute_layout, layout_to_json


@click.command(name="layout")
@click.argument(
    "input_path",
    type=click.Path(exists=True, dir_okay=True, file_okay=True, path_type=Path),
)
@click.option(
    "-o",
    "--output",
    "output_path",
    required=False,
    default=None,
    type=click.Path(dir_okay=True, file_okay=True, path_type=Path),
    help=(
        "Path to write the JSON to (or output directory when INPUT is a directory). "
        "Omit to print to stdout in single-file mode; required for bulk mode."
    ),
)
def layout_command(input_path: Path, output_path: Path | None) -> None:
    """Emit a JSON view of the resolved layout (grid, lanes, arcs, guides, pull-request geometry).

    With a single file at INPUT and no `-o`, writes the JSON to
    stdout. With `-o OUTPUT.json`, writes to that file. With a
    directory at INPUT and a directory at `-o`, recursively walks
    INPUT for `*.gitsvg.jsonl` files and writes one
    `<stem>.layout.json` per input under OUTPUT, preserving
    subdirectory structure.

    Runs the same validation pipeline as `gitsvg validate` per
    input, then computes the layout. Exits non-zero (writing
    nothing for that input) on any validation error.

    Output format may change before gitsvg 1.0; pin a gitsvg
    version when caching the schema.
    """
    if input_path.is_dir() and output_path is None:
        click.echo(
            "INPUT is a directory; -o OUTPUT_DIR is required for bulk mode.",
            err=True,
        )
        sys.exit(2)

    if output_path is None:
        sys.exit(_layout_to_stdout(input_path))

    sys.exit(
        process_input(
            input_path,
            output_path,
            output_ext=".layout.json",
            process_one=_layout_to_file,
        )
    )


def _layout_to_stdout(input_path: Path) -> int:
    """Run the pipeline, print the JSON to stdout, and return an exit code.

    Args:
        input_path: A `.gitsvg.jsonl` input file.

    Returns:
        0 on clean validation (after emitting the JSON), 1 when
        validation failed (after writing errors to stderr).
    """
    state, report, theme = run_validate_pipeline(input_path)
    if not report.is_clean():
        for err in report.errors:
            click.echo(err.format(), err=True)
        return 1
    layout_settings, _ = theme.split()
    layout = compute_layout(state, layout_settings)
    click.echo(json.dumps(layout_to_json(layout), indent=2))
    return 0


def _layout_to_file(input_path: Path, output_path: Path) -> ValidationReport:
    """Run the pipeline and write the JSON to `output_path` when clean.

    Args:
        input_path: A `.gitsvg.jsonl` input file.
        output_path: Where to write the JSON.

    Returns:
        The validation report. On clean reports the file has been
        written; on dirty reports no file is created.
    """
    state, report, theme = run_validate_pipeline(input_path)
    if not report.is_clean():
        return report
    layout_settings, _ = theme.split()
    layout = compute_layout(state, layout_settings)
    output_path.write_text(json.dumps(layout_to_json(layout), indent=2) + "\n")
    return report
