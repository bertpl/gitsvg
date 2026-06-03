"""Tests for orientation alias parsing + per-orientation default resolution.

Covers:
- The 13-entry alias table on `theme.orientation` (case-insensitive,
  `-`/`_` interchangeable, accepts Mermaid `TD`, CSS `ltr`/`rtl`,
  vernacular `top_down`/`bottom_up`).
- Rejection of non-canonical inputs (camelCase, malformed underscores,
  unknown short codes).
- The default-resolution helper's per-orientation outputs for the 10
  resolved fields (2 spacings, 4 margins, 4 pill offsets).
"""

import pytest
from pydantic import ValidationError

from gitsvg._shared.value_types import Orientation
from gitsvg.file_format.ops.impl._theme import ThemeOp
from gitsvg.theme import DefaultTheme


# ==================================================================================================
#  Alias parsing on `ThemeOp.orientation`
# ==================================================================================================
@pytest.mark.parametrize(
    ("user_input", "expected_canonical"),
    [
        # Canonical short codes
        ("bt", "bt"),
        ("tb", "tb"),
        ("lr", "lr"),
        ("rl", "rl"),
        # Case-insensitive
        ("BT", "bt"),
        ("Bt", "bt"),
        ("LR", "lr"),
        # Mermaid `TD` alias
        ("td", "tb"),
        ("TD", "tb"),
        # CSS-style 3-letter
        ("ltr", "lr"),
        ("rtl", "rl"),
        # Long pair forms — underscore separator
        ("bottom_to_top", "bt"),
        ("top_to_bottom", "tb"),
        ("left_to_right", "lr"),
        ("right_to_left", "rl"),
        # Long pair forms — hyphen separator
        ("bottom-to-top", "bt"),
        ("top-to-bottom", "tb"),
        ("left-to-right", "lr"),
        ("right-to-left", "rl"),
        # Mixed case + hyphen
        ("Bottom-To-Top", "bt"),
        ("BOTTOM_TO_TOP", "bt"),
        # Vernacular
        ("bottom_up", "bt"),
        ("top_down", "tb"),
        ("Top-Down", "tb"),
    ],
)
def test_orientation_aliases_normalize_to_canonical(user_input: str, expected_canonical: str) -> None:
    # --- arrange / act ----------------
    op = ThemeOp.model_validate({"op": "theme", "orientation": user_input})

    # --- assert -----------------------
    assert op.orientation == expected_canonical


@pytest.mark.parametrize(
    "bad_input",
    [
        # camelCase — collapses to `bottomtotop` after lowercase, not in table
        "bottomToTop",
        "BottomToTop",
        # Space-separated
        "bottom to top",
        # Malformed underscores
        "bo_ttom_t_o_top",
        # Not a known orientation at all
        "diagonal",
        "xyz",
        "",
    ],
)
def test_orientation_rejects_non_canonical_inputs(bad_input: str) -> None:
    # --- arrange / act / assert -------
    with pytest.raises(ValidationError):
        ThemeOp.model_validate({"op": "theme", "orientation": bad_input})


def test_orientation_field_absent_means_unset() -> None:
    """When the JSONL op omits `orientation`, `model_fields_set` doesn't
    include it (so the apply step doesn't touch the live theme's value)."""
    # --- arrange / act ----------------
    op = ThemeOp.model_validate({"op": "theme", "background_color": "#abcdef"})

    # --- assert -----------------------
    assert op.orientation is None
    assert "orientation" not in op.model_fields_set


# ==================================================================================================
#  Per-orientation default resolution
# ==================================================================================================
def _resolved_with_orientation(orientation: str):
    """Return a fresh `DefaultTheme` resolved with the given orientation."""
    return DefaultTheme.build({"orientation": orientation})


@pytest.mark.parametrize(
    ("orientation", "expected_branch_spacing", "expected_commit_spacing"),
    [
        # Vertical: wider branch_spacing (lanes stack horizontally and need
        # horizontal room for labels).
        ("bt", 100, 50),
        ("tb", 100, 50),
        # Horizontal: symmetric — commit labels sit above/below the branch
        # line and need both vertical room between branches and horizontal
        # room between commits in comparable amounts.
        ("lr", 75, 75),
        ("rl", 75, 75),
    ],
)
def test_resolver_picks_spacing_defaults_per_orientation(
    orientation: str, expected_branch_spacing: int, expected_commit_spacing: int
) -> None:
    # --- arrange / act ----------------
    theme = _resolved_with_orientation(orientation)

    # --- assert -----------------------
    assert theme.branch_spacing == expected_branch_spacing
    assert theme.commit_spacing == expected_commit_spacing


@pytest.mark.parametrize(
    ("orientation", "expected_left", "expected_right", "expected_top_bottom"),
    [
        # Vertical: left/right anchored to branch_spacing × 1.0 (symmetric);
        # top/bottom to commit_spacing × 0.5.
        ("bt", 100, 100, 25),
        ("tb", 100, 100, 25),
        # Horizontal: top/bottom anchored to branch_spacing × 1.0;
        # left/right anchored to commit_spacing but ASYMMETRIC — the
        # start side gets ×1.5 (room for the branch pill at
        # commit_axis=-0.75) and the end side stays at ×1.0. With
        # commit_spacing=75: start side = 112.5, end side = 75.
        ("lr", 112.5, 75, 75),  # LR: timeline starts on the left
        ("rl", 75, 112.5, 75),  # RL: timeline starts on the right
    ],
)
def test_resolver_uses_asymmetric_margins_in_horizontal_orientations(
    orientation: str, expected_left: int, expected_right: int, expected_top_bottom: int
) -> None:
    # --- arrange / act ----------------
    theme = _resolved_with_orientation(orientation)

    # --- assert -----------------------
    assert theme.margin_left == expected_left
    assert theme.margin_right == expected_right
    assert theme.margin_top == expected_top_bottom
    assert theme.margin_bottom == expected_top_bottom


@pytest.mark.parametrize(
    ("orientation", "expected_overshoot"),
    [
        ("bt", 0.25),
        ("tb", 0.25),
        ("lr", 0.5),
        ("rl", 0.5),
    ],
)
def test_resolver_picks_per_orientation_guide_overshoot(orientation: str, expected_overshoot: float) -> None:
    # --- arrange / act ----------------
    theme = _resolved_with_orientation(orientation)

    # --- assert -----------------------
    assert theme.guide_overshoot_in_rows == expected_overshoot


@pytest.mark.parametrize(
    ("orientation", "expected_branch_pill_commit", "expected_branch_pill_branch"),
    [
        # Vertical: pill sits along the commit axis (below the start commit).
        ("bt", -0.5, 0.0),
        ("tb", -0.5, 0.0),
        # Horizontal: pill sits ON the branch line, offset back along the
        # commit axis from the start (pixel-left of start in `lr`,
        # pixel-right in `rl`). The pill is edge-anchored on its near
        # side, so the offset is the minimum gap between the start commit
        # and the pill — the pill itself extends further into the
        # start-side margin.
        ("lr", -0.25, 0.0),
        ("rl", -0.25, 0.0),
    ],
)
def test_resolver_routes_branch_pill_offset_per_orientation(
    orientation: str, expected_branch_pill_commit: float, expected_branch_pill_branch: float
) -> None:
    # --- arrange / act ----------------
    theme = _resolved_with_orientation(orientation)

    # --- assert -----------------------
    assert theme.branch_name_pill_offset_commit_axis_in_rows == expected_branch_pill_commit
    assert theme.branch_name_pill_offset_branch_axis_in_lanes == expected_branch_pill_branch


@pytest.mark.parametrize("orientation", ["bt", "tb", "lr", "rl"])
def test_resolver_picks_label_angles_zero_per_orientation(orientation: str) -> None:
    """v0.1.8 default: every label angle resolves to 0° in every orientation.

    Plumbed-but-waiting-on-anchors — non-zero defaults arrive once future
    named themes ship visually-considered angle / anchor pairings.
    """
    # --- arrange / act ----------------
    theme = _resolved_with_orientation(orientation)

    # --- assert -----------------------
    assert theme.branch_label_angle == 0.0
    assert theme.commit_label_angle == 0.0
    assert theme.pull_request_label_angle == 0.0


@pytest.mark.parametrize(
    ("orientation", "expected_pr_pill_commit", "expected_pr_pill_branch"),
    [
        # Anchor is the phantom point on the source branch line at the
        # projected merge target's commit-axis position. Vertical: pill
        # sits half a row back from the merge row toward the source tip,
        # on the source branch line. Horizontal: pill sits half a lane
        # above the source branch line at the merge column.
        ("bt", -0.5, 0.0),
        ("tb", -0.5, 0.0),
        ("lr", 0.0, -0.5),
        ("rl", 0.0, -0.5),
    ],
)
def test_resolver_picks_pr_pill_offset_per_orientation(
    orientation: str, expected_pr_pill_commit: float, expected_pr_pill_branch: float
) -> None:
    # --- arrange / act ----------------
    theme = _resolved_with_orientation(orientation)

    # --- assert -----------------------
    assert theme.pull_request_pill_offset_commit_axis_in_rows == expected_pr_pill_commit
    assert theme.pull_request_pill_offset_branch_axis_in_lanes == expected_pr_pill_branch


# ==================================================================================================
#  Sentinel semantics — user-set values stay sticky; null resets to default
# ==================================================================================================
def test_user_set_margin_is_not_overwritten_by_resolver() -> None:
    # --- arrange / act ----------------
    theme = DefaultTheme.build({"margin_left": 200})

    # --- assert -----------------------
    assert theme.margin_left == 200  # user value wins
    # Other margins still resolve to defaults.
    assert theme.margin_right == 100  # default for BT


def test_user_set_label_angle_is_not_overwritten_by_resolver() -> None:
    # --- arrange / act ----------------
    theme = DefaultTheme.build({"commit_label_angle": 45.0})

    # --- assert -----------------------
    assert theme.commit_label_angle == 45.0  # user value wins
    # Other angle fields still resolve to default.
    assert theme.branch_label_angle == 0.0
    assert theme.pull_request_label_angle == 0.0


def test_explicit_null_orientation_resets_to_default() -> None:
    """A `theme:` op with `"orientation": null` should reset Theme.orientation
    to the package default (`"bt"`), per the sentinel-reset semantic."""
    # --- arrange / act ----------------
    op = ThemeOp.model_validate({"op": "theme", "orientation": None})

    # --- assert -----------------------
    # The op carries None for orientation; the apply step special-cases this
    # to map back to "bt". This test covers the op-level behavior; the
    # apply-step behavior is covered elsewhere.
    assert op.orientation is None
    assert "orientation" in op.model_fields_set


# ==================================================================================================
#  Orientation.is_vertical
# ==================================================================================================
@pytest.mark.parametrize(
    ("orientation", "expected"),
    [
        (Orientation.BT, True),
        (Orientation.TB, True),
        (Orientation.LR, False),
        (Orientation.RL, False),
    ],
)
def test_orientation_is_vertical(orientation: Orientation, expected: bool) -> None:
    # --- act / assert -----------------
    assert orientation.is_vertical is expected


# ==================================================================================================
#  Build-boundary orientation coercion (regression guard)
# ==================================================================================================
def test_build_coerces_raw_string_orientation_to_enum_before_resolution() -> None:
    """A raw-string `orientation` override is coerced to the `Orientation` enum
    at the `build()` boundary, before any resolver runs.

    `theme:` ops deliver `orientation` as a raw canonical string, so without the
    coercion it would reach orientation-dependent resolvers untyped — and a
    type-specific call like `orientation.is_vertical` (used by the spacing
    resolvers) would raise `AttributeError` on a `str`. Pinning both the resolved
    enum type and a resolver output that depends on `.is_vertical` keeps that
    regression caught.
    """
    # --- act --------------------------
    theme = DefaultTheme.build({"orientation": "lr"})

    # --- assert -----------------------
    # Coerced to the enum, not left as the raw "lr" string.
    assert theme.orientation is Orientation.LR
    # And the coercion happened before resolution: `_resolve_branch_spacing`
    # consumed `orientation.is_vertical` and picked the horizontal default.
    assert theme.branch_spacing == 75
