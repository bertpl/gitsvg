"""Tests for the connector style builders and their orientation coverage.

Builder-level: each `_build_<style>` emits the expected path commands for a
representative connector. End-to-end: every (orientation, style) pair
renders cleanly.
"""

import drawsvg as draw
import pytest

from gitsvg.layout import compute_layout
from gitsvg.parse import parse_jsonl_text
from gitsvg.render import render
from gitsvg.render._primitives._connector_styles import (
    _build_bezier,
    _build_double_rounded,
    _build_rounded,
    _build_straight,
    _ConnectorGeometry,
)
from gitsvg.state import apply_ops
from gitsvg.theme import BranchLineStyle

# A representative non-degenerate connector: one lane and one row apart.
_GEOM = _ConnectorGeometry(
    x1=0.0,
    y1=0.0,
    x2=100.0,
    y2=50.0,
    dx=1,
    dy=1,
    corner_radius=20.0,
    screen_y_first=False,
    commit_axis_vertical=True,
    trunk_is_start=True,
)


def _path_d(builder, geom: _ConnectorGeometry) -> str:
    """Run `builder` on a fresh path and return its `d` string (the builder opens it)."""
    path = draw.Path()
    builder(path, geom)
    return path.args["d"]


# ==================================================================================================
#  Builder-level — each style emits its characteristic commands
# ==================================================================================================
def test_straight_emits_a_line_and_no_curve() -> None:
    # --- act --------------------------
    d = _path_d(_build_straight, _GEOM)

    # --- assert -----------------------
    assert "L" in d
    assert "A" not in d and "C" not in d


def test_rounded_emits_one_quarter_arc() -> None:
    # --- act --------------------------
    d = _path_d(_build_rounded, _GEOM)

    # --- assert -----------------------
    assert d.count("A") == 1


def test_bezier_emits_a_cubic_curve() -> None:
    # --- act --------------------------
    d = _path_d(_build_bezier, _GEOM)

    # --- assert -----------------------
    assert "C" in d


def test_double_rounded_emits_two_arcs() -> None:
    # --- act --------------------------
    d = _path_d(_build_double_rounded, _GEOM)

    # --- assert -----------------------
    assert d.count("A") == 2


# ==================================================================================================
#  End-to-end — every (orientation, style) pair renders cleanly
# ==================================================================================================
@pytest.mark.parametrize("orientation", ["bt", "tb", "lr", "rl"])
@pytest.mark.parametrize("style", [s.value for s in BranchLineStyle])
def test_renders_in_every_orientation_and_style(orientation: str, style: str) -> None:
    # --- arrange ----------------------
    jsonl = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "feat", "id": "f1", "msg": "y"}\n'
        '{"op": "merge", "from": "feat", "into": "main", "as": "mg"}\n'
        f'{{"op": "theme", "orientation": "{orientation}", "branch_line_style": "{style}"}}\n'
    )
    parsed, report = parse_jsonl_text(jsonl, file="x.jsonl")
    state, theme = apply_ops(parsed, report)
    assert report.is_clean(), f"{orientation}/{style}: unexpected validation errors"

    # --- act --------------------------
    svg = render(compute_layout(state), theme).as_svg()

    # --- assert -----------------------
    assert "<path" in svg  # the branch-off and merge connectors rendered
