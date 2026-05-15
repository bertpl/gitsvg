"""Tests for font-chain-aware text-width computation."""

import pytest

from gitsvg.render._glyph_metrics import (
    GlyphWidths,
    parse_chain,
    resolve_chain,
    text_width,
)
from gitsvg.render._glyph_widths import inter_bold, inter_regular, sans_serif_regular


# ==================================================================================================
#  parse_chain
# ==================================================================================================
@pytest.mark.parametrize(
    "raw, expected",
    [
        ("Inter, sans-serif", ["inter", "sans-serif"]),
        ("'Inter', sans-serif", ["inter", "sans-serif"]),
        ('"Inter", sans-serif', ["inter", "sans-serif"]),
        (
            "'Inter', 'Helvetica Neue', Helvetica, Arial, sans-serif",
            ["inter", "helvetica neue", "helvetica", "arial", "sans-serif"],
        ),
        ("INTER, SANS-SERIF", ["inter", "sans-serif"]),
        ("  Inter  ,  sans-serif  ", ["inter", "sans-serif"]),
        ("Inter,,sans-serif", ["inter", "sans-serif"]),
        ("", []),
    ],
)
def test_parse_chain(raw: str, expected: list[str]) -> None:
    # --- arrange / act ----------------
    actual = parse_chain(raw)

    # --- assert -----------------------
    assert actual == expected


# ==================================================================================================
#  resolve_chain
# ==================================================================================================
def test_resolve_chain_known_entries_only() -> None:
    # --- arrange ----------------------
    chain = ["inter", "helvetica neue", "sans-serif", "fantasy"]

    # --- act --------------------------
    resolved = resolve_chain(chain, bold=False)

    # --- assert -----------------------
    # Two known entries; the other two are silently skipped.
    assert len(resolved) == 2
    assert all(isinstance(g, GlyphWidths) for g in resolved)


def test_resolve_chain_picks_bold_when_requested() -> None:
    # --- arrange / act ----------------
    regular = resolve_chain(["inter"], bold=False)[0]
    bold = resolve_chain(["inter"], bold=True)[0]

    # --- assert -----------------------
    # Bold weight produces a different (wider) table for at least one character.
    assert regular.table != bold.table
    assert bold.table["W"] >= regular.table["W"]


# ==================================================================================================
#  GlyphWidths
# ==================================================================================================
def test_glyph_widths_falls_back_to_widest_for_missing_char() -> None:
    # --- arrange ----------------------
    gw = GlyphWidths.from_widths({"a": 0.5, "b": 0.6, "c": 0.7})

    # --- act --------------------------
    known = gw.width_of("a")
    missing = gw.width_of("é")

    # --- assert -----------------------
    assert known == 0.5
    assert missing == 0.7  # widest in the LUT


# ==================================================================================================
#  text_width
# ==================================================================================================
def test_text_width_scales_linearly_with_font_size() -> None:
    # --- arrange / act ----------------
    width_at_10 = text_width("hello", "Inter, sans-serif", font_size=10)
    width_at_20 = text_width("hello", "Inter, sans-serif", font_size=20)

    # --- assert -----------------------
    assert width_at_20 == pytest.approx(2 * width_at_10)


def test_text_width_takes_per_character_max_across_chain() -> None:
    # --- arrange ----------------------
    text = "W"  # wide capital; tends to differ across fonts

    # --- act --------------------------
    width_inter_only = text_width(text, "Inter", font_size=1)
    width_sans_only = text_width(text, "sans-serif", font_size=1)
    width_combined = text_width(text, "Inter, sans-serif", font_size=1)

    # --- assert -----------------------
    # Combined chain takes the widest of the two LUTs.
    assert width_combined == pytest.approx(max(width_inter_only, width_sans_only))


def test_text_width_handles_unknown_chain_via_heuristic() -> None:
    # --- arrange / act ----------------
    width = text_width("hello", "Comic Sans MS, cursive", font_size=10)

    # --- assert -----------------------
    # Falls back to the per-character heuristic (5 chars × 10px × 0.58).
    assert width == pytest.approx(5 * 10 * 0.58)


def test_text_width_bold_widens_compared_to_regular() -> None:
    # --- arrange ----------------------
    text = "feature/long-branch-name"

    # --- act --------------------------
    regular = text_width(text, "Inter, sans-serif", font_size=11, bold=False)
    bold = text_width(text, "Inter, sans-serif", font_size=11, bold=True)

    # --- assert -----------------------
    assert bold > regular


def test_text_width_zero_for_empty_string() -> None:
    # --- arrange / act ----------------
    width = text_width("", "Inter, sans-serif", font_size=11)

    # --- assert -----------------------
    assert width == 0.0


# ==================================================================================================
#  Parity sanity — measured widths beat the old heuristic where they should
# ==================================================================================================
def test_narrow_chars_measured_tighter_than_uniform_factor() -> None:
    """A string of narrow letters now sums to less than `len × 0.58 × font_size`."""
    # --- arrange ----------------------
    text = "iiiiii"
    font_size = 11

    # --- act --------------------------
    measured = text_width(text, "Inter, sans-serif", font_size=font_size)
    old_heuristic = len(text) * font_size * 0.58

    # --- assert -----------------------
    assert measured < old_heuristic


def test_wide_chars_measured_wider_than_uniform_factor() -> None:
    """A string of wide letters now sums to more than `len × 0.58 × font_size`."""
    # --- arrange ----------------------
    text = "WWWWWW"
    font_size = 11

    # --- act --------------------------
    measured = text_width(text, "Inter, sans-serif", font_size=font_size)
    old_heuristic = len(text) * font_size * 0.58

    # --- assert -----------------------
    assert measured > old_heuristic


# ==================================================================================================
#  Sanity on the bundled LUTs
# ==================================================================================================
@pytest.mark.parametrize(
    "lut_module",
    [inter_regular, inter_bold, sans_serif_regular],
)
def test_lut_modules_have_basic_coverage(lut_module) -> None:
    """Every bundled LUT covers ASCII letters and digits."""
    # --- assert -----------------------
    for char in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789":
        assert char in lut_module.WIDTHS, f"{char!r} missing from {lut_module.__name__}"
    assert " " in lut_module.WIDTHS
