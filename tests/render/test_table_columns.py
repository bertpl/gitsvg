"""Tests for table column geometry (`gitsvg.render._table._columns`)."""

from gitsvg.render._table import TableField, compute_table_columns


def test_both_fields_active_pack_message_then_hash() -> None:
    # --- arrange / act ----------------
    layout = compute_table_columns(480, 64, gutter=8)

    # --- assert -----------------------
    assert [c.field for c in layout.columns] == [TableField.MESSAGE, TableField.HASH]
    assert [c.x_offset for c in layout.columns] == [0.0, 488.0]  # 0; 480+8
    assert layout.width == 552.0  # 480 + 8 + 64 (no trailing gutter)


def test_zero_width_message_is_omitted_and_space_reclaimed() -> None:
    """Disabling the message column leaves the hash column at the table origin."""
    # --- arrange / act ----------------
    layout = compute_table_columns(0, 64, gutter=8)

    # --- assert -----------------------
    assert [c.field for c in layout.columns] == [TableField.HASH]
    assert [c.x_offset for c in layout.columns] == [0.0]  # hash at the origin, not shifted by a gutter
    assert layout.width == 64.0


def test_zero_width_hash_leaves_a_single_message_column_with_no_gutter() -> None:
    # --- arrange / act ----------------
    layout = compute_table_columns(480, 0, gutter=8)

    # --- assert -----------------------
    assert [c.field for c in layout.columns] == [TableField.MESSAGE]
    assert layout.columns[0].x_offset == 0.0
    assert layout.width == 480.0


def test_all_fields_disabled_yields_empty_zero_width_table() -> None:
    # --- arrange / act ----------------
    layout = compute_table_columns(0, 0, gutter=8)

    # --- assert -----------------------
    assert layout.columns == []
    assert layout.width == 0.0
