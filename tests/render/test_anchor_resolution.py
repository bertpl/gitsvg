"""Tests for per-element box-anchor resolution + the rotation-wrap helper.

The per-orientation anchor defaults now live as `_resolve_*_anchor`
classmethods on `DefaultTheme` (post v0.1.9 anchor graduation); the
expected values reproduce v0.1.8's table — vertical pills centered,
horizontal branch pills edge-anchored toward the start commit,
commit labels anchored on the side opposite their extension direction.

The rotation-wrap helper (`rotated_target`) stays in
`gitsvg/render/_anchor_resolution.py`.
"""

import drawsvg as draw
import pytest

from gitsvg.render._anchor_resolution import rotated_target
from gitsvg.theme import DefaultTheme, Orientation


# ==================================================================================================
#  Branch pill anchor (DefaultTheme classmethod)
# ==================================================================================================
@pytest.mark.parametrize(
    ("orientation", "expected"),
    [
        (Orientation.BT, (0.5, 0.5)),
        (Orientation.TB, (0.5, 0.5)),
        (Orientation.LR, (1.0, 0.5)),
        (Orientation.RL, (0.0, 0.5)),
    ],
)
def test_default_theme_resolves_branch_pill_anchor(orientation: Orientation, expected: tuple[float, float]) -> None:
    # --- arrange / act ----------------
    result = DefaultTheme._resolve_branch_pill_anchor(orientation)

    # --- assert -----------------------
    assert result == expected


# ==================================================================================================
#  PR pill anchor (always centered)
# ==================================================================================================
@pytest.mark.parametrize("orientation", [Orientation.BT, Orientation.TB, Orientation.LR, Orientation.RL])
def test_default_theme_resolves_pr_pill_anchor_always_centered(orientation: Orientation) -> None:
    # --- arrange / act ----------------
    result = DefaultTheme._resolve_pull_request_pill_anchor(orientation)

    # --- assert -----------------------
    assert result == (0.5, 0.5)


# ==================================================================================================
#  Commit label anchor — per-side split
# ==================================================================================================
@pytest.mark.parametrize(
    ("orientation", "expected"),
    [
        (Orientation.BT, (1.0, 0.5)),
        (Orientation.TB, (1.0, 0.5)),
        (Orientation.LR, (0.5, 1.0)),
        (Orientation.RL, (0.5, 1.0)),
    ],
)
def test_default_theme_resolves_commit_label_anchor_before(
    orientation: Orientation, expected: tuple[float, float]
) -> None:
    # --- arrange / act ----------------
    result = DefaultTheme._resolve_commit_label_anchor_before(orientation)

    # --- assert -----------------------
    assert result == expected


@pytest.mark.parametrize(
    ("orientation", "expected"),
    [
        (Orientation.BT, (0.0, 0.5)),
        (Orientation.TB, (0.0, 0.5)),
        (Orientation.LR, (0.5, 0.0)),
        (Orientation.RL, (0.5, 0.0)),
    ],
)
def test_default_theme_resolves_commit_label_anchor_after(
    orientation: Orientation, expected: tuple[float, float]
) -> None:
    # --- arrange / act ----------------
    result = DefaultTheme._resolve_commit_label_anchor_after(orientation)

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
