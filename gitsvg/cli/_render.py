"""The `gitsvg render` CLI command.

Runs the full validate pipeline on the input file, then computes a
layout and renders the result to SVG.

Output:

- A single SVG file at the path given by `-o`.
- Validation errors print to stderr (one per line) and exit non-zero.
"""

import sys
from pathlib import Path

import click

from gitsvg.imports import resolve_imports
from gitsvg.layout import compute_layout
from gitsvg.parse import parse_jsonl_file
from gitsvg.render import render
from gitsvg.render._minify import minify
from gitsvg.render._theme import build_theme
from gitsvg.state import apply_ops, check_end_of_file


@click.command(name="render")
@click.argument("input_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option(
    "-o",
    "--output",
    "output_path",
    required=True,
    type=click.Path(dir_okay=False, path_type=Path),
    help="Path to write the SVG output to.",
)
@click.option(
    "--small",
    is_flag=True,
    default=False,
    help="Produce a more compact SVG (some loss of numeric precision).",
)
def render_command(input_path: Path, output_path: Path, small: bool) -> None:
    """Render a `.gitsvg.jsonl` input file to an SVG file.

    Runs the same validation pipeline as `gitsvg validate`, then
    computes a layout and renders the result. Exits non-zero (and
    writes nothing) if the input has any validation errors.
    """
    parsed_ops, report = parse_jsonl_file(input_path)
    expanded_ops = resolve_imports(parsed_ops, file=input_path, report=report)
    state = apply_ops(expanded_ops, report)
    check_end_of_file(state, report)

    if not report.is_clean():
        for err in report.errors:
            click.echo(err.format(), err=True)
        sys.exit(1)

    theme = build_theme(state)
    layout = compute_layout(state)
    drawing = render(layout, theme)
    if small:
        svg = drawing.as_svg(header="", skip_css=True, skip_js=True)
        output_path.write_text(minify(svg, small=True, theme=theme))
    else:
        drawing.save_svg(str(output_path))
