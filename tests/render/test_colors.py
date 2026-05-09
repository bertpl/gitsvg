"""Tests for branch colour resolution — explicit override + default cycle."""

from gitsvg.parse import parse_jsonl_text
from gitsvg.render._colors import resolve_branch_color
from gitsvg.render._constants import COLORS, DEFAULT_BRANCH_COLORS
from gitsvg.state import apply_ops


def _state_from(text: str):
    parsed, report = parse_jsonl_text(text, file="x.jsonl")
    return apply_ops(parsed, report)


def test_explicit_color_is_used_verbatim() -> None:
    # --- arrange ----------------------
    state = _state_from('{"op": "branch", "name": "main", "color": "#abcdef"}\n')

    # --- act / assert -----------------
    assert resolve_branch_color(state, "main") == "#abcdef"


def test_first_declared_branch_defaults_to_main_color() -> None:
    # --- arrange ----------------------
    state = _state_from('{"op": "branch", "name": "main"}\n')

    # --- act / assert -----------------
    assert resolve_branch_color(state, "main") == COLORS["main"]


def test_subsequent_branches_cycle_through_default_palette() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "branch", "name": "feat-1", "from_branch": "main"}\n'
        '{"op": "branch", "name": "feat-2", "from_branch": "main"}\n'
        '{"op": "branch", "name": "feat-3", "from_branch": "main"}\n'
        '{"op": "branch", "name": "feat-4", "from_branch": "main"}\n'
    )
    state = _state_from(text)

    # --- act / assert -----------------
    assert resolve_branch_color(state, "feat-1") == COLORS[DEFAULT_BRANCH_COLORS[0]]
    assert resolve_branch_color(state, "feat-2") == COLORS[DEFAULT_BRANCH_COLORS[1]]
    assert resolve_branch_color(state, "feat-3") == COLORS[DEFAULT_BRANCH_COLORS[2]]
    assert resolve_branch_color(state, "feat-4") == COLORS[DEFAULT_BRANCH_COLORS[3]]


def test_fifth_non_main_branch_wraps_back_to_palette_start() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "branch", "name": "b1", "from_branch": "main"}\n'
        '{"op": "branch", "name": "b2", "from_branch": "main"}\n'
        '{"op": "branch", "name": "b3", "from_branch": "main"}\n'
        '{"op": "branch", "name": "b4", "from_branch": "main"}\n'
        '{"op": "branch", "name": "b5", "from_branch": "main"}\n'
    )
    state = _state_from(text)

    # --- act / assert -----------------
    assert resolve_branch_color(state, "b5") == COLORS[DEFAULT_BRANCH_COLORS[0]]
