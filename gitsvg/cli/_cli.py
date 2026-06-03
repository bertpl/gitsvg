"""Top-level Click group for the `gitsvg` CLI."""

import click

from gitsvg import __version__

from ._errors import errors_command
from ._layout import layout_command
from ._render import render_command
from ._schema import schema_command
from ._state import state_command
from ._theme import theme_command
from ._validate import validate_command


@click.group()
@click.version_option(__version__, prog_name="gitsvg")
def cli() -> None:
    """gitsvg - render git tree visualizations as SVG from JSONL input."""


cli.add_command(schema_command)
cli.add_command(theme_command)
cli.add_command(errors_command)
cli.add_command(validate_command)
cli.add_command(render_command)
cli.add_command(state_command)
cli.add_command(layout_command)
