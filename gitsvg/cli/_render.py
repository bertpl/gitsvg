"""The `gitsvg render` CLI command.

Two invocation forms:

- *Single-file* — `gitsvg render INPUT.jsonl -o OUTPUT.svg`. Runs
  the full validate pipeline on `INPUT.jsonl`, computes a layout,
  renders the result, and writes one SVG to `OUTPUT.svg`.
- *Bulk* — `gitsvg render INPUT_DIR -o OUTPUT_DIR`. Recursively
  walks `INPUT_DIR` for `*.gitsvg.jsonl` files, renders each one
  to a mirrored path under `OUTPUT_DIR` with `.gitsvg.jsonl`
  swapped for `.svg`. Continue-on-error; exit non-zero if any
  file failed.

Validation errors print to stderr (one per line in single-file
mode, aggregated at the end in bulk mode) and exit non-zero. No
output file is written for a failing input.
"""

import sys
from pathlib import Path

import click

from gitsvg.cli._bulk import process_input
from gitsvg.cli._pipeline import run_validate_pipeline
from gitsvg.errors import ValidationReport
from gitsvg.layout import compute_layout
from gitsvg.render import compute_minify_config, minify, render


@click.command(name="render")
@click.argument(
    "input_path",
    type=click.Path(exists=True, dir_okay=True, file_okay=True, path_type=Path),
)
@click.option(
    "-o",
    "--output",
    "output_path",
    required=True,
    type=click.Path(dir_okay=True, file_okay=True, path_type=Path),
    help="Path to write the SVG to (or output directory when INPUT is a directory).",
)
@click.option(
    "--small",
    "minify_level",
    is_flag=False,
    flag_value=2,
    default=0,
    type=click.IntRange(0, 3),
    help=(
        "Minification level (0-3): 0 = pristine (default), 1 = lossless basics, "
        "2 = + structural compression (the default when --small is given with no value), "
        "3 = + font-fallback trim and tighter rounding."
    ),
)
def render_command(input_path: Path, output_path: Path, minify_level: int) -> None:
    """Render a `.gitsvg.jsonl` input file (or directory tree) to SVG.

    With a single file at INPUT and a file path at `-o`, renders
    one SVG. With a directory at INPUT and a directory at `-o`,
    recursively walks INPUT for `*.gitsvg.jsonl` files and writes
    mirrored `.svg` outputs under OUTPUT, preserving subdirectory
    structure.

    Runs the same validation pipeline as `gitsvg validate` per
    input. Exits non-zero (writing nothing for that input) on any
    validation error.
    """
    exit_code = process_input(
        input_path,
        output_path,
        output_ext=".svg",
        process_one=lambda inp, out: _render_one(inp, out, minify_level),
    )
    sys.exit(exit_code)


def _render_one(input_path: Path, output_path: Path, minify_level: int) -> ValidationReport:
    """Validate one input and write its SVG when clean.

    Args:
        input_path: A `.gitsvg.jsonl` input file.
        output_path: Where to write the resulting SVG.
        minify_level: Minification level passed through from
            the `--small` flag (0 = pristine).

    Returns:
        The validation report. When clean, the SVG has been
        written to `output_path`; when dirty, no file is created
        and the caller is responsible for surfacing the errors.
    """
    state, report, theme = run_validate_pipeline(input_path)
    if not report.is_clean():
        return report

    layout = compute_layout(state)
    _, renderer_settings = theme.split()
    drawing = render(layout, renderer_settings)
    config = compute_minify_config(minify_level)
    if config.level == 0:
        drawing.save_svg(str(output_path))
    else:
        svg = drawing.as_svg(header="", skip_css=True, skip_js=True)
        output_path.write_text(minify(svg, config, renderer_settings))
    return report
