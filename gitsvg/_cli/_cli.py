import click

from gitsvg import __version__


@click.group()
@click.version_option(__version__, prog_name="gitsvg")
def cli() -> None:
    """gitsvg — render git tree visualizations as SVG from JSON/YAML/Markdown input."""


@cli.command()
def render() -> None:
    """Render an input file to SVG. (Not implemented yet.)"""
    click.echo(f"gitsvg {__version__} — not implemented yet. Coming soon.")
