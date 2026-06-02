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
`clear_overrides`).

The `theme:` op apply handler (`gitsvg.theme._apply.apply_theme_op`)
imports `State` for the shared apply-handler signature and is
therefore imported via its leaf path from the state engine to avoid
a package-load cycle. Same pattern as `file_format/ops/framework/`.
"""

from gitsvg.theme._box_anchor import BoxAnchor, validate_box_anchor
from gitsvg.theme._branch_line_style import BranchLineStyle
from gitsvg.theme._builder import ThemeBuilder
from gitsvg.theme._color import is_color_visible
from gitsvg.theme._commit_label_layout import CommitLabelLayout
from gitsvg.theme._commit_row_mode import CommitRowMode
from gitsvg.theme._default_theme import DefaultTheme
from gitsvg.theme._merge_commit_style import MergeCommitStyle
from gitsvg.theme._orientation import Orientation, normalize_orientation
from gitsvg.theme._theme import Theme, _resolve_int_or_float

DEFAULT_THEME = DefaultTheme.build({})
"""The resolved default theme — `DefaultTheme.build({})` with no user overrides.

Cached as a module-level singleton for tests and callers that need a
fully-resolved baseline without going through the apply pipeline.
"""

__all__ = [
    "DEFAULT_THEME",
    "BoxAnchor",
    "BranchLineStyle",
    "CommitLabelLayout",
    "CommitRowMode",
    "DefaultTheme",
    "MergeCommitStyle",
    "Orientation",
    "Theme",
    "ThemeBuilder",
    "_resolve_int_or_float",
    "is_color_visible",
    "normalize_orientation",
    "validate_box_anchor",
]
