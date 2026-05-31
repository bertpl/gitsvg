"""E222 — `merge_lane_clearance` set while `auto_lane_change` is off.

The check runs at the `apply_ops` orchestration point, where the
resolved theme (the flag) and the explicit user overrides (the field +
its originating line) are both known. Because it checks the *final*
resolved state, a named-theme switch that wipes prior overrides is the
documented escape hatch.
"""

from gitsvg.parse import parse_jsonl_text
from gitsvg.state import apply_ops


def _codes(text: str) -> list[str]:
    """Parse + apply `text`, returning the emitted error codes."""
    parsed, report = parse_jsonl_text(text, file="x.jsonl")
    apply_ops(parsed, report)
    return [e.code for e in report.errors]


def test_clearance_without_auto_lane_change_emits_e222() -> None:
    # --- arrange / act ----------------
    codes = _codes('{"op": "theme", "merge_lane_clearance": 2}\n')

    # --- assert -----------------------
    assert "E222" in codes


def test_default_value_clearance_still_emits_e222() -> None:
    """Setting the field to its default `1` is still the mistake — explicit but inert."""
    # --- arrange / act ----------------
    codes = _codes('{"op": "theme", "merge_lane_clearance": 1}\n')

    # --- assert -----------------------
    assert "E222" in codes


def test_clearance_with_auto_lane_change_is_clean() -> None:
    # --- arrange / act ----------------
    codes = _codes('{"op": "theme", "auto_lane_change": true, "merge_lane_clearance": 2}\n')

    # --- assert -----------------------
    assert "E222" not in codes


def test_no_clearance_set_is_clean() -> None:
    # --- arrange / act ----------------
    codes = _codes('{"op": "theme", "auto_lane_change": false}\n')

    # --- assert -----------------------
    assert "E222" not in codes


def test_e222_attributed_to_the_setting_op_line() -> None:
    """The error points at the `theme:` op that set the field, not the diagram start."""
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "theme", "merge_lane_clearance": 2}\n'
    )

    # --- act --------------------------
    parsed, report = parse_jsonl_text(text, file="x.jsonl")
    apply_ops(parsed, report)

    # --- assert -----------------------
    e222 = next(e for e in report.errors if e.code == "E222")
    assert e222.line == 3  # the `theme:` op that set the field
    assert e222.field == "merge_lane_clearance"


# ==================================================================================================
#  Named-theme escape hatch
# ==================================================================================================
def test_named_theme_switch_wipes_clearance_and_clears_e222() -> None:
    """A later named-theme switch (default wipe) drops the override → no E222."""
    # --- arrange / act ----------------
    codes = _codes(
        '{"op": "theme", "merge_lane_clearance": 2}\n'
        '{"op": "theme", "name": "dark"}\n'  # default keep_prior_overrides=false → wipe
    )

    # --- assert -----------------------
    assert "E222" not in codes


def test_keep_prior_overrides_preserves_clearance_and_keeps_e222() -> None:
    """`keep_prior_overrides: true` preserves the override → E222 still fires."""
    # --- arrange ----------------------
    text = '{"op": "theme", "merge_lane_clearance": 2}\n{"op": "theme", "name": "dark", "keep_prior_overrides": true}\n'

    # --- act --------------------------
    parsed, report = parse_jsonl_text(text, file="x.jsonl")
    apply_ops(parsed, report)

    # --- assert -----------------------
    e222 = next(e for e in report.errors if e.code == "E222")
    assert e222.line == 1  # provenance survives the switch, still points at the setting op
