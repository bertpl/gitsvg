"""Concrete named-theme subclasses of `DefaultTheme`.

Each module under this package contains one concrete theme — a
subclass of `gitsvg.theme.DefaultTheme` that overrides the
`_resolve_<field>` classmethods it wants to vary. Themes register
themselves into the `NAMED_THEMES` dict in `gitsvg.theme._apply` so a
`theme:` op selecting `"name": "..."` resolves to the right subclass.

Themes share `DefaultTheme.build()` — the inherited factory walks
every field and dispatches to whichever `_resolve_*` the subclass
exposes, falling back to `DefaultTheme`'s for anything not overridden.
"""

from gitsvg.theme.themes._compact import CompactTheme
from gitsvg.theme.themes._dark import DarkTheme
from gitsvg.theme.themes._gui import GuiTheme
from gitsvg.theme.themes._muted import MutedTheme

__all__ = ["CompactTheme", "DarkTheme", "GuiTheme", "MutedTheme"]
