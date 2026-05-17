"""Unit tests for the `round_numbers` step."""

import pytest

from gitsvg.render._minify import round_numbers


@pytest.mark.parametrize(
    "raw, decimals, expected",
    [
        # 1-decimal rounding
        ('x="105.32"', 1, 'x="105.3"'),
        ('width="37.519999999999996"', 1, 'width="37.5"'),
        ('y="200.0"', 1, 'y="200"'),
        # integer rounding
        ('x="105.32"', 0, 'x="105"'),
        ('cx="175.5"', 0, 'cx="176"'),
        # multiple numbers per line, including in path data
        ('d="M105.32,15.0 L105.32,185.0"', 1, 'd="M105.3,15 L105.3,185"'),
        # negative numbers inside a quoted transform value
        ('transform="translate(-5.5, 10.27)"', 1, 'transform="translate(-5.5, 10.3)"'),
        # integers untouched
        ('viewBox="0 0 200 200"', 1, 'viewBox="0 0 200 200"'),
        ('stroke-dasharray="4,4"', 0, 'stroke-dasharray="4,4"'),
        # opacity / stroke-width preserved at 1 decimal
        ('opacity="0.85" stroke-width="0.7"', 1, 'opacity="0.8" stroke-width="0.7"'),
    ],
)
def test_round_numbers(raw: str, decimals: int, expected: str) -> None:
    # --- act --------------------------
    result = round_numbers(raw, decimals=decimals)

    # --- assert -----------------------
    assert result == expected


def test_round_numbers_leaves_non_numeric_content_alone() -> None:
    # --- arrange ----------------------
    raw = '<text font-family="Inter, sans-serif">main</text>'

    # --- act --------------------------
    result = round_numbers(raw, decimals=1)

    # --- assert -----------------------
    assert result == raw


def test_round_numbers_leaves_text_content_alone() -> None:
    """Numbers inside element text (between `>` and `<`) must not be rounded.

    Regression: an earlier implementation matched decimals anywhere in the
    SVG string, rewriting `<text>release v1.0</text>` to `release v1`.
    """
    # --- arrange ----------------------
    raw = '<text x="100">release v1.0</text>'

    # --- act --------------------------
    result = round_numbers(raw, decimals=0)

    # --- assert -----------------------
    assert ">release v1.0</text>" in result
