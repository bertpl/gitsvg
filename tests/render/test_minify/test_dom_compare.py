"""Unit tests for the DOM-comparison helper."""

import pytest

from tests.render.test_minify._dom_compare import assert_dom_equivalent, canonicalise


# ==================================================================================================
#  canonicalise — equivalence cases
# ==================================================================================================
def test_canonicalise_is_idempotent() -> None:
    # --- arrange ----------------------
    svg = '<svg><text font-family="Inter">a</text></svg>'

    # --- act --------------------------
    once = canonicalise(svg)
    twice = canonicalise(once)

    # --- assert -----------------------
    assert once == twice


def test_xml_declaration_is_stripped() -> None:
    # --- arrange ----------------------
    with_decl = '<?xml version="1.0" encoding="UTF-8"?>\n<svg><path/></svg>'
    without_decl = "<svg><path/></svg>"

    # --- act / assert -----------------
    assert canonicalise(with_decl) == canonicalise(without_decl)


def test_inter_element_whitespace_collapses() -> None:
    # --- arrange ----------------------
    with_ws = "<svg>\n  <path/>\n  <circle/>\n</svg>"
    without_ws = "<svg><path/><circle/></svg>"

    # --- act / assert -----------------
    assert canonicalise(with_ws) == canonicalise(without_ws)


def test_empty_defs_block_normalises_to_absent() -> None:
    # --- arrange ----------------------
    with_defs = "<svg><defs></defs><path/></svg>"
    without_defs = "<svg><path/></svg>"

    # --- act / assert -----------------
    assert canonicalise(with_defs) == canonicalise(without_defs)


def test_xmlns_xlink_declaration_is_ignored() -> None:
    # --- arrange ----------------------
    with_xlink = '<svg xmlns:xlink="http://www.w3.org/1999/xlink"><path/></svg>'
    without_xlink = "<svg><path/></svg>"

    # --- act / assert -----------------
    assert canonicalise(with_xlink) == canonicalise(without_xlink)


def test_default_font_weight_is_dropped() -> None:
    # --- arrange ----------------------
    with_default = '<svg><text font-weight="400">a</text></svg>'
    without_default = "<svg><text>a</text></svg>"

    # --- act / assert -----------------
    assert canonicalise(with_default) == canonicalise(without_default)


def test_short_and_long_hex_compare_equal() -> None:
    # --- arrange ----------------------
    short = '<svg><path fill="#abc"/></svg>'
    long = '<svg><path fill="#aabbcc"/></svg>'

    # --- act / assert -----------------
    assert canonicalise(short) == canonicalise(long)


def test_sub_pixel_numeric_diffs_normalise_equal() -> None:
    # --- arrange ----------------------
    hi_precision = '<svg><circle cx="100.123456" cy="200.0001"/></svg>'
    lo_precision = '<svg><circle cx="100.12" cy="200"/></svg>'

    # --- act / assert -----------------
    # Both round to 100.1 / 200.0 at the 1dp canonical precision.
    assert canonicalise(hi_precision) == canonicalise(lo_precision)


def test_hoisted_font_family_matches_unhoisted() -> None:
    """The font-family hoist (root attribute) is equivalent to per-element attribution."""
    # --- arrange ----------------------
    hoisted = '<svg font-family="Inter"><text>a</text><text>b</text></svg>'
    unhoisted = '<svg><text font-family="Inter">a</text><text font-family="Inter">b</text></svg>'

    # --- act / assert -----------------
    assert canonicalise(hoisted) == canonicalise(unhoisted)


def test_attribute_order_does_not_matter() -> None:
    # --- arrange ----------------------
    order_a = '<svg><circle cx="10" cy="20" r="5"/></svg>'
    order_b = '<svg><circle r="5" cy="20" cx="10"/></svg>'

    # --- act / assert -----------------
    assert canonicalise(order_a) == canonicalise(order_b)


# ==================================================================================================
#  assert_dom_equivalent — failure cases
# ==================================================================================================
def test_assert_dom_equivalent_raises_on_geometry_diff() -> None:
    # --- arrange ----------------------
    svg_a = '<svg><circle cx="10" cy="20" r="5"/></svg>'
    svg_b = '<svg><circle cx="99" cy="20" r="5"/></svg>'

    # --- act / assert -----------------
    with pytest.raises(AssertionError, match="not DOM-equivalent"):
        assert_dom_equivalent(svg_a, svg_b)


def test_assert_dom_equivalent_raises_on_missing_element() -> None:
    # --- arrange ----------------------
    svg_a = '<svg><circle cx="10" cy="20" r="5"/><path d="M0,0"/></svg>'
    svg_b = '<svg><circle cx="10" cy="20" r="5"/></svg>'

    # --- act / assert -----------------
    with pytest.raises(AssertionError):
        assert_dom_equivalent(svg_a, svg_b)


def test_assert_dom_equivalent_passes_on_identical_input() -> None:
    # --- arrange ----------------------
    svg = '<svg><circle cx="10" cy="20" r="5" fill="#abc"/></svg>'

    # --- act / assert -----------------
    assert_dom_equivalent(svg, svg)  # no exception
