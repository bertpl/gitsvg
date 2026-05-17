"""End-to-end validate + render test for the `theme:` op happy path.

Exercises the cascade rule against the full pipeline (parse → state →
layout → render): an explicit-overrides op, a second explicit op
patching one field, and the final SVG carrying the resolved values.
"""

from pathlib import Path

from gitsvg.layout import compute_layout
from gitsvg.parse import parse_jsonl_file, parse_jsonl_text
from gitsvg.render import render
from gitsvg.state import apply_ops, check_end_of_file

_FIXTURE = Path(__file__).parent.parent / "fixtures" / "inputs" / "happy_theme.gitsvg.jsonl"


def test_happy_theme_fixture_validates_cleanly() -> None:
    # --- arrange ----------------------
    parsed, report = parse_jsonl_file(_FIXTURE)

    # --- act --------------------------
    state, _theme = apply_ops(parsed, report)
    check_end_of_file(state, report)

    # --- assert -----------------------
    assert report.is_clean(), [e.format() for e in report.errors]


def test_happy_theme_resolved_theme_carries_overrides_and_cascade() -> None:
    """The fixture sets background to #f5f5f0 first, then patches it to
    #fffaf0 — final state should hold the latter; the earlier
    label_font_size override should survive (different field)."""
    # --- arrange / act ----------------
    parsed, report = parse_jsonl_file(_FIXTURE)
    state, theme = apply_ops(parsed, report)
    check_end_of_file(state, report)
    assert report.is_clean()

    # --- assert -----------------------
    assert theme.background_color == "#fffaf0"
    assert theme.label_font_size == 13
    assert theme.branch_spacing == 120


def test_happy_theme_renders_with_background_rect() -> None:
    # --- arrange ----------------------
    parsed, report = parse_jsonl_file(_FIXTURE)
    state, theme = apply_ops(parsed, report)
    check_end_of_file(state, report)

    # --- act --------------------------
    svg = render(compute_layout(state), theme).as_svg()

    # --- assert -----------------------
    assert 'fill="#fffaf0"' in svg
    # Font-size fields are typed `float`, so values render with a trailing `.0`.
    assert 'font-size="13.0"' in svg
    # The background rect is the first SVG element after the root.
    bg_pos = svg.index('fill="#fffaf0"')
    first_branch_pos = svg.index("<path")
    assert bg_pos < first_branch_pos
