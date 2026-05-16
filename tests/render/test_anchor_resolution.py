"""Tests for the per-element box-anchor resolution.

Verifies that each resolver returns the canonical `(u, v)` for every
orientation × `label_side` combination it covers. The expected values
mirror the per-orientation behaviour that previously lived inline in
each render primitive: vertical pills centred, horizontal branch pills
edge-anchored toward the start commit, commit labels anchored on the
side opposite their extension direction.
"""

import drawsvg as draw
import pytest

from gitsvg.render._anchor_resolution import (
    resolve_branch_pill_anchor,
    resolve_commit_label_anchor,
    resolve_pr_pill_anchor,
    rotated_target,
)


# ==================================================================================================
#  Branch pill
# ==================================================================================================
@pytest.mark.parametrize(
    ("orientation", "expected"),
    [
        ("bt", (0.5, 0.5)),
        ("tb", (0.5, 0.5)),
        ("lr", (1.0, 0.5)),
        ("rl", (0.0, 0.5)),
    ],
)
def test_resolve_branch_pill_anchor(orientation: str, expected: tuple[float, float]) -> None:
    # --- arrange / act ----------------
    result = resolve_branch_pill_anchor(orientation)  # type: ignore[arg-type]

    # --- assert -----------------------
    assert result == expected


# ==================================================================================================
#  PR pill
# ==================================================================================================
@pytest.mark.parametrize("orientation", ["bt", "tb", "lr", "rl"])
def test_resolve_pr_pill_anchor_always_centred(orientation: str) -> None:
    # --- arrange / act ----------------
    result = resolve_pr_pill_anchor(orientation)  # type: ignore[arg-type]

    # --- assert -----------------------
    assert result == (0.5, 0.5)


# ==================================================================================================
#  Commit label
# ==================================================================================================
@pytest.mark.parametrize(
    ("orientation", "label_side", "expected"),
    [
        # Vertical orientations: stack extends left/right of the dot,
        # vertically centred — u flips with label_side, v stays 0.5.
        ("bt", "before", (1.0, 0.5)),
        ("bt", "after", (0.0, 0.5)),
        ("tb", "before", (1.0, 0.5)),
        ("tb", "after", (0.0, 0.5)),
        # Horizontal orientations: stack extends above/below the dot,
        # horizontally centred — v flips with label_side, u stays 0.5.
        ("lr", "before", (0.5, 1.0)),
        ("lr", "after", (0.5, 0.0)),
        ("rl", "before", (0.5, 1.0)),
        ("rl", "after", (0.5, 0.0)),
    ],
)
def test_resolve_commit_label_anchor(orientation: str, label_side: str, expected: tuple[float, float]) -> None:
    # --- arrange / act ----------------
    result = resolve_commit_label_anchor(orientation, label_side)  # type: ignore[arg-type]

    # --- assert -----------------------
    assert result == expected


# ==================================================================================================
#  Rotation wrap
# ==================================================================================================
def test_rotated_target_at_zero_returns_target_unchanged() -> None:
    """At angle = 0 the helper must not emit a group, so the SVG stays
    byte-identical to the un-rotated path."""
    # --- arrange ----------------------
    d = draw.Drawing(100, 100)

    # --- act --------------------------
    result = rotated_target(d, angle=0, pivot_x=50, pivot_y=50)

    # --- assert -----------------------
    assert result is d
    assert d.elements == []


def test_rotated_target_at_zero_float_returns_target_unchanged() -> None:
    """Float-zero (the resolver's default) also skips the wrap."""
    # --- arrange ----------------------
    d = draw.Drawing(100, 100)

    # --- act --------------------------
    result = rotated_target(d, angle=0.0, pivot_x=50, pivot_y=50)

    # --- assert -----------------------
    assert result is d
    assert d.elements == []


def test_rotated_target_non_zero_returns_appended_group() -> None:
    # --- arrange ----------------------
    d = draw.Drawing(100, 100)

    # --- act --------------------------
    result = rotated_target(d, angle=45, pivot_x=50, pivot_y=70)

    # --- assert -----------------------
    assert isinstance(result, draw.Group)
    # The group is now a child of the drawing.
    assert d.elements == [result]


def test_rotated_target_transform_string_uses_pivot() -> None:
    """The emitted `<g transform="rotate(...)">` must carry the angle and the
    pivot pixel coordinates verbatim, so the world point stays fixed."""
    # --- arrange ----------------------
    d = draw.Drawing(100, 100)

    # --- act --------------------------
    group = rotated_target(d, angle=30, pivot_x=42.5, pivot_y=99)

    # --- assert -----------------------
    svg = d.as_svg()
    assert 'transform="rotate(30, 42.5, 99)"' in svg
    # Sanity: only one group element was added.
    assert svg.count("<g ") == 1
    # `group` returned by the helper is the one in the SVG.
    assert isinstance(group, draw.Group)
