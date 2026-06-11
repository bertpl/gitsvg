"""Resolution tests for `theme.table_cell_padding_x_in_font_sizes`."""

from gitsvg.parse import parse_jsonl_text
from gitsvg.state import apply_ops
from gitsvg.theme import DefaultTheme


def test_default_is_half_a_font_size() -> None:
    # --- arrange / act ----------------
    theme = DefaultTheme.build({})
    _, renderer_settings = theme.split()

    # --- assert -----------------------
    assert theme.table_cell_padding_x_in_font_sizes == 0.5
    # Resolved px = ratio * label_font_size (accessor lives on the renderer slice).
    assert renderer_settings.table_cell_padding_x == 0.5 * theme.label_font_size


def test_override_resolves_to_pixels() -> None:
    # --- arrange / act ----------------
    theme = DefaultTheme.build({"table_cell_padding_x_in_font_sizes": 1.0})
    _, renderer_settings = theme.split()

    # --- assert -----------------------
    assert renderer_settings.table_cell_padding_x == theme.label_font_size


def test_zero_is_allowed() -> None:
    """Zero padding is legal (cells abut the column edge); only negatives are rejected."""
    # --- arrange / act / assert -------
    assert DefaultTheme.build({"table_cell_padding_x_in_font_sizes": 0.0}).split()[1].table_cell_padding_x == 0.0


def test_negative_rejected_on_theme_op() -> None:
    # --- arrange / act ----------------
    parsed, report = parse_jsonl_text('{"op": "theme", "table_cell_padding_x_in_font_sizes": -0.5}\n', file="x.jsonl")
    apply_ops(parsed, report)

    # --- assert -----------------------
    assert not report.is_clean()
