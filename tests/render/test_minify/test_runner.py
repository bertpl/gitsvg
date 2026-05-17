"""Integration tests for the `minify(...)` entry point."""

from gitsvg.render._minify import minify
from gitsvg.theme import DEFAULT_THEME


def test_minify_is_noop_when_small_is_false() -> None:
    # --- arrange ----------------------
    svg = '<svg width="100.123"><circle cx="50.5" cy="50.5"/></svg>'

    # --- act --------------------------
    result = minify(svg, small=False, theme=DEFAULT_THEME)

    # --- assert -----------------------
    assert result == svg


def test_minify_applies_round1_rounding_when_small_is_true() -> None:
    # --- arrange ----------------------
    svg = '<svg width="100.1234"><circle cx="50.519999999999996" cy="50.5"/></svg>'

    # --- act --------------------------
    result = minify(svg, small=True, theme=DEFAULT_THEME)

    # --- assert -----------------------
    # 100.1234 -> 100.123 (3 dp); 50.5199... -> 50.52; 50.5 stays.
    assert result == '<svg width="100.123"><circle cx="50.52" cy="50.5"/></svg>'


def test_minify_preserves_stroke_width_and_opacity_exactly() -> None:
    """Round-1 rounding to 3 decimals + trailing-zero strip preserves 1-2 dp values."""
    # --- arrange ----------------------
    svg = '<path stroke-width="0.7"/><rect opacity="0.85"/>'

    # --- act --------------------------
    result = minify(svg, small=True, theme=DEFAULT_THEME)

    # --- assert -----------------------
    assert 'stroke-width="0.7"' in result
    assert 'opacity="0.85"' in result


def test_minify_runs_full_round1_bundle() -> None:
    """End-to-end: the full round-1 pass set combines into the small entrypoint."""
    # --- arrange ----------------------
    svg = (
        '<svg xmlns="ns" xmlns:xlink="xl">\n'
        "<defs>\n</defs>\n"
        '<text font-family="Inter, sans-serif" font-weight="400">a</text>\n'
        '<text font-family="Inter, sans-serif" font-weight="400">b</text>\n'
        "</svg>"
    )

    # --- act --------------------------
    result = minify(svg, small=True, theme=DEFAULT_THEME)

    # --- assert -----------------------
    assert "<defs>" not in result
    assert "xmlns:xlink" not in result
    assert "font-weight=" not in result
    assert result.count("font-family=") == 1
    assert 'font-family="Inter, sans-serif"' in result.split(">", 1)[0]
    assert ">\n<" not in result  # no inter-element whitespace
