"""The `gitsvg theme` CLI command.

Three forms, mirroring `schema` / `errors` for agent-friendly progressive
disclosure of the built-in named themes:

- `gitsvg theme`              - index of registered themes + one-line descriptions
- `gitsvg theme <name>`       - resolved field values for one named theme
- `gitsvg theme --list-names` - bare list of theme names, one per line
"""

import json
import sys

import click

from gitsvg.theme._named_themes import NAMED_THEMES


# ==================================================================================================
#  Click command
# ==================================================================================================
@click.command(name="theme")
@click.argument("name", required=False)
@click.option("--list-names", "list_names", is_flag=True, help="Print bare theme names, one per line.")
def theme_command(name: str | None, list_names: bool) -> None:
    """Inspect the built-in named themes.

    With no arguments, prints an index of all registered themes with
    one-line descriptions. Pass a theme name (e.g. `theme dark`) to
    print that theme's resolved field values at the default
    orientation. Pass `--list-names` to print only the bare list of
    theme names.
    """
    if list_names:
        for theme_name in sorted(NAMED_THEMES):
            click.echo(theme_name)
        return

    if name is None:
        click.echo(_render_index())
        return

    if name not in NAMED_THEMES:
        known = ", ".join(sorted(NAMED_THEMES))
        click.echo(f"Unknown theme: {name!r}", err=True)
        click.echo(f"Known themes: {known}", err=True)
        sys.exit(2)

    resolved = NAMED_THEMES[name].build({})
    click.echo(json.dumps(resolved.model_dump(mode="json"), indent=2))


# ==================================================================================================
#  Index rendering
# ==================================================================================================
def _render_index() -> str:
    """Render the prose-form theme index for `gitsvg theme` with no arguments.

    Returns:
        A multi-line string: each registered theme name padded to a
        column, then its one-line description. Suitable for printing
        directly to stdout.
    """
    names = sorted(NAMED_THEMES)
    lines: list[str] = ["gitsvg themes - built-in named themes", ""]

    width = max(len(name) for name in names)
    for name in names:
        lines.append(f"  {name.ljust(width)}  {_theme_one_liner(name)}")

    lines += [
        "",
        "Run `gitsvg theme <name>` for a theme's resolved field values.",
        "Run `gitsvg theme --list-names` for a bare theme-name list.",
    ]
    return "\n".join(lines)


def _theme_one_liner(name: str) -> str:
    """Return theme `name`'s one-line description: the first line of its class docstring.

    Markdown backticks are stripped for clean plain-text display.
    """
    doc = (NAMED_THEMES[name].__doc__ or "").strip()
    first_line = doc.splitlines()[0] if doc else ""
    return first_line.replace("`", "").strip()
