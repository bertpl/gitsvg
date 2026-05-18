"""The `gitsvg state` CLI command.

Emits a JSON snapshot of the diagram — branches, commits with their
parent chain, and open pull requests — as a structural description
of the resolved graph. The intended consumer is an LLM agent that
authored a `.gitsvg.jsonl` file and needs to read back the resolved
structure — auto-generated commit ids, resolved hashes (the
`"auto"` sentinel turned concrete), current branch heads, and the
parent chain — without re-parsing its own input or round-tripping
through the rendered SVG.

Three invocation forms, mirroring `gitsvg render`:

- *Single-file to stdout* — `gitsvg state INPUT.jsonl`. Writes the
  JSON to stdout.
- *Single-file to file* — `gitsvg state INPUT.jsonl -o OUTPUT.json`.
  Writes the JSON to the given file.
- *Bulk* — `gitsvg state INPUT_DIR -o OUTPUT_DIR`. Recursively
  walks `INPUT_DIR` for `*.gitsvg.jsonl` files, writes one
  `<stem>.state.json` per input under `OUTPUT_DIR`, mirroring
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
from gitsvg.state import state_to_json


@click.command(name="state")
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
def state_command(input_path: Path, output_path: Path | None) -> None:
    """Emit a JSON snapshot of the diagram (branches, commits, open pull requests).

    With a single file at INPUT and no `-o`, writes the JSON to
    stdout. With `-o OUTPUT.json`, writes to that file. With a
    directory at INPUT and a directory at `-o`, recursively walks
    INPUT for `*.gitsvg.jsonl` files and writes one
    `<stem>.state.json` per input under OUTPUT, preserving
    subdirectory structure.

    Runs the same validation pipeline as `gitsvg validate` per
    input. Exits non-zero (writing nothing for that input) on any
    validation error.

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
        sys.exit(_state_to_stdout(input_path))

    sys.exit(
        process_input(
            input_path,
            output_path,
            output_ext=".state.json",
            process_one=_state_to_file,
        )
    )


def _state_to_stdout(input_path: Path) -> int:
    """Run the pipeline, print the JSON to stdout, and return an exit code.

    Args:
        input_path: A `.gitsvg.jsonl` input file.

    Returns:
        0 on clean validation (after emitting the JSON), 1 when
        validation failed (after writing errors to stderr).
    """
    state, report, _theme = run_validate_pipeline(input_path)
    if not report.is_clean():
        for err in report.errors:
            click.echo(err.format(), err=True)
        return 1
    click.echo(json.dumps(state_to_json(state), indent=2))
    return 0


def _state_to_file(input_path: Path, output_path: Path) -> ValidationReport:
    """Run the pipeline and write the JSON to `output_path` when clean.

    Args:
        input_path: A `.gitsvg.jsonl` input file.
        output_path: Where to write the JSON.

    Returns:
        The validation report. On clean reports the file has been
        written; on dirty reports no file is created.
    """
    state, report, _theme = run_validate_pipeline(input_path)
    if not report.is_clean():
        return report
    output_path.write_text(json.dumps(state_to_json(state), indent=2) + "\n")
    return report
