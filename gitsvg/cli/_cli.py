"""Top-level Click group for the `gitsvg` CLI."""

import click

from gitsvg import __version__
from gitsvg.cli._errors import errors_command
from gitsvg.cli._render import render_command
from gitsvg.cli._schema import schema_command
from gitsvg.cli._validate import validate_command


@click.group()
@click.version_option(__version__, prog_name="gitsvg")
def cli() -> None:
    """gitsvg - render git tree visualizations as SVG from JSONL input."""


cli.add_command(schema_command)
cli.add_command(errors_command)
cli.add_command(validate_command)
cli.add_command(render_command)
