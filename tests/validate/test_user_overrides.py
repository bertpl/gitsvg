"""Tests for `UserOverrides.collect` — what the input set, lifted off state + builder."""

from gitsvg.parse import parse_jsonl_text
from gitsvg.state import apply_ops
from gitsvg.theme import ThemeBuilder
from gitsvg.validate import UserOverrides


def _collect(jsonl: str) -> UserOverrides:
    """Parse + apply `jsonl` with a fresh builder, then collect the overrides."""
    parsed, report = parse_jsonl_text(jsonl, file="x.jsonl")
    builder = ThemeBuilder()
    state, _theme = apply_ops(parsed, report, builder=builder)
    return UserOverrides.collect(state, builder)


def test_collect_captures_set_theme_field_value_and_line() -> None:
    # --- arrange / act ----------------
    overrides = _collect('{"op": "theme", "merge_lane_clearance": 2}\n')

    # --- assert -----------------------
    entry = overrides.theme_fields["merge_lane_clearance"]
    assert entry.value == 2
    assert entry.file == "x.jsonl"
    assert entry.line == 1


def test_collect_omits_unset_theme_fields() -> None:
    # --- arrange / act ----------------
    overrides = _collect('{"op": "branch", "name": "main"}\n')

    # --- assert -----------------------
    assert overrides.theme_fields == {}


def test_collect_captures_branch_pin_name_and_line() -> None:
    # --- arrange / act ----------------
    overrides = _collect(
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main", "branch_pos": 3}\n'
    )

    # --- assert -----------------------
    assert len(overrides.branch_pins) == 1
    pin = overrides.branch_pins[0]
    assert pin.name == "feat"
    assert pin.file == "x.jsonl"
    assert pin.line == 3


def test_collect_omits_unpinned_branches() -> None:
    # --- arrange / act ----------------
    overrides = _collect('{"op": "branch", "name": "main"}\n')

    # --- assert -----------------------
    assert overrides.branch_pins == ()
