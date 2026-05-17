"""Unit tests for the font-family passes: `trim_font_family_fallback` and `hoist_font_family_to_root`."""

from gitsvg.render._minify import hoist_font_family_to_root, trim_font_family_fallback
from gitsvg.theme import DEFAULT_THEME


def test_trim_font_family_fallback_replaces_full_chain() -> None:
    # --- arrange ----------------------
    svg = "<text font-family=\"'Inter', 'Helvetica Neue', Helvetica, Arial, sans-serif\">a</text>"

    # --- act --------------------------
    result = trim_font_family_fallback(svg, DEFAULT_THEME)

    # --- assert -----------------------
    assert result == '<text font-family="Inter, sans-serif">a</text>'


def test_trim_font_family_fallback_leaves_unrelated_strings_alone() -> None:
    # --- arrange ----------------------
    svg = '<text font-family="Courier, monospace">a</text>'

    # --- act --------------------------
    result = trim_font_family_fallback(svg, DEFAULT_THEME)

    # --- assert -----------------------
    assert result == svg


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
