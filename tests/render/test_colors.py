"""Tests for the renderer-side branch-color resolver."""

from gitsvg.parse import parse_jsonl_text
from gitsvg.render._colors import resolve_branch_color
from gitsvg.state import apply_ops
from gitsvg.theme import DEFAULT_THEME, Theme


def _state_theme_from(text: str):
    parsed, report = parse_jsonl_text(text, file="x.jsonl")
    return apply_ops(parsed, report)


# ==================================================================================================
#  Default cycle — first branch = `main`, then cycle palette
# ==================================================================================================
def test_first_branch_resolves_to_main_palette_color() -> None:
    # --- arrange / act / assert -------
    assert resolve_branch_color("b0", declaration_index=0, theme=DEFAULT_THEME) == DEFAULT_THEME.colors["main"]


def test_subsequent_branches_cycle_through_default_palette() -> None:
    # --- arrange ----------------------
    theme = DEFAULT_THEME
    cycle = theme.default_branch_color_cycle

    # --- act / assert -----------------
    assert resolve_branch_color("b1", declaration_index=1, theme=theme) == theme.colors[cycle[0]]
    assert resolve_branch_color("b2", declaration_index=2, theme=theme) == theme.colors[cycle[1]]
    assert resolve_branch_color("b3", declaration_index=3, theme=theme) == theme.colors[cycle[2]]
    assert resolve_branch_color("b4", declaration_index=4, theme=theme) == theme.colors[cycle[3]]
    # Wrap around.
    assert resolve_branch_color("b5", declaration_index=5, theme=theme) == theme.colors[cycle[0]]


# ==================================================================================================
#  Explicit override on the theme
# ==================================================================================================
def test_explicit_override_takes_precedence_over_cycle() -> None:
    # --- arrange ----------------------
    theme = Theme(branch_color_overrides={"b2": "#abcdef"})

    # --- act / assert -----------------
    assert resolve_branch_color("b2", declaration_index=5, theme=theme) == "#abcdef"


def test_override_uses_branch_id_not_name() -> None:
    """The resolver keys on `branch_id`, never on the branch name —
    important for the rebase-rebuild pattern (same name, fresh id)."""
    # --- arrange ----------------------
    state, theme = _state_theme_from(
        '{"op": "branch", "name": "main"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main", "color": "#111111"}\n'
        '{"op": "remove", "branches": ["feat"]}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
    )

    # --- act --------------------------
    live_feat = state.branches["feat"]
    resolved = resolve_branch_color(live_feat.id, declaration_index=1, theme=theme)

    # --- assert -----------------------
    # The redeclared `feat` has no color override, so it falls back to the
    # cycle — *not* the removed branch's "#111111".
    assert resolved != "#111111"
    assert resolved == theme.colors[theme.default_branch_color_cycle[0]]
