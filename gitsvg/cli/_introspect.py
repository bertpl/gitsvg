"""Shared plumbing for the JSON-introspection CLI commands (`state`, `layout`).

`gitsvg state` and `gitsvg layout` have the same command shape — run the
validate pipeline on an input, then emit a JSON view of the result —
differing only in which JSON payload they build from the resolved
`(state, theme)`. This module owns the common click surface (the shared
INPUT argument + `-o` option), the dir-guard / stdout-vs-file dispatch,
and the per-input runners; each command supplies a `payload_fn` and its
output extension.
"""

import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import NoReturn

import click

from gitsvg.errors import ValidationReport
from gitsvg.state import State
from gitsvg.theme import Theme

from ._bulk import print_report_errors, process_input
from ._pipeline import run_validate_pipeline

PayloadFn = Callable[[State, Theme], object]
"""Builds the JSON-serializable payload from the resolved state and theme."""


def introspection_command(name: str) -> Callable[[Callable], click.Command]:
    """Decorator applying the shared click surface for an introspection command.

    Stacks the common INPUT argument and `-o/--output` option onto the
    command and registers it under `name`. The decorated function keeps
    its own docstring (the per-command help text) and body.

    Args:
        name: The subcommand name (e.g. `"state"`).

    Returns:
        A decorator turning a `(input_path, output_path)` function into a
        registered `click.Command`.
    """

    def decorate(fn: Callable) -> click.Command:
        fn = click.option(
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
        )(fn)
        fn = click.argument(
            "input_path",
            type=click.Path(exists=True, dir_okay=True, file_okay=True, path_type=Path),
        )(fn)
        return click.command(name=name)(fn)

    return decorate


def run_introspection_command(
    input_path: Path,
    output_path: Path | None,
    *,
    output_ext: str,
    payload_fn: PayloadFn,
) -> NoReturn:
    """Dispatch a JSON-introspection command across its three invocation forms.

    Mirrors `gitsvg render`: single-file-to-stdout, single-file-to-file,
    and bulk directory walking. Exits the process with the appropriate
    status; never returns.

    Args:
        input_path: A `.gitsvg.jsonl` file, or a directory in bulk mode.
        output_path: Output file/dir, or None for single-file stdout mode.
        output_ext: Per-input output suffix in bulk mode (e.g.
            `".state.json"`).
        payload_fn: Builds the JSON payload from the resolved state and
            theme.
    """
    if input_path.is_dir() and output_path is None:
        click.echo(
            "INPUT is a directory; -o OUTPUT_DIR is required for bulk mode.",
            err=True,
        )
        sys.exit(2)

    if output_path is None:
        sys.exit(_to_stdout(input_path, payload_fn))

    sys.exit(
        process_input(
            input_path,
            output_path,
            output_ext=output_ext,
            process_one=lambda inp, outp: _to_file(inp, outp, payload_fn),
        )
    )


def _to_stdout(input_path: Path, payload_fn: PayloadFn) -> int:
    """Run the pipeline and print the JSON payload to stdout.

    Returns:
        0 after emitting the JSON on a clean report; 1 after writing the
        errors to stderr on a dirty one.
    """
    state, report, theme = run_validate_pipeline(input_path)
    if not report.is_clean():
        print_report_errors(report)
        return 1
    click.echo(json.dumps(payload_fn(state, theme), indent=2))
    return 0


def _to_file(input_path: Path, output_path: Path, payload_fn: PayloadFn) -> ValidationReport:
    """Run the pipeline and write the JSON payload to `output_path` when clean.

    Returns:
        The validation report; the file is written only on a clean
        report (a dirty one leaves no output).
    """
    state, report, theme = run_validate_pipeline(input_path)
    if not report.is_clean():
        return report
    output_path.write_text(json.dumps(payload_fn(state, theme), indent=2) + "\n")
    return report
