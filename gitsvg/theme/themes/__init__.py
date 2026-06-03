"""Concrete named-theme subclasses of `DefaultTheme`.

Each module under this package contains one concrete theme — a
subclass of `gitsvg.theme.DefaultTheme` that overrides the
`_resolve_<field>` classmethods it wants to vary. Each is registered in
the `NAMED_THEMES` dict in `gitsvg.theme._named_themes` so a `theme:` op
selecting `"name": "..."` resolves to the right subclass.

Themes share `DefaultTheme.build()` — the inherited factory walks
every field and dispatches to whichever `_resolve_*` the subclass
exposes, falling back to `DefaultTheme`'s for anything not overridden.
"""

from ._compact import CompactTheme
from ._dark import DarkTheme
from ._gui import GuiTheme
from ._muted import MutedTheme

__all__ = ["CompactTheme", "DarkTheme", "GuiTheme", "MutedTheme"]
