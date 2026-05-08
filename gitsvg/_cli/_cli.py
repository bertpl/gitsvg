"""Top-level Click group for the `gitsvg` CLI."""

import click

from gitsvg import __version__
from gitsvg._cli._schema import schema_command


@click.group()
@click.version_option(__version__, prog_name="gitsvg")
def cli() -> None:
    """gitsvg - render git tree visualizations as SVG from JSONL input."""


cli.add_command(schema_command)
