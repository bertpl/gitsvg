"""Minification reduction passes — one module per pass."""

from gitsvg.render._minify._steps.css_classes import extract_css_classes
from gitsvg.render._minify._steps.default_attrs import drop_default_attribute_values
from gitsvg.render._minify._steps.defs import drop_empty_defs_and_unused_xlink
from gitsvg.render._minify._steps.font_family import (
    hoist_font_family_to_root,
    trim_font_family_fallback,
)
from gitsvg.render._minify._steps.hex import shorten_hex_colors
from gitsvg.render._minify._steps.round_numbers import round_numbers
from gitsvg.render._minify._steps.whitespace import strip_inter_element_whitespace

__all__ = [
    "drop_default_attribute_values",
    "drop_empty_defs_and_unused_xlink",
    "extract_css_classes",
    "hoist_font_family_to_root",
    "round_numbers",
    "shorten_hex_colors",
    "strip_inter_element_whitespace",
    "trim_font_family_fallback",
]
