"""Unit tests for `gitsvg.render._minify` round-1 reduction passes."""

import pytest

from gitsvg.render._minify import (
    drop_default_attribute_values,
    drop_empty_defs_and_unused_xlink,
    hoist_font_family_to_root,
    minify,
    round_numbers,
    strip_inter_element_whitespace,
)


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
#  strip_inter_element_whitespace
# ==================================================================================================
def test_strip_inter_element_whitespace_removes_newlines_between_elements() -> None:
    # --- arrange ----------------------
    svg = "<svg>\n<defs>\n</defs>\n<path/>\n</svg>"

    # --- act --------------------------
    result = strip_inter_element_whitespace(svg)

    # --- assert -----------------------
    assert result == "<svg><defs></defs><path/></svg>"


def test_strip_inter_element_whitespace_preserves_text_content() -> None:
    """Whitespace bounded by `>` and `<` is structural; whitespace inside element content is not."""
    # --- arrange ----------------------
    svg = "<text>foo bar</text>\n<text>  leading and trailing  </text>"

    # --- act --------------------------
    result = strip_inter_element_whitespace(svg)

    # --- assert -----------------------
    assert result == "<text>foo bar</text><text>  leading and trailing  </text>"


# ==================================================================================================
#  drop_empty_defs_and_unused_xlink
# ==================================================================================================
def test_drop_empty_defs_removes_empty_defs_block() -> None:
    # --- arrange ----------------------
    svg = "<svg><defs>\n</defs><path/></svg>"

    # --- act --------------------------
    result = drop_empty_defs_and_unused_xlink(svg)

    # --- assert -----------------------
    assert "<defs>" not in result
    assert "</defs>" not in result


def test_drop_empty_defs_keeps_non_empty_defs_block() -> None:
    # --- arrange ----------------------
    svg = "<svg><defs><symbol id='a'/></defs><path/></svg>"

    # --- act --------------------------
    result = drop_empty_defs_and_unused_xlink(svg)

    # --- assert -----------------------
    assert "<defs>" in result
    assert "<symbol id='a'/>" in result


def test_drop_unused_xlink_when_no_xlink_references() -> None:
    # --- arrange ----------------------
    svg = '<svg xmlns="ns" xmlns:xlink="xl"><path/></svg>'

    # --- act --------------------------
    result = drop_empty_defs_and_unused_xlink(svg)

    # --- assert -----------------------
    assert 'xmlns:xlink="xl"' not in result
    assert 'xmlns="ns"' in result  # the other namespace is untouched


def test_keep_xlink_when_xlink_attributes_present() -> None:
    # --- arrange ----------------------
    svg = '<svg xmlns:xlink="xl"><use xlink:href="#a"/></svg>'

    # --- act --------------------------
    result = drop_empty_defs_and_unused_xlink(svg)

    # --- assert -----------------------
    assert 'xmlns:xlink="xl"' in result


# ==================================================================================================
#  hoist_font_family_to_root
# ==================================================================================================
def test_hoist_font_family_when_uniform_across_text_elements() -> None:
    # --- arrange ----------------------
    svg = (
        '<svg width="100" height="100">'
        '<text x="0" font-family="Inter, sans-serif">a</text>'
        '<text x="10" font-family="Inter, sans-serif">b</text>'
        "</svg>"
    )

    # --- act --------------------------
    result = hoist_font_family_to_root(svg)

    # --- assert -----------------------
    assert result.count("font-family=") == 1
    assert 'font-family="Inter, sans-serif"' in result.split(">", 1)[0]
    assert '<text x="0">a</text>' in result
    assert '<text x="10">b</text>' in result


def test_hoist_font_family_skips_when_values_differ() -> None:
    # --- arrange ----------------------
    svg = '<svg><text font-family="Inter, sans-serif">a</text><text font-family="Courier, monospace">b</text></svg>'

    # --- act --------------------------
    result = hoist_font_family_to_root(svg)

    # --- assert -----------------------
    # Untouched: still two font-family attributes, none on the root.
    assert result == svg


def test_hoist_font_family_skips_when_no_text_elements() -> None:
    # --- arrange ----------------------
    svg = '<svg><path d="M0,0"/></svg>'

    # --- act --------------------------
    result = hoist_font_family_to_root(svg)

    # --- assert -----------------------
    assert result == svg


# ==================================================================================================
#  drop_default_attribute_values
# ==================================================================================================
@pytest.mark.parametrize("default_value", ["400", "normal"])
def test_drop_default_font_weight(default_value: str) -> None:
    # --- arrange ----------------------
    svg = f'<text font-size="11" font-weight="{default_value}">a</text>'

    # --- act --------------------------
    result = drop_default_attribute_values(svg)

    # --- assert -----------------------
    assert "font-weight=" not in result
    assert 'font-size="11"' in result


def test_drop_default_attribute_values_keeps_non_default_font_weight() -> None:
    # --- arrange ----------------------
    svg = '<text font-weight="500">a</text>'

    # --- act --------------------------
    result = drop_default_attribute_values(svg)

    # --- assert -----------------------
    assert 'font-weight="500"' in result


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
    svg = '<svg width="100.1234"><circle cx="50.519999999999996" cy="50.5"/></svg>'

    # --- act --------------------------
    result = minify(svg, small=True)

    # --- assert -----------------------
    # 100.1234 -> 100.123 (3 dp); 50.5199... -> 50.52; 50.5 stays.
    assert result == '<svg width="100.123"><circle cx="50.52" cy="50.5"/></svg>'


def test_minify_preserves_stroke_width_and_opacity_exactly() -> None:
    """Round-1 rounding to 3 decimals + trailing-zero strip preserves 1-2 dp values."""
    # --- arrange ----------------------
    svg = '<path stroke-width="0.7"/><rect opacity="0.85"/>'

    # --- act --------------------------
    result = minify(svg, small=True)

    # --- assert -----------------------
    assert 'stroke-width="0.7"' in result
    assert 'opacity="0.85"' in result


def test_minify_runs_full_round1_bundle() -> None:
    """End-to-end: the four PR2 passes plus PR1's rounding combine into the small entrypoint."""
    # --- arrange ----------------------
    svg = (
        '<svg xmlns="ns" xmlns:xlink="xl">\n'
        "<defs>\n</defs>\n"
        '<text font-family="Inter, sans-serif" font-weight="400">a</text>\n'
        '<text font-family="Inter, sans-serif" font-weight="400">b</text>\n'
        "</svg>"
    )

    # --- act --------------------------
    result = minify(svg, small=True)

    # --- assert -----------------------
    assert "<defs>" not in result
    assert "xmlns:xlink" not in result
    assert "font-weight=" not in result
    assert result.count("font-family=") == 1
    assert 'font-family="Inter, sans-serif"' in result.split(">", 1)[0]
    assert ">\n<" not in result  # no inter-element whitespace
