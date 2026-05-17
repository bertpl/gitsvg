"""Round every decimal number in the SVG to a fixed number of decimal places."""

import re

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
