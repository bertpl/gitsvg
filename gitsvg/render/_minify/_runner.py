"""The `minify(...)` entry point that drives the round-1 pass sequence."""

from gitsvg.render._minify._steps import (
    drop_default_attribute_values,
    drop_empty_defs_and_unused_xlink,
    hoist_font_family_to_root,
    round_numbers,
    strip_inter_element_whitespace,
    trim_font_family_fallback,
)
from gitsvg.render._renderer_settings import RendererSettings


def minify(svg: str, small: bool, theme: RendererSettings) -> str:
    """Apply the round-1 reductions in sequence when `small` is True.

    When `small` is False, returns `svg` unchanged. When True, runs
    every registered pass in order; each pass takes a string and
    returns a string. New round-1 passes are registered here as they
    land.

    Args:
        svg: The full SVG markup as a string.
        small: When True, apply the round-1 reductions.
        theme: Resolved theme — supplies the font-family values the
            trim pass needs.

    Returns:
        The (potentially) reduced SVG markup.
    """
    if not small:
        return svg
    svg = round_numbers(svg, decimals=3)
    svg = drop_default_attribute_values(svg)
    svg = trim_font_family_fallback(svg, theme)
    svg = hoist_font_family_to_root(svg)
    svg = drop_empty_defs_and_unused_xlink(svg)
    svg = strip_inter_element_whitespace(svg)
    return svg
