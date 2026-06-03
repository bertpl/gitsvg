"""Size reductions applied to rendered SVG output via the `--small` level dial.

These are string-level (and one call-site-level) transforms over the SVG
already emitted by drawsvg. The CLI's `--small` flag selects a minification
level (0-3); each level enables a different subset of transforms. Default
rendering (`--small` absent, or `--small=0`) is byte-identical to drawsvg's
default output.

Level contract:

- L0: pristine drawsvg output.
- L1: lossless basics — structural drops, whitespace strip, font-family
  hoist, 6dp rounding. Visually lossless when rendered full screen on
  current screen resolutions.
- L2: L1 + hex shortening + 4dp rounding. Same visually-lossless
  guarantee under the same viewing conditions.
- L3: L2 + font-fallback trim + 2dp rounding. Accepts platform-dependent
  visual deviation (font-fallback trim changes rendering on viewers
  without Inter installed).
"""

from ._steps import (
    drop_default_attribute_values,
    drop_empty_defs_and_unused_xlink,
    extract_css_classes,
    hoist_font_family_to_root,
    round_numbers,
    shorten_hex_colors,
    strip_inter_element_whitespace,
    trim_font_family_fallback,
)
from .config import MinifyConfig, compute_minify_config
from .level import MinifyLevel
from .runner import minify

__all__ = [
    "MinifyConfig",
    "MinifyLevel",
    "compute_minify_config",
    "drop_default_attribute_values",
    "drop_empty_defs_and_unused_xlink",
    "extract_css_classes",
    "hoist_font_family_to_root",
    "minify",
    "round_numbers",
    "shorten_hex_colors",
    "strip_inter_element_whitespace",
    "trim_font_family_fallback",
]
