"""Orientation enum + the input-alias normalization table.

Defines the canonical four-valued `Orientation` `StrEnum` used by
`Theme.orientation`, and the alias-normalization function used by the
`theme:` op's `orientation` field to accept a generous set of input
forms (case-insensitive short codes including Mermaid's `TD` and CSS
`ltr` / `rtl`, long forms with `-` or `_` separator, vernacular
`top_down` / `bottom_up`).
"""

from enum import StrEnum


class Orientation(StrEnum):
    """Canonical four-valued diagram orientation.

    Members carry the canonical short-code string values (`"bt"`,
    `"tb"`, `"lr"`, `"rl"`) so the enum interoperates transparently
    with code that still compares against raw strings and with
    Pydantic / JSON serialization (which reads off the string value).
    """

    BT = "bt"
    TB = "tb"
    LR = "lr"
    RL = "rl"

    @property
    def is_vertical(self) -> bool:
        """Return True for the vertical orientations (`bt`, `tb`)."""
        return self in (Orientation.BT, Orientation.TB)


# Two-step normalization: input is first lowercased and `-` replaced by
# `_`, then looked up in this table. Every accepted alias (Mermaid `TD`,
# CSS `ltr` / `rtl`, the four explicit `<dir>_to_<dir>` long forms, and
# the two vernacular `top_down` / `bottom_up`) maps to its canonical
# `Orientation` member; canonical codes also map to themselves so a
# single lookup covers every accepted input. CamelCase (`bottomToTop`),
# space-separated (`"bottom to top"`), and malformed-with-extra-under-
# scores (`bo_ttom_t_o_top`) are deliberately rejected — strict table
# lookup is what enforces this.
_ALIAS_TABLE: dict[str, Orientation] = {
    "bt": Orientation.BT,
    "tb": Orientation.TB,
    "lr": Orientation.LR,
    "rl": Orientation.RL,
    "td": Orientation.TB,
    "ltr": Orientation.LR,
    "rtl": Orientation.RL,
    "bottom_to_top": Orientation.BT,
    "top_to_bottom": Orientation.TB,
    "left_to_right": Orientation.LR,
    "right_to_left": Orientation.RL,
    "bottom_up": Orientation.BT,
    "top_down": Orientation.TB,
}


def normalize_orientation(value: object) -> object:
    """Normalize an input orientation string to its canonical `Orientation` member.

    Two-step normalization:

    1. Pre-normalize: lowercase + replace `-` with `_`.
    2. Exact lookup in the alias table; raises if not found.

    Non-string inputs pass through unchanged (Pydantic raises later
    when the value doesn't match the declared `Orientation` type).

    Args:
        value: User-supplied orientation. Strings get normalized;
            anything else passes through.

    Returns:
        The canonical `Orientation` member when the input is a known
        string; the original value otherwise.

    Raises:
        ValueError: When a string input does not normalize to any
            canonical value. The message lists every accepted form.
    """
    if not isinstance(value, str):
        return value
    normalized = value.lower().replace("-", "_")
    if normalized not in _ALIAS_TABLE:
        accepted = ", ".join(sorted(_ALIAS_TABLE))
        raise ValueError(
            f"unknown orientation {value!r}; accepted (case-insensitive, `-` and `_` interchangeable): {accepted}"
        )
    return _ALIAS_TABLE[normalized]
