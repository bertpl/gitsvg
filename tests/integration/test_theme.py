"""End-to-end validate + render test for the `theme:` op happy path.

Exercises the cascade rule against the full pipeline (parse → state →
layout → render): an explicit-overrides op, a second explicit op
patching one field, and the final SVG carrying the resolved values.
"""

from pathlib import Path

from gitsvg.layout import compute_layout
from gitsvg.parse import parse_jsonl_file, parse_jsonl_text
from gitsvg.render import render
from gitsvg.render._theme import build_theme
from gitsvg.state import apply_ops, check_end_of_file

_FIXTURE = Path(__file__).parent.parent / "fixtures" / "inputs" / "happy_theme.gitsvg.jsonl"


def test_happy_theme_fixture_validates_cleanly() -> None:
    # --- arrange ----------------------
    parsed, report = parse_jsonl_file(_FIXTURE)

    # --- act --------------------------
    state = apply_ops(parsed, report)
    check_end_of_file(state, report)

    # --- assert -----------------------
    assert report.is_clean(), [e.format() for e in report.errors]


def test_happy_theme_resolved_theme_carries_overrides_and_cascade() -> None:
    """The fixture sets background to #f5f5f0 first, then patches it to
    #fffaf0 — final state should hold the latter; the earlier
    label_font_size override should survive (different field)."""
    # --- arrange ----------------------
    parsed, report = parse_jsonl_file(_FIXTURE)
    state = apply_ops(parsed, report)
    check_end_of_file(state, report)
    assert report.is_clean()

    # --- act --------------------------
    theme = build_theme(state)

    # --- assert -----------------------
    assert theme.background_color == "#fffaf0"
    assert theme.label_font_size == 13
    assert theme.branch_spacing == 120


def test_happy_theme_renders_with_background_rect() -> None:
    # --- arrange ----------------------
    parsed, report = parse_jsonl_file(_FIXTURE)
    state = apply_ops(parsed, report)
    check_end_of_file(state, report)

    # --- act --------------------------
    theme = build_theme(state)
    svg = render(compute_layout(state), theme).as_svg()

    # --- assert -----------------------
    assert 'fill="#fffaf0"' in svg
    assert 'font-size="13"' in svg
    # The background rect is the first SVG element after the root.
    bg_pos = svg.index('fill="#fffaf0"')
    first_branch_pos = svg.index("<path")
    assert bg_pos < first_branch_pos


def test_theme_op_then_canvas_op_canvas_wins_for_spacing() -> None:
    """A `canvas:` op specifying spacing wins over a theme op — the
    `build_theme` adapter folds `state.canvas` on top of `state.theme`."""
    # --- arrange ----------------------
    text = (
        '{"op": "theme", "branch_spacing": 80}\n'
        '{"op": "canvas", "branch_spacing": 60}\n'
        '{"op": "branch", "name": "main"}\n'
    )
    parsed, report = parse_jsonl_text(text, file="x.jsonl")
    state = apply_ops(parsed, report)

    # --- act --------------------------
    assert report.is_clean()
    theme = build_theme(state)

    # --- assert -----------------------
    # canvas op (specific) beats theme op (general).
    assert theme.branch_spacing == 60
