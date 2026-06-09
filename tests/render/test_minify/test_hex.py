"""Unit tests for the `shorten_hex_colors` step."""

import pytest

from gitsvg.render._minify import shorten_hex_colors


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        # Pair-wise matches shorten.
        ('fill="#aabbcc"', 'fill="#abc"'),
        ('stroke="#ffffff"', 'stroke="#fff"'),
        ('stroke="#000000"', 'stroke="#000"'),
        # Case-preserving (case-sensitive pair matching — mixed-case pairs
        # like `#AaBbCc` do not shorten, since `A` != `a` byte-wise).
        ('fill="#AABBCC"', 'fill="#ABC"'),
        ('fill="#AaBbCc"', 'fill="#AaBbCc"'),
        # Non-matching pairs stay unchanged.
        ('fill="#aabbcd"', 'fill="#aabbcd"'),
        ('fill="#a1b2c3"', 'fill="#a1b2c3"'),
        # Multiple matches in one string.
        ('fill="#aabbcc" stroke="#112233"', 'fill="#abc" stroke="#123"'),
        # 3-digit hex stays unchanged.
        ('fill="#abc"', 'fill="#abc"'),
        # Non-hex content untouched.
        ('font-family="Inter, sans-serif"', 'font-family="Inter, sans-serif"'),
    ],
)
def test_shorten_hex_colors(raw: str, expected: str) -> None:
    # --- act --------------------------
    result = shorten_hex_colors(raw)

    # --- assert -----------------------
    assert result == expected


def test_shorten_does_not_corrupt_longer_hex_strings() -> None:
    """A hash followed by more than 6 hex digits must not be partially shortened."""
    # --- arrange ----------------------
    raw = 'data-id="#abcdef0"'

    # --- act --------------------------
    result = shorten_hex_colors(raw)

    # --- assert -----------------------
    # `#abcdef0` is not a 6-digit hex with pair-matches; lookahead prevents
    # shortening the leading `#abcdef` portion.
    assert result == raw
