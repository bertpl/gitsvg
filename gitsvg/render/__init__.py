"""Render — turn validated state + layout into an SVG drawing.

Public surface:

- `render(state, layout)` — render one diagram and return the
  `drawsvg.Drawing` object. Callers persist it with `.save_svg(path)`
  or convert with `.as_svg()`.
- `build_theme(state)` — resolve `state.theme` plus per-branch
  colour overrides into the `Theme` the renderer consumes.
- `minify(svg, ...)` — string-level size reductions for `--small`
  rendered output.
"""

from gitsvg.render._minify import minify
from gitsvg.render._renderer import render
from gitsvg.render._theme import build_theme

__all__ = ["build_theme", "minify", "render"]
