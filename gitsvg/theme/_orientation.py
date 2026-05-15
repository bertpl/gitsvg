"""Orientation literals + the input-alias normalisation table.

Defines the canonical four-valued orientation `Literal` type used by
`Theme.orientation`, and the alias-normalisation function used by the
`theme:` op's `orientation` field to accept a generous set of input
forms (case-insensitive short codes including Mermaid's `TD` and CSS
`ltr` / `rtl`, long forms with `-` or `_` separator, vernacular
`top_down` / `bottom_up`).
"""

from typing import Literal

OrientationLiteral = Literal["bt", "tb", "lr", "rl"]
"""The canonical four-valued orientation type used internally."""

# Two-step normalisation: input is first lowercased and `-` replaced by
# `_`, then looked up in this table. Every accepted alias (Mermaid `TD`,
# CSS `ltr` / `rtl`, the four explicit `<dir>_to_<dir>` long forms, and
# the two vernacular `top_down` / `bottom_up`) maps to its canonical
# short code; canonical codes also map to themselves so a single lookup
# covers every accepted input. CamelCase (`bottomToTop`), space-
# separated (`"bottom to top"`), and malformed-with-extra-underscores
# (`bo_ttom_t_o_top`) are deliberately rejected — strict table lookup
# is what enforces this.
_ALIAS_TABLE: dict[str, OrientationLiteral] = {
    "bt": "bt",
    "tb": "tb",
    "lr": "lr",
    "rl": "rl",
    "td": "tb",
    "ltr": "lr",
    "rtl": "rl",
    "bottom_to_top": "bt",
    "top_to_bottom": "tb",
    "left_to_right": "lr",
    "right_to_left": "rl",
    "bottom_up": "bt",
    "top_down": "tb",
}


def normalize_orientation(value: object) -> object:
    """Normalise an input orientation string to its canonical short code.

    Two-step normalisation:

    1. Pre-normalise: lowercase + replace `-` with `_`.
    2. Exact lookup in the alias table; raises if not found.

    Non-string inputs pass through unchanged (Pydantic raises later
    when the value doesn't match the declared `OrientationLiteral`
    type).

    Args:
        value: User-supplied orientation. Strings get normalised;
            anything else passes through.

    Returns:
        The canonical short code (`"bt"`, `"tb"`, `"lr"`, or `"rl"`)
        when the input is a known string; the original value
        otherwise.

    Raises:
        ValueError: When a string input does not normalise to any
            canonical value. The message lists every accepted form.
    """
    if not isinstance(value, str):
        return value
    normalised = value.lower().replace("-", "_")
    if normalised not in _ALIAS_TABLE:
        accepted = ", ".join(sorted(_ALIAS_TABLE))
        raise ValueError(
            f"unknown orientation {value!r}; accepted (case-insensitive, `-` and `_` interchangeable): {accepted}"
        )
    return _ALIAS_TABLE[normalised]
