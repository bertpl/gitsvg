"""End-to-end tests: each non-default orientation renders cleanly + canvas swap."""

import pytest

from gitsvg.layout import compute_layout
from gitsvg.parse import parse_jsonl_text
from gitsvg.render import render
from gitsvg.render._canvas import compute_canvas
from gitsvg.state import apply_ops


def _render_with_orientation(orientation: str):
    """Apply a small fixture under the given orientation; return (svg, canvas)."""
    text = (
        f'{{"op": "theme", "orientation": "{orientation}"}}\n'
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "init"}\n'
        '{"op": "commit", "branch": "main", "id": "c2", "msg": "next"}\n'
        '{"op": "branch", "name": "feature", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "feature", "id": "c3", "msg": "work"}\n'
        '{"op": "merge", "into": "main", "from": "feature"}\n'
    )
    parsed, report = parse_jsonl_text(text, file="x.jsonl")
    state, theme = apply_ops(parsed, report)
    layout = compute_layout(state)
    canvas = compute_canvas(layout, theme)
    drawing = render(layout, theme)
    return drawing.as_svg(), canvas


@pytest.mark.parametrize("orientation", ["bt", "tb", "lr", "rl"])
def test_each_orientation_renders_without_error(orientation: str) -> None:
    # --- arrange / act / assert -------
    svg, _ = _render_with_orientation(orientation)
    # Sanity: the SVG opens with the expected XML/svg header.
    assert svg.startswith("<?xml")
    assert "<svg" in svg


def test_lr_swaps_canvas_dimensions_relative_to_bt() -> None:
    """In LR, the commit axis maps to width and the branch axis to height
    — the opposite of BT. The fixture has more commits (4) than branches
    (2), so LR should be wider and shorter than BT (the spacings also
    swap per orientation, amplifying the effect)."""
    # --- arrange / act ----------------
    _, canvas_bt = _render_with_orientation("bt")
    _, canvas_lr = _render_with_orientation("lr")

    # --- assert -----------------------
    # LR is wider (commits drive width with the larger LR commit_spacing).
    assert canvas_lr.width > canvas_bt.width
    # LR is shorter (branches drive height with the smaller LR branch_spacing).
    assert canvas_lr.height < canvas_bt.height
    # Sanity: orientation field is propagated to RenderCanvas.
    assert canvas_bt.orientation == "bt"
    assert canvas_lr.orientation == "lr"


def test_tb_canvas_dimensions_match_bt() -> None:
    """TB and BT both stack branches horizontally; canvas dimensions match."""
    # --- arrange / act ----------------
    _, canvas_bt = _render_with_orientation("bt")
    _, canvas_tb = _render_with_orientation("tb")

    # --- assert -----------------------
    assert canvas_bt.width == canvas_tb.width
    assert canvas_bt.height == canvas_tb.height


def test_rl_canvas_dimensions_match_lr() -> None:
    """RL and LR both stack branches vertically; canvas dimensions match."""
    # --- arrange / act ----------------
    _, canvas_lr = _render_with_orientation("lr")
    _, canvas_rl = _render_with_orientation("rl")

    # --- assert -----------------------
    assert canvas_lr.width == canvas_rl.width
    assert canvas_lr.height == canvas_rl.height
