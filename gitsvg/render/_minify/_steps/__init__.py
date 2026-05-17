"""Round-1 reduction passes — one module per pass."""

from gitsvg.render._minify._steps._default_attrs import drop_default_attribute_values
from gitsvg.render._minify._steps._defs import drop_empty_defs_and_unused_xlink
from gitsvg.render._minify._steps._font_family import (
    hoist_font_family_to_root,
    trim_font_family_fallback,
)
from gitsvg.render._minify._steps._round_numbers import round_numbers
from gitsvg.render._minify._steps._whitespace import strip_inter_element_whitespace

__all__ = [
    "drop_default_attribute_values",
    "drop_empty_defs_and_unused_xlink",
    "hoist_font_family_to_root",
    "round_numbers",
    "strip_inter_element_whitespace",
    "trim_font_family_fallback",
]
