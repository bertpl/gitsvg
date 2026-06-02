"""Tests for table cell-text preparation (`gitsvg.render._table.text`)."""

import pytest

from gitsvg.render._glyph_metrics import text_width
from gitsvg.render._table import fit_text, flatten_message

_FONT = "Inter, sans-serif"
_SIZE = 12.0


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("one line", "one line"),
        ("a\nb\nc", "a b c"),
        ("a\r\nb", "a b"),
        ("trailing\n", "trailing"),
        ("", ""),
    ],
)
def test_flatten_message(raw: str, expected: str) -> None:
    # --- arrange / act / assert -------
    assert flatten_message(raw) == expected


def test_fit_text_returns_text_unchanged_when_it_fits() -> None:
    # --- arrange / act ----------------
    result = fit_text("short", 1000.0, _FONT, _SIZE)

    # --- assert -----------------------
    assert result == "short"


def test_fit_text_ellipsizes_when_too_wide() -> None:
    # --- arrange ----------------------
    text = "a very long commit message that will not fit in a narrow column"
    max_width = 60.0

    # --- act --------------------------
    result = fit_text(text, max_width, _FONT, _SIZE)

    # --- assert -----------------------
    assert result != text
    assert result.endswith("…")
    assert text_width(result, _FONT, _SIZE) <= max_width
    # The kept prefix is genuinely a prefix of the original (sans ellipsis).
    assert text.startswith(result[:-1])


def test_fit_text_returns_empty_when_not_even_ellipsis_fits() -> None:
    # --- arrange / act ----------------
    result = fit_text("anything", 0.5, _FONT, _SIZE)

    # --- assert -----------------------
    assert result == ""


def test_fit_text_keeps_more_characters_in_a_wider_column() -> None:
    """A wider column keeps at least as many characters as a narrower one."""
    # --- arrange ----------------------
    text = "a very long commit message that will not fit in a narrow column"

    # --- act --------------------------
    narrow = fit_text(text, 60.0, _FONT, _SIZE)
    wide = fit_text(text, 120.0, _FONT, _SIZE)

    # --- assert -----------------------
    assert len(wide) >= len(narrow)
    assert text_width(wide, _FONT, _SIZE) <= 120.0
