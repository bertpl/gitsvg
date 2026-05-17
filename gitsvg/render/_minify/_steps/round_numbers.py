"""Round every decimal number inside SVG attribute values to a fixed precision."""

import re

# Numbers are only rounded within quoted attribute values. Element text
# content between `>` and `<` is left untouched — a label like
# `<text>release v1.0</text>` must not be rewritten to `release v1`.
_QUOTED_VALUE_RE = re.compile(r'"[^"]*"')
_NUMBER_RE = re.compile(r"-?\d+\.\d+")


def round_numbers(svg: str, decimals: int) -> str:
    """Round every decimal number in attribute values to `decimals` places.

    Targets attribute values like `x="105.32"`, `width="37.5199...96"`,
    and the floating-point coordinates inside `d="..."` path data.
    Integer-valued numbers, non-numeric content, and any text inside
    element bodies (between `>` and `<`) are left untouched.

    Args:
        svg: The full SVG markup as a string.
        decimals: Number of decimal places to keep. Use `0` to round
            to integer pixels; positive values keep that many decimals.

    Returns:
        A new SVG string with all attribute-value decimals rounded.
    """

    def _round_match(match: re.Match[str]) -> str:
        """Round one matched decimal number to `decimals` places and trim trailing zeros."""
        rounded = round(float(match.group(0)), decimals)
        if decimals <= 0:
            return str(int(rounded))
        formatted = f"{rounded:.{decimals}f}"
        # Trim trailing zeros / dangling dot — `12.10` -> `12.1`, `12.0` -> `12`.
        return formatted.rstrip("0").rstrip(".")

    def _round_inside_quoted_value(match: re.Match[str]) -> str:
        """Apply `_round_match` to every decimal number inside one quoted attribute value."""
        return _NUMBER_RE.sub(_round_match, match.group(0))

    return _QUOTED_VALUE_RE.sub(_round_inside_quoted_value, svg)
