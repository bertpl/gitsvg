"""Minification reduction passes — one module per pass."""

from .css_classes import extract_css_classes
from .default_attrs import drop_default_attribute_values
from .defs import drop_empty_defs_and_unused_xlink
from .font_family import (
    hoist_font_family_to_root,
    trim_font_family_fallback,
)
from .hex import shorten_hex_colors
from .round_numbers import round_numbers
from .whitespace import strip_inter_element_whitespace

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
