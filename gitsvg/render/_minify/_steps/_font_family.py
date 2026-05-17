"""Font-family passes: trim the rendered fallback chain and hoist a uniform value onto the root."""

import re

from gitsvg.render._renderer_settings import RendererSettings


def trim_font_family_fallback(svg: str, theme: RendererSettings) -> str:
    """Replace the rendered `font-family` chain with the short form.

    The rendered output uses `theme.label_font_family` on every text
    element. Under `--small`, drop the intermediate fallbacks: replace
    every occurrence with `theme.label_font_family_small`, which relies
    on the host's generic-`sans-serif` resolution instead. On every
    modern OS that resolves to a perfectly acceptable default.
    """
    return svg.replace(theme.label_font_family, theme.label_font_family_small)


def hoist_font_family_to_root(svg: str) -> str:
    """Hoist a uniform `font-family` from `<text>` elements onto the `<svg>` root.

    When every `<text>` element carries the same `font-family` value,
    SVG's attribute inheritance lets us specify it once on the root
    instead of repeating it on each text node. When values differ,
    or there are no text elements, returns the input unchanged.

    Args:
        svg: The full SVG markup as a string.

    Returns:
        The SVG with `font-family` consolidated onto the root when uniform.
    """
    text_ff_values = re.findall(r'<text\b[^>]*?\bfont-family="([^"]*)"', svg)
    if not text_ff_values or len(set(text_ff_values)) > 1:
        return svg
    common_value = text_ff_values[0]
    # Drop the attribute (and its leading whitespace) from each <text>.
    svg = re.sub(
        r'(<text\b[^>]*?)\s+font-family="[^"]*"',
        r"\1",
        svg,
    )
    # Add it to the <svg ...> opening tag, just before the closing `>`.
    svg = re.sub(
        r"(<svg\b[^>]*?)>",
        rf'\1 font-family="{common_value}">',
        svg,
        count=1,
    )
    return svg
