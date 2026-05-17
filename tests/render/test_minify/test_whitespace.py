"""Unit tests for the `strip_inter_element_whitespace` step."""

from gitsvg.render._minify import strip_inter_element_whitespace


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
