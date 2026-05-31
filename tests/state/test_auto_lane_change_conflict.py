"""E221 — `branch_pos` pin conflicts with `theme.auto_lane_change`.

The check runs at the `apply_ops` orchestration point, where both the
resolved theme (the flag) and the state (per-branch pins) are known.
"""

from gitsvg.parse import parse_jsonl_text
from gitsvg.state import apply_ops


def _codes(text: str) -> list[str]:
    """Parse + apply `text`, returning the emitted error codes."""
    parsed, report = parse_jsonl_text(text, file="x.jsonl")
    apply_ops(parsed, report)
    return [e.code for e in report.errors]


def test_pin_with_auto_lane_change_emits_e221() -> None:
    # --- arrange / act ----------------
    codes = _codes(
        '{"op": "theme", "auto_lane_change": true}\n'
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main", "branch_pos": 3}\n'
    )

    # --- assert -----------------------
    assert "E221" in codes


def test_pin_without_auto_lane_change_is_clean() -> None:
    # --- arrange / act ----------------
    codes = _codes(
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main", "branch_pos": 3}\n'
    )

    # --- assert -----------------------
    assert "E221" not in codes


def test_auto_lane_change_without_pin_is_clean() -> None:
    # --- arrange / act ----------------
    codes = _codes(
        '{"op": "theme", "auto_lane_change": true}\n'
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
    )

    # --- assert -----------------------
    assert "E221" not in codes


def test_e221_attributed_to_the_pinned_branch_line() -> None:
    """The error points at the `branch:` op that set the pin, not the `theme:` op."""
    # --- arrange ----------------------
    text = (
        '{"op": "theme", "auto_lane_change": true}\n'
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main", "branch_pos": 3}\n'
    )

    # --- act --------------------------
    parsed, report = parse_jsonl_text(text, file="x.jsonl")
    apply_ops(parsed, report)

    # --- assert -----------------------
    e221 = next(e for e in report.errors if e.code == "E221")
    assert e221.line == 4  # the pinned `branch:` op
    assert e221.field == "branch_pos"
