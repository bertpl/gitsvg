"""Tests for the branch-line primitive."""

import re

import drawsvg as draw

from gitsvg._theme import DEFAULT_THEME
from gitsvg.layout import LayoutBranch, compute_layout
from gitsvg.parse import parse_jsonl_text
from gitsvg.render import render
from gitsvg.render._canvas import RenderCanvas
from gitsvg.render._primitives._branch_line import draw_branch_line
from gitsvg.state import apply_ops


# ==================================================================================================
#  Direct primitive test — empty branch (start == end) emits nothing
# ==================================================================================================
def _canvas() -> RenderCanvas:
    """Return a minimal `RenderCanvas` sufficient for the geometry transform."""
    return RenderCanvas(
        width=200,
        height=200,
        n_commits=3,
        n_branches=2,
        branch_spacing=100,
        commit_spacing=50,
        margin_branch_axis_lower=100,
        margin_branch_axis_upper=100,
        margin_commit_axis_lower=25,
        margin_commit_axis_upper=25,
    )


def test_empty_branch_emits_no_line() -> None:
    """A branch with `start == end` produces no `<line>`/`<path>` in the drawing."""
    # --- arrange ----------------------
    d = draw.Drawing(200, 200)
    empty_branch = LayoutBranch(
        id="b1",
        name="lonely",
        branch_pos=1,
        start=2,
        end=2,
        label_side="right",
    )

    # --- act --------------------------
    draw_branch_line(d, empty_branch, "#000000", _canvas(), DEFAULT_THEME)
    svg = d.as_svg()

    # --- assert -----------------------
    # No `<line>`/`<path>` element produced for this branch's line.
    assert "<line" not in svg
    assert "<path" not in svg


def test_non_empty_branch_emits_a_line() -> None:
    """Sanity check: a branch with `start != end` still produces a line."""
    # --- arrange ----------------------
    d = draw.Drawing(200, 200)
    branch = LayoutBranch(
        id="b1",
        name="b",
        branch_pos=1,
        start=0,
        end=2,
        label_side="right",
    )

    # --- act --------------------------
    draw_branch_line(d, branch, "#000000", _canvas(), DEFAULT_THEME)
    svg = d.as_svg()

    # --- assert -----------------------
    # drawsvg renders `Line` as a `<path>` with `M x1,y1 L x2,y2`.
    assert "<path" in svg


# ==================================================================================================
#  End-to-end — degenerate paths absent from rendered output
# ==================================================================================================
def _render(text: str) -> str:
    """Parse → state → layout → render → SVG string."""
    parsed, report = parse_jsonl_text(text, file="x.jsonl")
    state = apply_ops(parsed, report)
    return render(compute_layout(state)).as_svg()


def test_diagram_with_empty_branches_emits_no_zero_length_paths() -> None:
    """Empty branches (declared but no commits) don't add zero-length `<path>` elements."""
    # --- arrange / act ----------------
    svg = _render(
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
        '{"op": "branch", "name": "scratch", "from_branch": "main"}\n'
    )

    # --- assert -----------------------
    # Any `<path>` of the form `M x,y L x,y` (same start and end) would
    # be a zero-length line. None should appear.
    zero_length = re.findall(r'd="M([^"]*?) L\1"', svg)
    assert zero_length == []
