"""Numeric helpers shared across pipeline stages."""


def resolve_int_or_float(value: float) -> int | float:
    """Cast a whole-number float to int; return float otherwise.

    Used by `Theme`'s resolved-pixel properties so the SVG attribute
    formatting matches the pre-ratio defaults exactly (drawsvg writes
    integer values without a decimal point and float values with one).
    """
    return int(value) if value == int(value) else value
