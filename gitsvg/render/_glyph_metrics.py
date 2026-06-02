"""Font-chain-aware text-width computation.

Parses ``theme.label_font_family`` into a CSS-style fallback chain,
resolves each entry to a bundled glyph-width LUT under
``_glyph_widths/``, and returns the per-character maximum width
across every resolved LUT. SVG geometry sized from this width is
safe whichever font in the chain a viewer actually picks.

When no entry in the chain resolves to a known LUT (e.g. only
cursive / fantasy fonts plus an unrecognized specific name), the
implementation falls back to a coarse per-character factor so the
function never raises and downstream geometry stays well-defined.
"""

import logging
from dataclasses import dataclass
from typing import Final

from gitsvg.render._glyph_widths import (
    inter_bold,
    inter_regular,
    monospace_bold,
    monospace_regular,
    sans_serif_bold,
    sans_serif_regular,
)

# Coarse heuristic factors used only when the empty-resolved-chain
# safety net trips. Calibrated for Inter at typical font sizes — the
# same numbers the entire pipeline used before the LUT-driven
# approach landed.
_HEURISTIC_FACTOR_NORMAL: Final = 0.58
_HEURISTIC_FACTOR_BOLD: Final = 0.64

_logger = logging.getLogger(__name__)
_logged_unresolved: set[str] = set()


# ==================================================================================================
#  GlyphWidths — single per-font lookup with widest-glyph fallback
# ==================================================================================================
@dataclass(frozen=True)
class GlyphWidths:
    """Per-character em-width lookup with a widest-glyph fallback.

    Wraps a raw LUT dict alongside the widest glyph in the same LUT,
    used as the per-character fallback for any character missing from
    the table. The fallback keeps every measurement conservative —
    we never under-estimate.
    """

    table: dict[str, float]
    fallback: float

    # --------------------------------------------------------------------------
    #  Construction
    # --------------------------------------------------------------------------
    @classmethod
    def from_widths(cls, widths: dict[str, float]) -> "GlyphWidths":
        """Build a `GlyphWidths` from a raw LUT, deriving the fallback."""
        return cls(table=widths, fallback=max(widths.values()))

    # --------------------------------------------------------------------------
    #  Lookup
    # --------------------------------------------------------------------------
    def width_of(self, char: str) -> float:
        """Return the em-width of `char`, or the LUT's widest glyph if absent."""
        return self.table.get(char, self.fallback)


# ==================================================================================================
#  Registry — chain-entry name → `GlyphWidths`
# ==================================================================================================
_REGISTRY_REGULAR: Final[dict[str, GlyphWidths]] = {
    "inter": GlyphWidths.from_widths(inter_regular.WIDTHS),
    "sans-serif": GlyphWidths.from_widths(sans_serif_regular.WIDTHS),
    "monospace": GlyphWidths.from_widths(monospace_regular.WIDTHS),
}

_REGISTRY_BOLD: Final[dict[str, GlyphWidths]] = {
    "inter": GlyphWidths.from_widths(inter_bold.WIDTHS),
    "sans-serif": GlyphWidths.from_widths(sans_serif_bold.WIDTHS),
    "monospace": GlyphWidths.from_widths(monospace_bold.WIDTHS),
}


# ==================================================================================================
#  Chain parsing + resolution
# ==================================================================================================
def parse_chain(font_family: str) -> list[str]:
    """Parse a CSS-style font-family string into normalized entries.

    Splits on commas, strips whitespace and surrounding single or
    double quotes from each entry, and lowercases. Empty entries
    (from stray commas) are dropped.

    Args:
        font_family: Raw CSS font-family value, e.g.
            ``"'Inter', 'Helvetica Neue', sans-serif"``.

    Returns:
        Normalized entries in their original order, e.g.
        ``["inter", "helvetica neue", "sans-serif"]``.
    """
    entries: list[str] = []
    for raw in font_family.split(","):
        cleaned = raw.strip().strip("'\"").strip().lower()
        if cleaned:
            entries.append(cleaned)
    return entries


def resolve_chain(chain: list[str], *, bold: bool) -> list[GlyphWidths]:
    """Resolve normalized chain entries to bundled `GlyphWidths`.

    Args:
        chain: Output of `parse_chain`.
        bold: Whether to use bold-weight metrics.

    Returns:
        The resolved `GlyphWidths` instances in chain order. Entries
        without a matching bundled LUT (unknown specific font names,
        unrecognized generic keywords like ``cursive`` / ``fantasy``)
        are skipped.
    """
    registry = _REGISTRY_BOLD if bold else _REGISTRY_REGULAR
    return [registry[entry] for entry in chain if entry in registry]


# ==================================================================================================
#  Public API
# ==================================================================================================
def text_width(
    text: str,
    font_family: str,
    font_size: float,
    *,
    bold: bool = False,
) -> float:
    """Compute pixel width safe across the declared font fallback chain.

    For each character in `text`, takes the maximum em-width across
    every LUT resolved from the chain (per-LUT widest-glyph used for
    chars missing from a LUT). Sum, multiply by `font_size`. If no
    entry in the chain resolves to a known LUT, falls back to a
    coarse per-character factor.

    Args:
        text: The text to measure.
        font_family: CSS-style comma-separated font-family chain.
        font_size: Pixel font size.
        bold: Whether to use bold-weight metrics.

    Returns:
        Pixel width.
    """
    chain = parse_chain(font_family)
    luts = resolve_chain(chain, bold=bold)
    if not luts:
        if font_family not in _logged_unresolved:
            _logged_unresolved.add(font_family)
            _logger.debug(
                "no font in chain %r resolves to a bundled glyph-width LUT; using heuristic",
                font_family,
            )
        factor = _HEURISTIC_FACTOR_BOLD if bold else _HEURISTIC_FACTOR_NORMAL
        return len(text) * font_size * factor

    em_width = sum(max(lut.width_of(ch) for lut in luts) for ch in text)
    return em_width * font_size
