"""Render — turn a layout + resolved theme into an SVG drawing.

Public surface:

- `render(layout, theme)` — render one diagram and return the
  `drawsvg.Drawing` object. Callers persist it with `.save_svg(path)`
  or convert with `.as_svg()`.
- `minify(svg, ...)` — string-level size reductions for `--small`
  rendered output.
"""

from gitsvg.render._minify import minify
from gitsvg.render._renderer import render

__all__ = ["minify", "render"]
