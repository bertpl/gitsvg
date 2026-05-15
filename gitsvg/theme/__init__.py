"""Theme — every presentational constant the renderer reads.

A `Theme` accumulates as the input file's `theme:` ops apply and as
`branch:` ops carry colour overrides. The pipeline's apply stage
produces a fully-resolved `Theme` alongside `State`; the renderer
consumes it directly. See `docs/architecture.md` Pipeline section
for the dual-output rule.

Public surface:

- `Theme` — the dataclass.
- `DEFAULT_THEME` — frozen-by-convention reference; use
  `dataclasses.replace(DEFAULT_THEME, ...)` rather than mutating.

The `theme:` op apply handler (`gitsvg.theme._apply.apply_theme_op`)
imports `State` for the shared apply-handler signature and is
therefore imported via its leaf path from the state engine to avoid
a package-load cycle. Same pattern as `file_format/ops/framework/`.
"""

from gitsvg.theme._resolve import resolve_defaults
from gitsvg.theme._theme import DEFAULT_THEME, Theme, _resolve_int_or_float

__all__ = [
    "DEFAULT_THEME",
    "Theme",
    "_resolve_int_or_float",
    "resolve_defaults",
]
