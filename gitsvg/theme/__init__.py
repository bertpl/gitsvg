"""Theme — every presentational constant the renderer reads.

A `Theme` is a Pydantic base class with all fields `Optional[T] = None`.
Concrete subclasses (today `DefaultTheme`) implement per-field
`_resolve_<field>` classmethods and a `build(user_set)` factory that
produces a fully-populated instance from the dict of explicit
overrides the apply pass accumulated.

`ThemeBuilder` is the transient accumulator threaded through the apply
pass: it tracks the chosen `theme_cls`, the `user_set` dict, and
state-derived per-branch color overrides. The state engine calls
`builder.build()` once at end-of-apply to produce the resolved `Theme`.
A `theme:` op carrying `name` reassigns `theme_cls` (via
`set_theme_cls`) and, unless the op also carries
`keep_prior_overrides: true`, wipes both accumulator dicts (via
`clear_overrides`). The op's apply handler lives with its peers under
`gitsvg.state._apply`; the registry of selectable named themes is
`gitsvg.theme._named_themes.NAMED_THEMES`.
"""

from ._builder import ThemeBuilder
from ._default_theme import DefaultTheme
from ._theme import Theme

DEFAULT_THEME = DefaultTheme.build({})
"""The resolved default theme — `DefaultTheme.build({})` with no user overrides.

Cached as a module-level singleton for tests and callers that need a
fully-resolved baseline without going through the apply pipeline.
"""

__all__ = [
    "DEFAULT_THEME",
    "DefaultTheme",
    "Theme",
    "ThemeBuilder",
]
