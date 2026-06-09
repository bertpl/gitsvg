"""Unit tests for `MinifyConfig` and `compute_minify_config`."""

import pytest

from gitsvg.render._minify import MinifyConfig, MinifyLevel, compute_minify_config


def test_l0_disables_every_toggle() -> None:
    # --- act --------------------------
    config = compute_minify_config(0)

    # --- assert -----------------------
    assert config.level == 0
    assert not config.drop_default_attrs
    assert not config.drop_empty_defs
    assert not config.hoist_font_family
    assert not config.trim_font_fallback
    assert not config.shorten_hex
    assert not config.round_numbers
    assert not config.extract_css_classes
    assert not config.strip_whitespace
    assert config.rounding_decimals == 0


def test_l1_enables_lossless_basics_only() -> None:
    # --- act --------------------------
    config = compute_minify_config(1)

    # --- assert -----------------------
    assert config.level == 1
    assert config.drop_default_attrs
    assert config.drop_empty_defs
    assert config.hoist_font_family
    assert not config.shorten_hex
    assert not config.trim_font_fallback
    assert not config.extract_css_classes
    assert config.round_numbers
    assert config.strip_whitespace
    assert config.rounding_decimals == 6


def test_l2_adds_hex_shortening_css_extraction_and_tighter_rounding() -> None:
    # --- act --------------------------
    config = compute_minify_config(2)

    # --- assert -----------------------
    assert config.level == 2
    assert config.shorten_hex
    assert config.extract_css_classes
    assert not config.trim_font_fallback
    assert config.rounding_decimals == 4
    # L1 toggles inherit.
    assert config.drop_default_attrs
    assert config.drop_empty_defs
    assert config.hoist_font_family
    assert config.round_numbers
    assert config.strip_whitespace


def test_l3_adds_font_fallback_trim_and_tightest_rounding() -> None:
    # --- act --------------------------
    config = compute_minify_config(3)

    # --- assert -----------------------
    assert config.level == 3
    assert config.trim_font_fallback
    assert config.rounding_decimals == 2
    # L2 toggles inherit.
    assert config.shorten_hex
    assert config.extract_css_classes
    # L1 toggles inherit.
    assert config.drop_default_attrs
    assert config.drop_empty_defs
    assert config.hoist_font_family
    assert config.round_numbers
    assert config.strip_whitespace


@pytest.mark.parametrize("level", [0, 1, 2, 3])
def test_config_is_frozen(level: MinifyLevel) -> None:
    """`MinifyConfig` is a frozen dataclass — mutation should raise."""
    # --- arrange ----------------------
    config = compute_minify_config(level)

    # --- act / assert -----------------
    with pytest.raises((AttributeError, Exception)):
        config.level = 99  # type: ignore[misc]


@pytest.mark.parametrize(("level", "expected_decimals"), [(0, 0), (1, 6), (2, 4), (3, 2)])
def test_rounding_decimals_ladder(level: MinifyLevel, expected_decimals: int) -> None:
    # --- act --------------------------
    config = compute_minify_config(level)

    # --- assert -----------------------
    assert config.rounding_decimals == expected_decimals


def test_minify_config_is_a_dataclass_with_explicit_fields() -> None:
    """Sanity check: `MinifyConfig` exposes the documented set of fields."""
    # --- arrange / act ----------------
    fields = set(MinifyConfig.__dataclass_fields__)

    # --- assert -----------------------
    expected = {
        "level",
        "drop_default_attrs",
        "drop_empty_defs",
        "hoist_font_family",
        "trim_font_fallback",
        "shorten_hex",
        "round_numbers",
        "extract_css_classes",
        "strip_whitespace",
        "rounding_decimals",
    }
    assert fields == expected
