"""Render — turn a layout + resolved theme into an SVG drawing.

Public surface:

- `render(layout, theme)` — render one diagram and return the
  `drawsvg.Drawing` object. Callers persist it with `.save_svg(path)`
  or convert with `.as_svg()`.
- `minify(svg, config, theme)` — string-level size reductions for
  `--small` rendered output. Combine with `compute_minify_config(level)`
  to drive from a `MinifyLevel`.
"""

from gitsvg.render._minify import MinifyConfig, MinifyLevel, compute_minify_config, minify
from gitsvg.render._renderer import render

__all__ = ["MinifyConfig", "MinifyLevel", "compute_minify_config", "minify", "render"]
