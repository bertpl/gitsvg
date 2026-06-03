"""Registry of the built-in named themes selectable via a `theme` op's `name`.

Maps each public name to its `Theme` subclass: `default` to the base
`DefaultTheme` resolver, the rest to the concrete subclasses under
`gitsvg.theme.themes`. The `theme:` op apply handler resolves a
`name`-bearing op through this dict (unknown name → E216) and swaps the
`ThemeBuilder.theme_cls` to the match; the `gitsvg theme` CLI command
reads it to list and describe the themes.
"""

from ._default_theme import DefaultTheme
from ._theme import Theme
from .themes import CompactTheme, DarkTheme, GuiTheme, MutedTheme

# New named themes land here; no other wiring is needed — both the apply
# handler and the `gitsvg theme` command read the registry dynamically.
NAMED_THEMES: dict[str, type[Theme]] = {
    "default": DefaultTheme,
    "muted": MutedTheme,
    "dark": DarkTheme,
    "compact": CompactTheme,
    "gui": GuiTheme,
}
