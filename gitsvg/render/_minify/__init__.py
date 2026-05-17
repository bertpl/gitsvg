"""Round-1 size reductions applied to rendered SVG output under `--small`.

These are string-level (and one call-site-level) transforms over the SVG
already emitted by drawsvg. The CLI's `--small` flag toggles them on;
default rendering is byte-identical to non-`--small` output.

Round-2 size reductions (renderer rewrites: CSS classes, `<g>` grouping,
`<symbol>` + `<use>`) are deferred — they will live alongside or in
place of these passes when implemented.
"""

from gitsvg.render._minify._runner import minify
from gitsvg.render._minify._steps import (
    drop_default_attribute_values,
    drop_empty_defs_and_unused_xlink,
    hoist_font_family_to_root,
    round_numbers,
    strip_inter_element_whitespace,
    trim_font_family_fallback,
)

__all__ = [
    "drop_default_attribute_values",
    "drop_empty_defs_and_unused_xlink",
    "hoist_font_family_to_root",
    "minify",
    "round_numbers",
    "strip_inter_element_whitespace",
    "trim_font_family_fallback",
]
