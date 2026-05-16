"""End-of-state-stage default resolution for orientation-aware fields.

Mutates a `Theme` in place, replacing every `None`-default sentinel
on an orientation-resolved field with a concrete pixel value. Called
by the state engine as the last step of `apply_ops` so the renderer
never sees a `None`.

Sentinel semantics: `None` means "still default — fill from the
orientation-resolved formula"; any concrete value means "user-set,
sticky." A field set to `null` mid-stream by a later `theme:` op
resets to `None`, which lets the resolver re-fill it — the supported
"opt back into the default" mechanism.

Cascade order matters because later steps depend on earlier
resolutions:

1. **Spacings** (`branch_spacing`, `commit_spacing`) — depend on
   orientation alone.
2. **Pill offsets** (4 fields) — depend on orientation alone.
3. **Margins** (`margin_left`, `margin_right`, `margin_top`,
   `margin_bottom`) — depend on orientation *and* the resolved
   spacings.

`theme.orientation` is always concrete (default `"bt"`); the
resolver reads it directly and never overwrites it.
"""

from gitsvg.theme._orientation import Orientation
from gitsvg.theme._theme import Theme, _resolve_int_or_float


def resolve_defaults(theme: Theme) -> None:
    """Fill `None`-default fields on `theme` with concrete pixel values.

    Mutates in place. Idempotent: a second call leaves the theme
    unchanged because every field is now non-`None`.

    Args:
        theme: The accumulated live theme, post-`apply_ops`. Fields
            the user explicitly set are kept; `None` fields are
            filled from the per-orientation default formula.
    """
    _resolve_spacings(theme)
    _resolve_label_offset(theme)
    _resolve_guide_overshoot(theme)
    _resolve_pill_offsets(theme)
    _resolve_margins(theme)
    _resolve_label_angles(theme)


# ==================================================================================================
#  Per-stage resolvers
# ==================================================================================================
def _resolve_spacings(theme: Theme) -> None:
    """Fill `None` spacings with the per-orientation defaults.

    Vertical orientations (`bt`, `tb`) get the wider `branch_spacing`
    (branches stack horizontally, labels need horizontal room);
    horizontal orientations (`lr`, `rl`) swap the roles.
    """
    branch_default, commit_default = _spacing_defaults(theme.orientation)
    if theme.branch_spacing is None:
        theme.branch_spacing = branch_default
    if theme.commit_spacing is None:
        theme.commit_spacing = commit_default


def _resolve_pill_offsets(theme: Theme) -> None:
    """Fill `None` pill offsets with the per-orientation defaults.

    Vertical orientations: branch-name pill sits below the start
    (`commit_axis=-0.5`); PR pill sits above the tip
    (`commit_axis=+0.5`). Both use the commit-axis component and
    centre on the branch lane (`branch_axis=0`).

    Horizontal orientations: branch-name pill sits *along* the branch
    line, offset back along the commit axis from the start
    (`commit_axis=-0.25` → pixel-left of start in `lr`, pixel-right
    in `rl`). The pill is anchored on its edge nearest the start
    commit (see `_branch_pill.py`), so this offset is the minimum
    gap between the start commit and the pill — the pill itself
    extends further into the start-side margin. PR pill currently
    keeps its branch-axis offset (sits below the branch line) —
    pending a separate decision on whether to mirror the branch
    pill's treatment.
    """
    is_vertical = theme.orientation in (Orientation.BT, Orientation.TB)
    branch_pill_commit_default = -0.5 if is_vertical else -0.25
    branch_pill_branch_default = 0.0 if is_vertical else 0.0
    # PR pill anchor is the phantom point at (source-branch lane,
    # merge target's commit-axis) — see `_pull_request_pill.py`. The
    # default offset nudges the pill half a row back from the merge
    # row toward the source tip in vertical orientations, and half a
    # lane up from the source branch line in horizontal orientations
    # (so it sits above-and-out from the source line at the merge
    # column).
    pr_pill_commit_default = -0.5 if is_vertical else 0.0
    pr_pill_branch_default = 0.0 if is_vertical else -0.5

    if theme.branch_name_pill_offset_commit_axis_in_rows is None:
        theme.branch_name_pill_offset_commit_axis_in_rows = branch_pill_commit_default
    if theme.branch_name_pill_offset_branch_axis_in_lanes is None:
        theme.branch_name_pill_offset_branch_axis_in_lanes = branch_pill_branch_default
    if theme.pull_request_pill_offset_commit_axis_in_rows is None:
        theme.pull_request_pill_offset_commit_axis_in_rows = pr_pill_commit_default
    if theme.pull_request_pill_offset_branch_axis_in_lanes is None:
        theme.pull_request_pill_offset_branch_axis_in_lanes = pr_pill_branch_default


def _resolve_guide_overshoot(theme: Theme) -> None:
    """Fill `None` `guide_overshoot_in_rows` per orientation.

    Vertical orientations (`bt`, `tb`) use `0.25` (resolved to
    12.5 px overshoot at the default `commit_spacing=50`). Horizontal
    orientations (`lr`, `rl`) use `0.5` (50 px overshoot at
    `commit_spacing=100`) — the larger reach covers the branch-pill
    area in the asymmetrically-wider start-side margin without leaving
    the pill visually disconnected from the guide line.
    """
    if theme.guide_overshoot_in_rows is None:
        if theme.orientation in (Orientation.BT, Orientation.TB):
            theme.guide_overshoot_in_rows = 0.25
        else:
            theme.guide_overshoot_in_rows = 0.5


def _resolve_label_offset(theme: Theme) -> None:
    """Fill `None` `label_offset_branch_axis_in_lanes` per orientation.

    Vertical orientations (`bt`, `tb`) use `0.12` (the historical
    default — 12 px at the default `branch_spacing=100`). Horizontal
    orientations (`lr`, `rl`) use `0.24` so the resolved pixel offset
    matches BT (twice the lane ratio compensates for the halved
    `branch_spacing=50` in horizontal orientations).
    """
    if theme.label_offset_branch_axis_in_lanes is None:
        if theme.orientation in (Orientation.BT, Orientation.TB):
            theme.label_offset_branch_axis_in_lanes = 0.12
        else:
            theme.label_offset_branch_axis_in_lanes = 0.24


def _resolve_label_angles(theme: Theme) -> None:
    """Fill `None` label-angle fields with their per-orientation defaults.

    0° across all orientations today for every label kind — labels
    always horizontally readable. The shape accommodates richer per-
    orientation defaults once future named themes ship visually-
    considered angle / anchor pairings (Mermaid-style 45°, follow-line
    90° / 270° in horizontal orientations, etc.).
    """
    if theme.branch_label_angle is None:
        theme.branch_label_angle = 0.0
    if theme.commit_label_angle is None:
        theme.commit_label_angle = 0.0
    if theme.pull_request_label_angle is None:
        theme.pull_request_label_angle = 0.0


def _resolve_margins(theme: Theme) -> None:
    """Fill `None` margins with per-orientation defaults × resolved spacings.

    Vertical orientations (`bt`, `tb`): left/right anchored to
    `branch_spacing` (×1.0); top/bottom anchored to `commit_spacing`
    (×0.5). Symmetric.

    Horizontal orientations (`lr`, `rl`): top/bottom anchored to
    `branch_spacing` (×1.0); left/right anchored to `commit_spacing`
    but **asymmetric** — the side where the timeline starts (left in
    `lr`, right in `rl`) gets ×1.5 to give the branch-name pill (now
    placed at `commit_axis=-0.75` from the branch start) room to extend
    into the margin without clipping; the opposite side stays at ×1.0.
    `_resolve_int_or_float` keeps whole-number results as `int` so SVG
    attribute formatting matches the byte-identical baseline.
    """
    if theme.orientation in (Orientation.BT, Orientation.TB):
        horizontal_default = _resolve_int_or_float(1.0 * theme.branch_spacing)
        vertical_default = _resolve_int_or_float(0.5 * theme.commit_spacing)
        margin_left_default = horizontal_default
        margin_right_default = horizontal_default
        margin_top_default = vertical_default
        margin_bottom_default = vertical_default
    else:
        # Horizontal: top/bottom from branch_spacing; left/right from
        # commit_spacing with the start side widened to fit the branch pill.
        margin_top_default = _resolve_int_or_float(1.0 * theme.branch_spacing)
        margin_bottom_default = _resolve_int_or_float(1.0 * theme.branch_spacing)
        start_side = _resolve_int_or_float(1.5 * theme.commit_spacing)
        end_side = _resolve_int_or_float(1.0 * theme.commit_spacing)
        if theme.orientation == Orientation.LR:
            # Timeline starts on the left in LR.
            margin_left_default = start_side
            margin_right_default = end_side
        else:  # rl
            # Timeline starts on the right in RL.
            margin_left_default = end_side
            margin_right_default = start_side

    if theme.margin_left is None:
        theme.margin_left = margin_left_default
    if theme.margin_right is None:
        theme.margin_right = margin_right_default
    if theme.margin_top is None:
        theme.margin_top = margin_top_default
    if theme.margin_bottom is None:
        theme.margin_bottom = margin_bottom_default


# ==================================================================================================
#  Helpers
# ==================================================================================================
def _spacing_defaults(orientation: Orientation) -> tuple[int, int]:
    """Return `(branch_spacing_default, commit_spacing_default)` for the given orientation.

    Vertical orientations get `(100, 50)` — branches stack horizontally,
    each lane needs horizontal room for labels. Horizontal orientations
    get `(75, 75)` — symmetric, since commit labels sit above/below the
    branch line and need both vertical room between branches and
    horizontal room between commits in comparable amounts.
    """
    if orientation in (Orientation.BT, Orientation.TB):
        return 100, 50
    return 75, 75
