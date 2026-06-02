"""Unit tests for the `extract_css_classes` step."""

import re

from gitsvg.render._minify import extract_css_classes


def test_three_elements_sharing_exact_cluster_emit_one_trunk_class() -> None:
    """All members of a tag-kind sharing the same attrs → one trunk class, no leaves."""
    # --- arrange ----------------------
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg">'
        '<path stroke="#a00" stroke-width="2" fill="none" d="M0,0"/>'
        '<path stroke="#a00" stroke-width="2" fill="none" d="M1,1"/>'
        '<path stroke="#a00" stroke-width="2" fill="none" d="M2,2"/>'
        "</svg>"
    )

    # --- act --------------------------
    result = extract_css_classes(svg)

    # --- assert -----------------------
    assert "<style>" in result
    # Trunk extracts the full shared cluster — no presentation attrs remain inline.
    assert result.count('class="c1"') == 3
    for forbidden in ('stroke="#a00"', 'stroke-width="2"', 'fill="none"'):
        assert forbidden not in result, f"{forbidden} should have been extracted into the class"


def test_shared_trunk_with_color_variants_emits_trunk_plus_leaf_classes() -> None:
    """The gitsvg pattern: shared structural baseline + per-color leaves."""
    # --- arrange ----------------------
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg">'
        '<path stroke="#a00" stroke-width="2" fill="none" d="M0,0"/>'
        '<path stroke="#a00" stroke-width="2" fill="none" d="M1,1"/>'
        '<path stroke="#a00" stroke-width="2" fill="none" d="M2,2"/>'
        '<path stroke="#00a" stroke-width="2" fill="none" d="M3,3"/>'
        '<path stroke="#00a" stroke-width="2" fill="none" d="M4,4"/>'
        '<path stroke="#0a0" stroke-width="2" fill="none" d="M5,5"/>'
        "</svg>"
    )

    # --- act --------------------------
    result = extract_css_classes(svg)

    # --- assert -----------------------
    # Trunk: {stroke-width:2, fill:none} → c1, applied to all 6 paths.
    # Leaf: {stroke:#a00} → c2 (3 uses); {stroke:#00a} → c3 (2 uses); green alone.
    assert "<style>" in result
    # c1 appears on every path (combined with leaves on multi-class refs).
    assert result.count('"c1') == 6
    # Trunk attrs gone from inline.
    assert 'stroke-width="2"' not in result
    assert 'fill="none"' not in result
    # Two leaf classes (red and blue) extracted; green stays inline.
    assert 'class="c1 c2"' in result
    assert 'class="c1 c3"' in result
    assert 'stroke="#0a0"' in result  # green still inline (singleton)


def test_singleton_element_does_not_get_extracted() -> None:
    """A unique cluster with one member stays inline (n < 2 floor)."""
    # --- arrange ----------------------
    svg = '<svg xmlns="http://www.w3.org/2000/svg"><path stroke="#a00" stroke-width="2" fill="none" d="M0,0"/></svg>'

    # --- act --------------------------
    result = extract_css_classes(svg)

    # --- assert -----------------------
    assert "<style>" not in result
    assert "class=" not in result
    assert 'stroke="#a00"' in result


def test_two_tag_kinds_get_independent_trunks() -> None:
    """Each tag-kind's trunk is computed in isolation; no cross-tag leakage."""
    # --- arrange ----------------------
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg">'
        '<path stroke="#a00" stroke-width="2" d="M0,0"/>'
        '<path stroke="#a00" stroke-width="2" d="M1,1"/>'
        '<text font-family="Inter" font-size="11" x="0" y="0">a</text>'
        '<text font-family="Inter" font-size="11" x="10" y="10">b</text>'
        "</svg>"
    )

    # --- act --------------------------
    result = extract_css_classes(svg)

    # --- assert -----------------------
    assert "<style>" in result
    # Two trunk classes: one for <path>, one for <text>.
    assert ".c1{" in result
    assert ".c2{" in result
    # Both paths share c1; both texts share c2.
    assert result.count('class="c1"') == 2
    assert result.count('class="c2"') == 2


def test_residuals_across_tag_kinds_can_share_a_leaf_class() -> None:
    """A residual cluster `{fill:#fff}` that appears on both a path and a text shares one leaf class."""
    # --- arrange ----------------------
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg">'
        '<path fill="#fff" stroke-width="2" d="M0,0"/>'
        '<path fill="#fff" stroke-width="2" d="M1,1"/>'
        '<text fill="#fff" font-size="11" x="0" y="0">a</text>'
        '<text fill="#fff" font-size="11" x="10" y="10">b</text>'
        "</svg>"
    )

    # --- act --------------------------
    result = extract_css_classes(svg)

    # --- assert -----------------------
    # Path trunk: {fill:#fff, stroke-width:2}; text trunk: {fill:#fff, font-size:11}.
    # Each tag-kind extracts its own full trunk; no cross-kind leaf needed since
    # all members already got their full presentation set extracted.
    assert "<style>" in result
    assert 'fill="#fff"' not in result
    assert 'stroke-width="2"' not in result
    assert 'font-size="11"' not in result


def test_no_extraction_returns_input_unchanged() -> None:
    """When nothing meets the extraction threshold, return the input string verbatim."""
    # --- arrange ----------------------
    svg = '<svg xmlns="http://www.w3.org/2000/svg"><path d="M0,0"/></svg>'

    # --- act --------------------------
    result = extract_css_classes(svg)

    # --- assert -----------------------
    assert result == svg


def test_idempotent_extraction() -> None:
    """Running extraction twice produces the same output as running it once."""
    # --- arrange ----------------------
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg">'
        '<path stroke="#a00" stroke-width="2" fill="none" d="M0,0"/>'
        '<path stroke="#a00" stroke-width="2" fill="none" d="M1,1"/>'
        "</svg>"
    )

    # --- act --------------------------
    once = extract_css_classes(svg)
    twice = extract_css_classes(once)

    # --- assert -----------------------
    assert once == twice


def test_class_names_are_deterministic() -> None:
    """The same input always produces the same class numbering."""
    # --- arrange ----------------------
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg">'
        '<path stroke="#a00" stroke-width="2" d="M0,0"/>'
        '<path stroke="#a00" stroke-width="2" d="M1,1"/>'
        "</svg>"
    )

    # --- act --------------------------
    first = extract_css_classes(svg)
    second = extract_css_classes(svg)

    # --- assert -----------------------
    assert first == second
    assert re.search(r"\.c1\{[^}]*stroke", first)


def test_font_size_is_emitted_with_px_unit() -> None:
    """CSS-context `font-size` requires a unit suffix; bare numerics get `px` appended.

    Regression: a CSS rule `font-size:11` is invalid syntax — browsers ignore it
    and text falls back to the default size. The extract step must emit
    `font-size:11px` so the rule actually applies.
    """
    # --- arrange ----------------------
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg">'
        '<text font-size="11" fill="#000" x="0" y="0">a</text>'
        '<text font-size="11" fill="#000" x="10" y="10">b</text>'
        "</svg>"
    )

    # --- act --------------------------
    result = extract_css_classes(svg)

    # --- assert -----------------------
    assert "font-size:11px" in result
    assert "font-size:11;" not in result and "font-size:11}" not in result


def test_invalid_xml_returns_unchanged() -> None:
    """A non-parseable SVG passes through unchanged rather than erroring."""
    # --- arrange ----------------------
    svg = "not a valid SVG"

    # --- act --------------------------
    result = extract_css_classes(svg)

    # --- assert -----------------------
    assert result == svg
