"""Unit tests for `gitsvg.render._minify` round-1 reduction passes."""

import pytest

from gitsvg.render._minify import minify, round_numbers


# ==================================================================================================
#  round_numbers
# ==================================================================================================
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
        # negative numbers
        ("translate(-5.5, 10.27)", 1, "translate(-5.5, 10.3)"),
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


# ==================================================================================================
#  minify entrypoint
# ==================================================================================================
def test_minify_is_noop_when_small_is_false() -> None:
    # --- arrange ----------------------
    svg = '<svg width="100.123"><circle cx="50.5" cy="50.5"/></svg>'

    # --- act --------------------------
    result = minify(svg, small=False)

    # --- assert -----------------------
    assert result == svg


def test_minify_applies_round1_rounding_when_small_is_true() -> None:
    # --- arrange ----------------------
    svg = '<svg width="100.123"><circle cx="50.519999999999996" cy="50.5"/></svg>'

    # --- act --------------------------
    result = minify(svg, small=True)

    # --- assert -----------------------
    assert result == '<svg width="100.1"><circle cx="50.5" cy="50.5"/></svg>'


def test_minify_preserves_stroke_width_and_opacity() -> None:
    """Round-1 rounding to 1 decimal must not flatten sub-pixel stroke widths or opacities."""
    # --- arrange ----------------------
    svg = '<path stroke-width="0.7"/><rect opacity="0.85"/>'

    # --- act --------------------------
    result = minify(svg, small=True)

    # --- assert -----------------------
    assert 'stroke-width="0.7"' in result
    # 0.85 → 0.8 under banker's rounding; the salient property is that it's still < 1.
    assert 'opacity="0.8"' in result
