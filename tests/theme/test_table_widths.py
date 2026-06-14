"""Resolution / override / validation tests for the `table_*_width` fields."""

import pytest
from pydantic import ValidationError

from gitsvg.parse import parse_jsonl_text
from gitsvg.state import apply_ops
from gitsvg.theme import DefaultTheme
from tests._jsonl import build_jsonl


def test_table_widths_have_sensible_defaults() -> None:
    # --- arrange / act ----------------
    theme = DefaultTheme.build({})

    # --- assert -----------------------
    assert theme.table_msg_width == 480
    assert theme.table_hash_width == 64


@pytest.mark.parametrize("field", ["table_msg_width", "table_hash_width"])
def test_table_width_override_and_zero_disable(field: str) -> None:
    # --- arrange / act ----------------
    overridden = DefaultTheme.build({field: 200})
    disabled = DefaultTheme.build({field: 0})

    # --- assert -----------------------
    assert getattr(overridden, field) == 200
    assert getattr(disabled, field) == 0  # 0 is legal — disables the column


@pytest.mark.parametrize("field", ["table_msg_width", "table_hash_width"])
def test_negative_table_width_rejected_at_theme_level(field: str) -> None:
    """The `Theme` field validator rejects negatives (defense in depth)."""
    # --- arrange / act / assert -------
    with pytest.raises(ValidationError):
        DefaultTheme.build({field: -1})


def test_negative_table_width_rejected_on_theme_op() -> None:
    """A negative width is rejected at schema level on the `theme:` op (with a line number)."""
    # --- arrange / act ----------------
    parsed, report = parse_jsonl_text(build_jsonl({"op": "theme", "table_hash_width": -1}), file="x.jsonl")
    apply_ops(parsed, report)

    # --- assert -----------------------
    assert not report.is_clean()


def test_table_widths_resolve_through_apply() -> None:
    # --- arrange / act ----------------
    parsed, report = parse_jsonl_text(
        build_jsonl({"op": "theme", "table_hash_width": 50, "table_msg_width": 300}),
        file="x.jsonl",
    )
    _, theme = apply_ops(parsed, report)

    # --- assert -----------------------
    assert report.is_clean()
    assert (theme.table_msg_width, theme.table_hash_width) == (300, 50)
