"""Round-1 size reductions applied to rendered SVG output under `--small`.

These are string-level (and one call-site-level) transforms over the SVG
already emitted by drawsvg. The CLI's `--small` flag toggles them on;
default rendering is byte-identical to non-`--small` output.

Round-2 size reductions (renderer rewrites: CSS classes, `<g>` grouping,
`<symbol>` + `<use>`) are deferred — they will live alongside or in
place of these passes when implemented.
"""

import re

from gitsvg.render._renderer_settings import RendererSettings

# ==================================================================================================
#  Individual passes
# ==================================================================================================
_NUMBER_RE = re.compile(r"-?\d+\.\d+")


def round_numbers(svg: str, decimals: int) -> str:
    """Round every decimal number in the SVG to `decimals` places.

    Targets attribute values like `x="105.32"`, `width="37.5199...96"`,
    and the floating-point coordinates inside `d="..."` path data.
    Integer-valued numbers and non-numeric content are left untouched.

    Args:
        svg: The full SVG markup as a string.
        decimals: Number of decimal places to keep. Use `0` to round
            to integer pixels; positive values keep that many decimals.

    Returns:
        A new SVG string with all decimals rounded.
    """

    def _replace(match: re.Match[str]) -> str:
        rounded = round(float(match.group(0)), decimals)
        if decimals <= 0:
            return str(int(rounded))
        formatted = f"{rounded:.{decimals}f}"
        # Trim trailing zeros / dangling dot — `12.10` -> `12.1`, `12.0` -> `12`.
        return formatted.rstrip("0").rstrip(".")

    return _NUMBER_RE.sub(_replace, svg)


def strip_inter_element_whitespace(svg: str) -> str:
    """Drop whitespace that sits between elements (`>` followed by whitespace then `<`).

    Whitespace inside element content (e.g. between `<text>` and its
    first child character) is preserved — the regex only matches
    whitespace bounded by `>` on the left and `<` on the right, which
    is structurally inter-element.

    Args:
        svg: The full SVG markup as a string.

    Returns:
        The SVG with all inter-element whitespace removed.
    """
    return re.sub(r">\s+<", "><", svg)


def drop_empty_defs_and_unused_xlink(svg: str) -> str:
    """Remove `<defs></defs>` when empty and `xmlns:xlink="..."` when unused.

    drawsvg always emits a `<defs>` block, even when it contains
    nothing; gitsvg never references the xlink namespace today, so
    its declaration on the root is dead weight.

    Args:
        svg: The full SVG markup as a string.

    Returns:
        The SVG with empty `<defs>` and unused `xmlns:xlink` declarations removed.
    """
    svg = re.sub(r"<defs>\s*</defs>", "", svg)
    if not re.search(r"xlink:[a-zA-Z]+=", svg):
        svg = re.sub(r'\s+xmlns:xlink="[^"]*"', "", svg)
    return svg


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


# Pairs of `(attribute, default_value)`. Attributes carrying the listed value
# are removed from any element under `--small`. Both `400` and `normal` are
# valid SVG defaults for `font-weight`; we drop either form.
_DEFAULT_ATTRIBUTE_VALUES: list[tuple[str, str]] = [
    ("font-weight", "400"),
    ("font-weight", "normal"),
]


def drop_default_attribute_values(svg: str) -> str:
    """Remove attribute values that match SVG defaults.

    Today this drops `font-weight="400"` (or `="normal"`), the only
    explicit-default attribute drawsvg emits in our output. The lookup
    grows as future renderer changes surface more candidates.

    Args:
        svg: The full SVG markup as a string.

    Returns:
        The SVG with default-valued attributes removed.
    """
    for attr, default_value in _DEFAULT_ATTRIBUTE_VALUES:
        pattern = rf'\s+{re.escape(attr)}="{re.escape(default_value)}"'
        svg = re.sub(pattern, "", svg)
    return svg


# ==================================================================================================
#  Entrypoint
# ==================================================================================================
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
