"""Color-string helpers shared across pipeline stages.

`is_color_visible` decides whether a resolved color value would paint
anything. The renderer reads it to skip a no-op fill (so an unset or
fully-transparent band stays byte-identical to no band at all), and the
same predicate backs the validation that rejects a band color set to a
visible value where it has no effect.

Lives in `theme/` because both the renderer and the state engine
already depend on the theme package, so a neutral home here avoids
coupling the two stages to each other.
"""


def is_color_visible(color: str | None) -> bool:
    """Return whether `color` would paint a visible fill.

    A color is invisible when it is unset (`None`) or a hex value whose
    alpha channel is fully zero — `#RGBA` with `A == 0`, or `#RRGGBBAA`
    with `AA == 00`. Hex values without an alpha channel (`#RGB`,
    `#RRGGBB`) imply full opacity and are therefore visible.

    Args:
        color: A resolved color string (3-, 4-, 6-, or 8-digit hex with
            a leading `#`), or `None`.

    Returns:
        `True` if the color paints something; `False` if it is unset or
        fully transparent.
    """
    if color is None:
        return False
    hex_digits = color.removeprefix("#")
    if len(hex_digits) == 4:  # #RGBA — last nibble is alpha
        return hex_digits[-1] != "0"
    if len(hex_digits) == 8:  # #RRGGBBAA — last byte is alpha
        return hex_digits[-2:] != "00"
    return True  # #RGB / #RRGGBB — no alpha channel, fully opaque
