"""RendererSettings — the renderer pipeline stage's slice of `Theme`.

`Theme.split()` produces a `RendererSettings` instance carrying the
renderer-side fields of the resolved theme. Today every theme field
is renderer-relevant (no layout-affecting field exists), so
`RendererSettings` structurally mirrors `Theme`. The dedicated class
marks the pipeline boundary — every module under `gitsvg/render/`
imports `RendererSettings` (not `Theme`), and the architecture meta-
test enforces this so a future regression cannot silently re-couple
the renderer to `Theme`.

Implementation note: `RendererSettings` subclasses `Theme` so the
field declarations, validators, and resolved-pixel property
accessors live in one place. Conceptually the relationship is "the
renderer's slice of the resolved theme"; the inheritance is a
mechanical convenience that keeps the field block DRY. When future
fields land in `LayoutSettings`, `RendererSettings` narrows by
redeclaring the relevant fields as excluded (or, more likely, by
moving to a sibling schema).
"""

from gitsvg.theme._theme import Theme


class RendererSettings(Theme):
    """The renderer pipeline stage's slice of the resolved theme.

    Structurally identical to `Theme` today — every theme field is
    renderer-relevant. The class identity (distinct from `Theme`) is
    what the pipeline-split meta-test enforces; downstream renderer
    code imports `RendererSettings` so the boundary stays type-visible.
    """
