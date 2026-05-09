"""Render — turn validated state + layout into an SVG drawing.

Public surface:

- `render(state, layout)` — render one diagram and return the
  `drawsvg.Drawing` object. Callers persist it with `.save_svg(path)`
  or convert with `.as_svg()`.
"""

from gitsvg.render._renderer import render

__all__ = ["render"]
