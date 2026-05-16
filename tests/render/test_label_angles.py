"""Tests for the three label-angle theme fields and their rotation transform.

Default output (every angle field unset → resolver fills 0°) is covered
by the byte-identical example diffs that gate the refactor PR; the
tests here cover the activation path: setting a non-zero angle emits
a `<g transform="rotate(angle, wx, wy)">` wrap around the relevant
primitive, with the world anchor point as the rotation pivot.
"""

import re

import pytest

from gitsvg.layout import compute_layout
from gitsvg.parse import parse_jsonl_text
from gitsvg.render import render
from gitsvg.state import apply_ops


def _render_from(text: str) -> str:
    """Run the full validate + layout + render pipeline and return the SVG."""
    parsed, report = parse_jsonl_text(text, file="x.jsonl")
    state, theme = apply_ops(parsed, report)
    layout = compute_layout(state)
    return render(layout, theme).as_svg()


_ROTATE_RE = re.compile(r'transform="rotate\(([^,]+), ([^,]+), ([^)]+)\)"')


# ==================================================================================================
#  Default — no rotation transforms emitted at 0°
# ==================================================================================================
def test_default_render_emits_no_rotate_transform() -> None:
    """Byte-identical gate at default: no label-angle override, every
    angle resolves to 0°, no rotation group emitted anywhere."""
    # --- arrange ----------------------
    text = '{"op": "branch", "name": "main"}\n{"op": "commit", "branch": "main", "id": "c1", "msg": "init"}\n'

    # --- act --------------------------
    svg = _render_from(text)

    # --- assert -----------------------
    assert "rotate(" not in svg


# ==================================================================================================
#  Per-field activation — each angle field wraps the right primitive
# ==================================================================================================
def test_branch_label_angle_wraps_branch_pill() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "theme", "branch_label_angle": 30}\n'
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "init"}\n'
    )

    # --- act --------------------------
    svg = _render_from(text)

    # --- assert -----------------------
    matches = _ROTATE_RE.findall(svg)
    # Exactly one rotation group — the branch pill (only branch in the fixture).
    # Commit label is not rotated (commit_label_angle stays at the default 0°).
    assert len(matches) == 1
    angle, _, _ = matches[0]
    assert float(angle) == 30


def test_commit_label_angle_wraps_commit_label() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "theme", "commit_label_angle": -45}\n'
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "init"}\n'
        '{"op": "commit", "branch": "main", "id": "c2", "msg": "next"}\n'
    )

    # --- act --------------------------
    svg = _render_from(text)

    # --- assert -----------------------
    matches = _ROTATE_RE.findall(svg)
    # Two commits → two commit-label rotation groups (one per labelled commit).
    # Branch pill is not rotated.
    assert len(matches) == 2
    for angle, _, _ in matches:
        assert float(angle) == -45


def test_pull_request_label_angle_wraps_pr_pill() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "theme", "pull_request_label_angle": 60}\n'
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "init"}\n'
        '{"op": "branch", "name": "feature", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "feature", "id": "c2", "msg": "work"}\n'
        '{"op": "pull_request", "id": "pr1", "from": "feature", "into": "main", "title": "merge feature"}\n'
    )

    # --- act --------------------------
    svg = _render_from(text)

    # --- assert -----------------------
    matches = _ROTATE_RE.findall(svg)
    # Exactly one rotation group — the PR pill. Branch pills (2) and commit
    # labels (2) all stay un-rotated.
    assert len(matches) == 1
    angle, _, _ = matches[0]
    assert float(angle) == 60


# ==================================================================================================
#  Multiple fields together — each primitive uses its own angle
# ==================================================================================================
def test_independent_angles_per_label_kind() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "theme", "branch_label_angle": 10, "commit_label_angle": 20}\n'
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "init"}\n'
    )

    # --- act --------------------------
    svg = _render_from(text)

    # --- assert -----------------------
    angles = {float(angle) for angle, _, _ in _ROTATE_RE.findall(svg)}
    assert angles == {10.0, 20.0}


# ==================================================================================================
#  Pivot is the world anchor point — combined orientation + angle
# ==================================================================================================
@pytest.mark.parametrize("orientation", ["bt", "tb", "lr", "rl"])
def test_rotation_pivot_matches_branch_pill_world_point(orientation: str) -> None:
    """When `branch_label_angle` is set, the rotation pivot is the pill's
    world anchor point — `(wx, wy) = pill_rect_top_left + (u*width, v*height)` — so
    the box anchor stays pinned regardless of orientation. We back this out
    by checking the rotate(angle, px, py) pivot lands on the rect edge /
    centre that the `BoxAnchor` resolves to."""
    # --- arrange ----------------------
    text = (
        f'{{"op": "theme", "orientation": "{orientation}", "branch_label_angle": 45}}\n'
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "init"}\n'
    )

    # --- act --------------------------
    svg = _render_from(text)

    # --- assert -----------------------
    rotate_matches = _ROTATE_RE.findall(svg)
    assert len(rotate_matches) == 1
    _, pivot_x_str, pivot_y_str = rotate_matches[0]
    pivot_x = float(pivot_x_str)
    pivot_y = float(pivot_y_str)

    # Pull the pill rect coords + dimensions to verify pivot lands at the
    # resolved `(u, v)` of the rect.
    rect_match = re.search(r'<rect x="([^"]+)" y="([^"]+)" width="([^"]+)" height="([^"]+)"', svg)
    assert rect_match is not None
    rect_x = float(rect_match.group(1))
    rect_y = float(rect_match.group(2))
    rect_w = float(rect_match.group(3))
    rect_h = float(rect_match.group(4))

    # `BoxAnchor` per orientation: BT/TB centred (0.5, 0.5); LR right-edge
    # anchored (1.0, 0.5); RL left-edge anchored (0.0, 0.5).
    if orientation == "lr":
        expected_u = 1.0
    elif orientation == "rl":
        expected_u = 0.0
    else:
        expected_u = 0.5
    expected_pivot_x = rect_x + expected_u * rect_w
    expected_pivot_y = rect_y + 0.5 * rect_h

    assert pivot_x == pytest.approx(expected_pivot_x)
    assert pivot_y == pytest.approx(expected_pivot_y)


def test_rotation_pivot_for_commit_label_at_non_default_orientation() -> None:
    """LR orientation with a non-zero `commit_label_angle` — the rotation
    pivot must land at the commit dot's world position (with the resolved
    label offset along the branch axis), independent of the angle value."""
    # --- arrange ----------------------
    # Two commits to keep the pill out of the same area as the commit label.
    base_text = (
        '{"op": "theme", "orientation": "lr"}\n'
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "c2", "msg": "y"}\n'
    )

    # --- act --------------------------
    # Render twice with different angles; pivot should be invariant.
    text_30 = base_text.replace(
        '{"op": "theme", "orientation": "lr"}',
        '{"op": "theme", "orientation": "lr", "commit_label_angle": 30}',
    )
    text_60 = base_text.replace(
        '{"op": "theme", "orientation": "lr"}',
        '{"op": "theme", "orientation": "lr", "commit_label_angle": 60}',
    )
    svg_30 = _render_from(text_30)
    svg_60 = _render_from(text_60)

    # --- assert -----------------------
    pivots_30 = [(px, py) for _, px, py in _ROTATE_RE.findall(svg_30)]
    pivots_60 = [(px, py) for _, px, py in _ROTATE_RE.findall(svg_60)]
    # Same number of rotated commit labels in both renders.
    assert len(pivots_30) == len(pivots_60) == 2
    # Same pivot coordinates regardless of angle — the world point is invariant.
    assert pivots_30 == pivots_60
