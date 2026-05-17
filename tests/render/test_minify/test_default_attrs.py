"""Unit tests for the `drop_default_attribute_values` step."""

import pytest

from gitsvg.render._minify import drop_default_attribute_values


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
