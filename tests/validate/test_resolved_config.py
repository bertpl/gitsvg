"""Resolved-config consistency checks (E221-E224).

`check_resolved_config` runs at the validate stage on the fully-resolved
theme plus the `UserOverrides` record of what the input set. Because the
checks read the *final* resolved state, a later named-theme switch that wipes prior
overrides clears the conflict — exercised by the escape-hatch cases.
"""

from tests._jsonl import build_jsonl
from tests.validate._helpers import resolved_config_report


def _codes(text: str) -> list[str]:
    """Run the resolved-config path on `text`, returning the emitted error codes."""
    return [e.code for e in resolved_config_report(text).errors]


# ==================================================================================================
#  E221 — branch_pos pin × theme.auto_lane_change
# ==================================================================================================
def test_pin_with_auto_lane_change_emits_e221() -> None:
    # --- arrange / act ----------------
    codes = _codes(
        build_jsonl(
            {"op": "theme", "auto_lane_change": True},
            {"op": "branch", "name": "main"},
            {"op": "commit", "branch": "main", "id": "m1", "msg": "x"},
            {"op": "branch", "name": "feat", "from_branch": "main", "branch_pos": 3},
        )
    )

    # --- assert -----------------------
    assert "E221" in codes


def test_pin_without_auto_lane_change_is_clean() -> None:
    # --- arrange / act ----------------
    codes = _codes(
        build_jsonl(
            {"op": "branch", "name": "main"},
            {"op": "commit", "branch": "main", "id": "m1", "msg": "x"},
            {"op": "branch", "name": "feat", "from_branch": "main", "branch_pos": 3},
        )
    )

    # --- assert -----------------------
    assert "E221" not in codes


def test_auto_lane_change_without_pin_is_clean() -> None:
    # --- arrange / act ----------------
    codes = _codes(
        build_jsonl(
            {"op": "theme", "auto_lane_change": True},
            {"op": "branch", "name": "main"},
            {"op": "commit", "branch": "main", "id": "m1", "msg": "x"},
            {"op": "branch", "name": "feat", "from_branch": "main"},
        )
    )

    # --- assert -----------------------
    assert "E221" not in codes


def test_e221_attributed_to_the_pinned_branch_line() -> None:
    """The error points at the `branch:` op that set the pin, not the `theme:` op."""
    # --- arrange ----------------------
    text = build_jsonl(
        {"op": "theme", "auto_lane_change": True},
        {"op": "branch", "name": "main"},
        {"op": "commit", "branch": "main", "id": "m1", "msg": "x"},
        {"op": "branch", "name": "feat", "from_branch": "main", "branch_pos": 3},
    )

    # --- act --------------------------
    report = resolved_config_report(text)

    # --- assert -----------------------
    e221 = next(e for e in report.errors if e.code == "E221")
    assert e221.line == 4  # the pinned `branch:` op
    assert e221.field == "branch_pos"


# ==================================================================================================
#  E222 — merge_lane_clearance set while auto_lane_change is off
# ==================================================================================================
def test_clearance_without_auto_lane_change_emits_e222() -> None:
    # --- arrange / act ----------------
    codes = _codes(build_jsonl({"op": "theme", "merge_lane_clearance": 2}))

    # --- assert -----------------------
    assert "E222" in codes


def test_default_value_clearance_still_emits_e222() -> None:
    """Setting the field to its default `1` is still the mistake — explicit but inert."""
    # --- arrange / act ----------------
    codes = _codes(build_jsonl({"op": "theme", "merge_lane_clearance": 1}))

    # --- assert -----------------------
    assert "E222" in codes


def test_clearance_with_auto_lane_change_is_clean() -> None:
    # --- arrange / act ----------------
    codes = _codes(build_jsonl({"op": "theme", "auto_lane_change": True, "merge_lane_clearance": 2}))

    # --- assert -----------------------
    assert "E222" not in codes


def test_no_clearance_set_is_clean() -> None:
    # --- arrange / act ----------------
    codes = _codes(build_jsonl({"op": "theme", "auto_lane_change": False}))

    # --- assert -----------------------
    assert "E222" not in codes


def test_e222_attributed_to_the_setting_op_line() -> None:
    """The error points at the `theme:` op that set the field, not the diagram start."""
    # --- arrange ----------------------
    text = build_jsonl(
        {"op": "branch", "name": "main"},
        {"op": "commit", "branch": "main", "id": "m1", "msg": "x"},
        {"op": "theme", "merge_lane_clearance": 2},
    )

    # --- act --------------------------
    report = resolved_config_report(text)

    # --- assert -----------------------
    e222 = next(e for e in report.errors if e.code == "E222")
    assert e222.line == 3  # the `theme:` op that set the field
    assert e222.field == "merge_lane_clearance"


def test_named_theme_switch_wipes_clearance_and_clears_e222() -> None:
    """A later named-theme switch (default wipe) drops the override → no E222."""
    # --- arrange / act ----------------
    codes = _codes(
        build_jsonl(
            {"op": "theme", "merge_lane_clearance": 2}, {"op": "theme", "name": "dark"}
        )  # default keep_prior_overrides=false → wipe
    )

    # --- assert -----------------------
    assert "E222" not in codes


def test_keep_prior_overrides_preserves_clearance_and_keeps_e222() -> None:
    """`keep_prior_overrides: true` preserves the override → E222 still fires."""
    # --- arrange ----------------------
    text = build_jsonl(
        {"op": "theme", "merge_lane_clearance": 2}, {"op": "theme", "name": "dark", "keep_prior_overrides": True}
    )

    # --- act --------------------------
    report = resolved_config_report(text)

    # --- assert -----------------------
    e222 = next(e for e in report.errors if e.code == "E222")
    assert e222.line == 1  # the recorded override survives the switch, still points at the setting op


# ==================================================================================================
#  E223 — commit_label_layout: table × horizontal orientation
# ==================================================================================================
def test_table_with_lr_emits_e223() -> None:
    # --- arrange / act ----------------
    codes = _codes(build_jsonl({"op": "theme", "orientation": "lr", "commit_label_layout": "table"}))

    # --- assert -----------------------
    assert "E223" in codes


def test_table_with_rl_emits_e223() -> None:
    # --- arrange / act ----------------
    codes = _codes(build_jsonl({"op": "theme", "orientation": "rl", "commit_label_layout": "table"}))

    # --- assert -----------------------
    assert "E223" in codes


def test_table_with_vertical_orientation_is_clean() -> None:
    # --- arrange / act ----------------
    codes = _codes(build_jsonl({"op": "theme", "orientation": "tb", "commit_label_layout": "table"}))

    # --- assert -----------------------
    assert "E223" not in codes


def test_table_with_default_orientation_is_clean() -> None:
    """Default orientation is `bt` (vertical) → no E223."""
    # --- arrange / act ----------------
    codes = _codes(build_jsonl({"op": "theme", "commit_label_layout": "table"}))

    # --- assert -----------------------
    assert "E223" not in codes


def test_e223_attributed_to_the_layout_op_line() -> None:
    # --- arrange ----------------------
    text = build_jsonl(
        {"op": "branch", "name": "main"},
        {"op": "theme", "orientation": "lr"},
        {"op": "theme", "commit_label_layout": "table"},
    )

    # --- act --------------------------
    report = resolved_config_report(text)

    # --- assert -----------------------
    e223 = next(e for e in report.errors if e.code == "E223")
    assert e223.line == 3  # the op that set commit_label_layout
    assert e223.field == "commit_label_layout"


# ==================================================================================================
#  E224 — commit_label_layout: table × explicit commit_row_mode: shared
# ==================================================================================================
def test_table_with_explicit_shared_emits_e224() -> None:
    # --- arrange / act ----------------
    codes = _codes(build_jsonl({"op": "theme", "commit_label_layout": "table", "commit_row_mode": "shared"}))

    # --- assert -----------------------
    assert "E224" in codes


def test_table_with_explicit_unique_is_clean() -> None:
    # --- arrange / act ----------------
    codes = _codes(build_jsonl({"op": "theme", "commit_label_layout": "table", "commit_row_mode": "unique"}))

    # --- assert -----------------------
    assert "E224" not in codes


def test_table_without_row_mode_is_clean() -> None:
    """Leaving `commit_row_mode` unset is fine — table mode forces unique on its own."""
    # --- arrange / act ----------------
    codes = _codes(build_jsonl({"op": "theme", "commit_label_layout": "table"}))

    # --- assert -----------------------
    assert "E224" not in codes


def test_shared_without_table_mode_is_clean() -> None:
    """`commit_row_mode: shared` is only a conflict under table mode."""
    # --- arrange / act ----------------
    codes = _codes(build_jsonl({"op": "theme", "commit_row_mode": "shared"}))

    # --- assert -----------------------
    assert "E224" not in codes


def test_e224_attributed_to_the_row_mode_op_line() -> None:
    # --- arrange ----------------------
    text = build_jsonl({"op": "theme", "commit_label_layout": "table"}, {"op": "theme", "commit_row_mode": "shared"})

    # --- act --------------------------
    report = resolved_config_report(text)

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
        build_jsonl(
            {"op": "theme", "orientation": "lr", "commit_label_layout": "table"}, {"op": "theme", "name": "dark"}
        )  # default keep_prior_overrides=false → wipes table mode
    )

    # --- assert -----------------------
    assert "E223" not in codes
