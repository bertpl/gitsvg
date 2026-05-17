"""Integration tests for the `minify(...)` entry point under the level dial."""

from gitsvg.render._minify import compute_minify_config, minify
from gitsvg.theme import DEFAULT_THEME


def test_minify_is_noop_at_l0() -> None:
    # --- arrange ----------------------
    svg = '<svg width="100.123"><circle cx="50.5" cy="50.5"/></svg>'
    config = compute_minify_config(0)

    # --- act --------------------------
    result = minify(svg, config, DEFAULT_THEME)

    # --- assert -----------------------
    assert result == svg


def test_minify_at_l1_rounds_to_6dp() -> None:
    # --- arrange ----------------------
    svg = '<svg width="100.1234567"><circle cx="50.5"/></svg>'
    config = compute_minify_config(1)

    # --- act --------------------------
    result = minify(svg, config, DEFAULT_THEME)

    # --- assert -----------------------
    # 100.1234567 rounds to 100.123457 (6 dp). 50.5 is unchanged.
    assert 'width="100.123457"' in result
    assert 'cx="50.5"' in result


def test_minify_at_l1_does_not_trim_font_family() -> None:
    """L1 is lossless: the font-fallback chain stays intact (possibly hoisted to root)."""
    # --- arrange ----------------------
    svg = f'<svg><text font-family="{DEFAULT_THEME.label_font_family}">a</text></svg>'
    config = compute_minify_config(1)

    # --- act --------------------------
    result = minify(svg, config, DEFAULT_THEME)

    # --- assert -----------------------
    assert DEFAULT_THEME.label_font_family in result


def test_minify_at_l2_shortens_hex_and_rounds_to_4dp() -> None:
    # --- arrange ----------------------
    svg = '<svg><path fill="#aabbcc" stroke-width="0.123456"/></svg>'
    config = compute_minify_config(2)

    # --- act --------------------------
    result = minify(svg, config, DEFAULT_THEME)

    # --- assert -----------------------
    assert 'fill="#abc"' in result
    # 0.123456 → 0.1235 at 4dp (unambiguous; 6 > half).
    assert 'stroke-width="0.1235"' in result


def test_minify_at_l3_trims_font_fallback() -> None:
    # --- arrange ----------------------
    svg = f'<svg><text font-family="{DEFAULT_THEME.label_font_family}">a</text></svg>'
    config = compute_minify_config(3)

    # --- act --------------------------
    result = minify(svg, config, DEFAULT_THEME)

    # --- assert -----------------------
    assert DEFAULT_THEME.label_font_family not in result
    assert DEFAULT_THEME.label_font_family_small in result


def test_minify_runs_full_pipeline_at_l3() -> None:
    """End-to-end: every L3-enabled step combines on a representative SVG."""
    # --- arrange ----------------------
    svg = (
        '<svg xmlns="ns" xmlns:xlink="xl">\n'
        "<defs>\n</defs>\n"
        f'<text font-family="{DEFAULT_THEME.label_font_family}" font-weight="400">a</text>\n'
        f'<text font-family="{DEFAULT_THEME.label_font_family}" font-weight="400">b</text>\n'
        '<path fill="#ffffff"/>\n'
        "</svg>"
    )
    config = compute_minify_config(3)

    # --- act --------------------------
    result = minify(svg, config, DEFAULT_THEME)

    # --- assert -----------------------
    assert "<defs>" not in result
    assert "xmlns:xlink" not in result
    assert "font-weight=" not in result
    assert 'fill="#fff"' in result
    assert result.count("font-family=") == 1
    assert DEFAULT_THEME.label_font_family_small in result.split(">", 1)[0]
    assert ">\n<" not in result
