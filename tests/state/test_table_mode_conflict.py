"""E223 / E224 — `commit_label_layout: table` mutual-exclusion checks.

Both run at the `apply_ops` orchestration point on the resolved theme:
E223 (table × horizontal orientation) and E224 (table × explicit
`commit_row_mode: shared`). Because they check the *final* resolved
state, a later named-theme switch that drops table mode clears the
conflict.
"""

from gitsvg.parse import parse_jsonl_text
from gitsvg.state import apply_ops


def _codes(text: str) -> list[str]:
    """Parse + apply `text`, returning the emitted error codes."""
    parsed, report = parse_jsonl_text(text, file="x.jsonl")
    apply_ops(parsed, report)
    return [e.code for e in report.errors]


# ==================================================================================================
#  E223 — table × horizontal orientation
# ==================================================================================================
def test_table_with_lr_emits_e223() -> None:
    # --- arrange / act ----------------
    codes = _codes('{"op": "theme", "orientation": "lr", "commit_label_layout": "table"}\n')

    # --- assert -----------------------
    assert "E223" in codes


def test_table_with_rl_emits_e223() -> None:
    # --- arrange / act ----------------
    codes = _codes('{"op": "theme", "orientation": "rl", "commit_label_layout": "table"}\n')

    # --- assert -----------------------
    assert "E223" in codes


def test_table_with_vertical_orientation_is_clean() -> None:
    # --- arrange / act ----------------
    codes = _codes('{"op": "theme", "orientation": "tb", "commit_label_layout": "table"}\n')

    # --- assert -----------------------
    assert "E223" not in codes


def test_table_with_default_orientation_is_clean() -> None:
    """Default orientation is `bt` (vertical) → no E223."""
    # --- arrange / act ----------------
    codes = _codes('{"op": "theme", "commit_label_layout": "table"}\n')

    # --- assert -----------------------
    assert "E223" not in codes


def test_e223_attributed_to_the_layout_op_line() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "theme", "orientation": "lr"}\n'
        '{"op": "theme", "commit_label_layout": "table"}\n'
    )

    # --- act --------------------------
    parsed, report = parse_jsonl_text(text, file="x.jsonl")
    apply_ops(parsed, report)

    # --- assert -----------------------
    e223 = next(e for e in report.errors if e.code == "E223")
    assert e223.line == 3  # the op that set commit_label_layout
    assert e223.field == "commit_label_layout"


# ==================================================================================================
#  E224 — table × explicit commit_row_mode: shared
# ==================================================================================================
def test_table_with_explicit_shared_emits_e224() -> None:
    # --- arrange / act ----------------
    codes = _codes('{"op": "theme", "commit_label_layout": "table", "commit_row_mode": "shared"}\n')

    # --- assert -----------------------
    assert "E224" in codes


def test_table_with_explicit_unique_is_clean() -> None:
    # --- arrange / act ----------------
    codes = _codes('{"op": "theme", "commit_label_layout": "table", "commit_row_mode": "unique"}\n')

    # --- assert -----------------------
    assert "E224" not in codes


def test_table_without_row_mode_is_clean() -> None:
    """Leaving `commit_row_mode` unset is fine — table mode forces unique on its own."""
    # --- arrange / act ----------------
    codes = _codes('{"op": "theme", "commit_label_layout": "table"}\n')

    # --- assert -----------------------
    assert "E224" not in codes


def test_shared_without_table_mode_is_clean() -> None:
    """`commit_row_mode: shared` is only a conflict under table mode."""
    # --- arrange / act ----------------
    codes = _codes('{"op": "theme", "commit_row_mode": "shared"}\n')

    # --- assert -----------------------
    assert "E224" not in codes


def test_e224_attributed_to_the_row_mode_op_line() -> None:
    # --- arrange ----------------------
    text = '{"op": "theme", "commit_label_layout": "table"}\n{"op": "theme", "commit_row_mode": "shared"}\n'

    # --- act --------------------------
    parsed, report = parse_jsonl_text(text, file="x.jsonl")
    apply_ops(parsed, report)

    # --- assert -----------------------
    e224 = next(e for e in report.errors if e.code == "E224")
    assert e224.line == 2  # the op that set commit_row_mode
    assert e224.field == "commit_row_mode"


# ==================================================================================================
#  Named-theme escape hatch (end-of-apply checking)
# ==================================================================================================
def test_named_theme_switch_dropping_table_clears_e223() -> None:
    """A later named-theme switch (default wipe) drops table mode → the conflict clears."""
    # --- arrange / act ----------------
    codes = _codes(
        '{"op": "theme", "orientation": "lr", "commit_label_layout": "table"}\n'
        '{"op": "theme", "name": "dark"}\n'  # default keep_prior_overrides=false → wipes table mode
    )

    # --- assert -----------------------
    assert "E223" not in codes
