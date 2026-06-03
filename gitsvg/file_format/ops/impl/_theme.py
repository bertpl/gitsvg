"""The `theme` operation."""

from typing import Annotated, Literal

from pydantic import BeforeValidator, Field, field_validator

from gitsvg._value_types import (
    BoxAnchor,
    BranchLineStyle,
    CommitLabelLayout,
    CommitRowMode,
    MergeCommitStyle,
    Orientation,
    normalize_orientation,
    validate_box_anchor,
)
from gitsvg.file_format.ops.framework._base import OpBase
from gitsvg.file_format.ops.framework._types import (
    HexColor,
    IdStr,
    NonEmptyStr,
    NonNegativeFloat,
    NonNegativeInt,
)

Opacity = Annotated[float, Field(ge=0, le=1)]
"""Float in `[0, 1]` — for opacity fields where SVG semantics are bounded."""

OrientationInput = Annotated[Orientation, BeforeValidator(normalize_orientation)]
"""Annotated orientation type that normalizes permissive input forms (case-insensitive, `-`/`_` interchangeable, Mermaid `TD`, CSS `ltr`/`rtl`, vernacular `top_down`/`bottom_up`) to the canonical short code before the `Literal` validator runs."""


class ThemeOp(OpBase):
    """Apply a theme patch to the diagram's accumulated theme overrides.

    Each `theme:` op contributes to a per-diagram accumulator that
    resolves to the final `Theme` at end-of-apply. Three field roles:

    - **`name`** selects the theme class the final resolution
      dispatches to. Last write wins across the apply pass — the most
      recent `name` set anywhere in the op stream picks the class.
    - **`keep_prior_overrides`** modifies the effect of `name` in the
      same op. By default (`false`) a `name` change wipes every
      previously-accumulated override (both `theme:` field overrides
      and state-derived per-branch `branch:` color overrides) before
      this op's own explicit fields apply. Setting it to `true`
      preserves prior overrides so a chosen theme can be layered onto
      existing tweaks. The flag is only meaningful when `name` is also
      set in the same op; explicit values without `name` are rejected
      (E220) and the implicit default has no effect there.
    - **Every other field** is an explicit theme-field override; later
      writes to the same field win.

    A mixed op (`name` plus explicit fields) applies in two steps: the
    `name` switch runs first (with its conditional wipe), then the
    explicit fields override on top — so an op's own fields are never
    discarded by its own reset. An op with neither a `name`, an
    explicit field, nor a `keep_prior_overrides` value is rejected
    (E217).
    """

    op: Literal["theme"]
    name: IdStr | None = Field(
        default=None,
        description="Optional named theme; switches the resolution target. By default wipes every accumulated override before this op's own fields apply (see `keep_prior_overrides` to preserve them).",
    )
    keep_prior_overrides: bool = Field(
        default=False,
        description="When set on an op that also sets `name`, controls whether previously-accumulated overrides survive the theme switch: `false` (default) wipes both prior `theme:` field overrides and state-derived per-branch `branch:` color overrides; `true` preserves them so this theme layers on top. Only meaningful alongside `name` — explicit values on an op without `name` are rejected (E220).",
    )

    # --- Orientation ------------------------------------
    orientation: OrientationInput | None = Field(
        default=None,
        description=(
            "Diagram orientation. Canonical short codes: `bt` (bottom-to-top, default), "
            "`tb` (top-to-bottom), `lr` (left-to-right), `rl` (right-to-left). "
            "Aliases accepted (case-insensitive, `-`/`_` interchangeable): Mermaid's `TD` (≡ `tb`), "
            "CSS-style `ltr` (≡ `lr`) and `rtl` (≡ `rl`), the four explicit `<dir>_to_<dir>` "
            "long forms (e.g. `bottom_to_top`), and the vernacular `top_down` / `bottom_up`."
        ),
    )

    # --- Layout policy ----------------------------------
    commit_row_mode: CommitRowMode | None = Field(
        default=None,
        description="How commits pack along the commit axis: `shared` (default; commits on different branches may share a row, keeping the diagram compact) or `unique` (every commit gets its own row, assigned in authoring order, so vertical position strictly encodes the order events were declared).",
    )
    auto_lane_change: bool | None = Field(
        default=None,
        description="When `true`, a branch migrates toward lower lane indices as lower lanes free up (a lower-lane branch ends), so live branches always occupy the lowest lanes; when `false` (default) a branch keeps its assigned lane for its whole life. Mutually exclusive with any `branch:` op that sets `branch_pos` (E221).",
    )
    merge_lane_clearance: NonNegativeInt | None = Field(
        default=None,
        description="Rows a merged or pull-requested source branch keeps its lane reserved past the end of its drawn line. `1` (default) reserves through the merge row, so a migrating sibling reclaims the freed lane one row after the merge; `0` lets a sibling land on the merge row itself; `2`+ leaves more breathing room. Only has effect under `auto_lane_change` — setting it while that flag is off is rejected (E222).",
    )

    # --- Spacing (px) -----------------------------------
    branch_spacing: NonNegativeFloat | None = Field(
        default=None,
        description="Pixel distance between adjacent branch-axis slots.",
    )
    commit_spacing: NonNegativeFloat | None = Field(
        default=None,
        description="Pixel distance between adjacent commit-axis slots.",
    )
    margin_left: NonNegativeFloat | None = Field(
        default=None,
        description="Pixel margin at the visually-left edge of the canvas. `null` resolves to the per-orientation default (see format spec).",
    )
    margin_right: NonNegativeFloat | None = Field(
        default=None,
        description="Pixel margin at the visually-right edge of the canvas. `null` resolves to the per-orientation default.",
    )
    margin_top: NonNegativeFloat | None = Field(
        default=None,
        description="Pixel margin at the visually-top edge of the canvas. `null` resolves to the per-orientation default.",
    )
    margin_bottom: NonNegativeFloat | None = Field(
        default=None,
        description="Pixel margin at the visually-bottom edge of the canvas. `null` resolves to the per-orientation default.",
    )

    # --- Strokes & geometry (px) ------------------------
    branch_line_width: NonNegativeFloat | None = Field(
        default=None,
        description="Stroke width of branch lines and arcs.",
    )
    commit_radius: NonNegativeFloat | None = Field(
        default=None,
        description="Radius of a commit dot.",
    )
    commit_stroke_width: NonNegativeFloat | None = Field(
        default=None,
        description="Stroke width of the white outline around a commit dot.",
    )
    highlight_radius: NonNegativeFloat | None = Field(
        default=None,
        description="Radius of a highlighted commit dot.",
    )
    merge_commit_radius: NonNegativeFloat | None = Field(
        default=None,
        description="Radius of a merge-commit dot (commits with 2+ parents). Defaults to `commit_radius`, so merge and ordinary dots match unless set; raise it to keep merge dots prominent when shrinking `commit_radius`. Under `merge_commit_style: checkmark` the dot's ring scales from this radius.",
    )
    arc_corner_radius_in_grid_units: NonNegativeFloat | None = Field(
        default=None,
        description="Corner radius for `rounded`-style connectors, expressed as a multiple of `min(branch_spacing, commit_spacing)`. Per-connector clamped at render time to fit the segment lengths, so values larger than 1.0 produce no further effect. Ignored by the `straight` and `double_rounded` styles.",
    )
    branch_line_style: BranchLineStyle | None = Field(
        default=None,
        description="Shape of the connectors between lanes (branch-off, merge, pull-request): `rounded` (default; two straight legs joined by a single quarter-arc corner), `straight` (a direct line), `bezier` (a single flowing curve that runs along a branch's own lane where it joins that branch, then sweeps diagonally across to the connecting commit, with no flat perpendicular leg), `double_rounded` (a stepped connector — two quarter-arcs around an orthogonal crossing near the trunk), or `double_bezier` (a smooth cubic-Bézier S, tangent to the commit axis at both ends).",
    )
    merge_commit_style: MergeCommitStyle | None = Field(
        default=None,
        description="Style for merge-commit dots (commits with 2+ parents); ordinary commits are unaffected: `circle` (default; the plain branch-color dot, identical to an ordinary commit) or `checkmark` (a hollow dot — fill and stroke swap so the dot is `commit_stroke_color`-filled with a branch-color ring — overlaid with a branch-color checkmark).",
    )
    label_offset_branch_axis_in_lanes: NonNegativeFloat | None = Field(
        default=None,
        description="Offset between a commit dot and the start of its label along the branch axis, expressed as a multiple of `branch_spacing`.",
    )
    branch_guide_width: NonNegativeFloat | None = Field(
        default=None,
        description="Stroke width of the faint per-lane vertical guides.",
    )
    branch_guide_dash: NonEmptyStr | None = Field(
        default=None,
        description='SVG stroke-dasharray for the branch guides (e.g. `"4,4"`).',
    )
    guide_overshoot_in_rows: NonNegativeFloat | None = Field(
        default=None,
        description="How far each branch guide extends past the commit-axis margin edges, expressed as a multiple of `commit_spacing` (applied symmetrically at both ends).",
    )

    # --- Typography -------------------------------------
    label_font_family: NonEmptyStr | None = Field(
        default=None,
        description="Full CSS font-family chain used for all text elements.",
    )
    label_font_family_small: NonEmptyStr | None = Field(
        default=None,
        description="Compact font-family chain emitted under `--small`.",
    )
    label_font_size: NonNegativeFloat | None = Field(
        default=None,
        description="Font size for commit-message labels.",
    )
    branch_label_font_size: NonNegativeFloat | None = Field(
        default=None,
        description="Font size for branch-name pills and pull-request title pills.",
    )
    hash_font_size: NonNegativeFloat | None = Field(
        default=None,
        description="Font size for the secondary hash line on commit labels.",
    )
    branch_name_pill_offset_commit_axis_in_rows: float | None = Field(
        default=None,
        description="Branch-name pill offset along the commit axis, expressed as a signed multiple of `commit_spacing`. Positive = toward higher commit-axis index. Default is `-0.5` (pill sits below the branch's start row in bottom-to-top orientation).",
    )
    branch_name_pill_offset_branch_axis_in_lanes: float | None = Field(
        default=None,
        description="Branch-name pill offset along the branch axis, expressed as a signed multiple of `branch_spacing`. Positive = toward higher branch-axis index. Default is `0` (pill is centered on the branch lane in bottom-to-top orientation).",
    )
    pill_padding_x_in_font_sizes: NonNegativeFloat | None = Field(
        default=None,
        description="Extra pill width beyond the rendered text, expressed as a multiple of `branch_label_font_size`.",
    )
    pill_padding_y_in_font_sizes: NonNegativeFloat | None = Field(
        default=None,
        description="Extra pill height beyond the font size, expressed as a multiple of `branch_label_font_size`.",
    )
    pill_corner_radius_in_font_sizes: NonNegativeFloat | None = Field(
        default=None,
        description="Pill rounded-corner radius (`rx` / `ry`), expressed as a multiple of `branch_label_font_size`.",
    )
    label_line_padding_in_font_sizes: NonNegativeFloat | None = Field(
        default=None,
        description="Extra height per line in a multi-line commit-label stack, expressed as a multiple of `label_font_size`.",
    )

    # --- Pull-request visuals ---------------------------
    pull_request_dash: NonEmptyStr | None = Field(
        default=None,
        description='SVG stroke-dasharray for pull-request arcs (e.g. `"6,4"`).',
    )
    pull_request_pill_offset_commit_axis_in_rows: float | None = Field(
        default=None,
        description="PR title-pill offset along the commit axis, expressed as a signed multiple of `commit_spacing`. Positive = toward higher commit-axis index. Default is `+0.5` (pill sits above the source-tip commit in bottom-to-top orientation).",
    )
    pull_request_pill_offset_branch_axis_in_lanes: float | None = Field(
        default=None,
        description="PR title-pill offset along the branch axis, expressed as a signed multiple of `branch_spacing`. Positive = toward higher branch-axis index. Default is `0` (pill is centered on the source branch's lane in bottom-to-top orientation).",
    )

    # --- Label angles -----------------------------------
    branch_label_angle: float | None = Field(
        default=None,
        description="Rotation angle (degrees) for the branch-name pill, applied around the pill's world anchor point so the anchor stays pinned regardless of angle. Default is 0° across all orientations; the default anchor positions are tuned for un-rotated text, so non-zero values render mechanically but typically need a custom `branch_pill_anchor` to look visually settled.",
    )
    commit_label_angle: float | None = Field(
        default=None,
        description="Rotation angle (degrees) for the commit-label stack (governs msg + hash + future tag lines together). Default is 0° across all orientations; see `branch_label_angle` for the visual-practicality caveat.",
    )
    pull_request_label_angle: float | None = Field(
        default=None,
        description="Rotation angle (degrees) for the pull-request title pill. Default is 0° across all orientations; see `branch_label_angle` for the visual-practicality caveat.",
    )

    # --- Box anchors ------------------------------------
    branch_pill_anchor: BoxAnchor | None = Field(
        default=None,
        description="Branch-name pill `(u, v)` in `[0, 1]²` — where inside the un-rotated pill rect the world anchor point sits (and equivalently where rotation pivots around). Two-element JSON array. Per-orientation defaults: `bt`/`tb` center `[0.5, 0.5]`; `lr` right-edge `[1.0, 0.5]`; `rl` left-edge `[0.0, 0.5]`.",
    )
    pull_request_pill_anchor: BoxAnchor | None = Field(
        default=None,
        description="PR-title pill `(u, v)` in `[0, 1]²`. Two-element JSON array. Defaults to center `[0.5, 0.5]` in every orientation.",
    )
    commit_label_anchor_before: BoxAnchor | None = Field(
        default=None,
        description="Commit-label `(u, v)` for the `before` (lower-index) side. Two-element JSON array. Per-orientation defaults: `bt`/`tb` `[1.0, 0.5]` (stack's right-middle at the world point); `lr`/`rl` `[0.5, 1.0]` (stack's bottom-middle).",
    )
    commit_label_anchor_after: BoxAnchor | None = Field(
        default=None,
        description="Commit-label `(u, v)` for the `after` (higher-index) side. Two-element JSON array. Per-orientation defaults: `bt`/`tb` `[0.0, 0.5]`; `lr`/`rl` `[0.5, 0.0]`.",
    )

    # --- Colors ----------------------------------------
    label_color: HexColor | None = Field(
        default=None,
        description="Fill color for commit-message labels.",
    )
    hash_color: HexColor | None = Field(
        default=None,
        description="Fill color for the secondary hash line on commit labels.",
    )
    branch_guide_color: HexColor | None = Field(
        default=None,
        description="Stroke color for the faint per-lane vertical guides.",
    )
    commit_stroke_color: HexColor | None = Field(
        default=None,
        description="Stroke color for the outline around commit dots. Visually separates the dot from any branch line passing through it. Default is `white` (reads as a halo on light backgrounds); dark themes typically override this to their background color so the outline reads as a 'carved out' gap. Under `merge_commit_style: checkmark`, merge dots reuse this color as their fill.",
    )
    branch_label_bg_opacity: Opacity | None = Field(
        default=None,
        description="Background opacity (0–1) for branch-name and PR title pills.",
    )
    background_color: HexColor | None = Field(
        default=None,
        description="Optional full-canvas background color; unset by default (transparent SVG).",
    )
    commit_row_band_color: HexColor | None = Field(
        default=None,
        description="Optional zebra-stripe fill painted on alternate commit-axis rows, spanning the full canvas just above the background (any orientation; unset by default = no banding, so output is unchanged). Accepts 3/4/6/8-digit hex; an alpha channel (e.g. `#00000022`) composes the stripe over the background, while `#RGB`/`#RRGGBB` paint fully opaque.",
    )
    commit_label_layout: CommitLabelLayout | None = Field(
        default=None,
        description="How commit labels are placed: `inline` (default — `msg`/`hash` float beside each dot) or `table` (commit `hash`/branch/message laid out as fixed-width columns beside the graph, one row per commit). `table` is supported only in vertical orientations (`bt`/`tb`) and forces one commit per row (`commit_row_mode: unique`); combining it with a horizontal orientation or an explicit `commit_row_mode: shared` is rejected.",
    )
    table_msg_width: NonNegativeInt | None = Field(
        default=None,
        description="Width (px) of the message column in `table` layout; `0` omits the column and reclaims its space. No effect outside table mode.",
    )
    table_hash_width: NonNegativeInt | None = Field(
        default=None,
        description="Width (px) of the hash column in `table` layout; `0` omits the column and reclaims its space. No effect outside table mode.",
    )
    table_cell_padding_x_in_font_sizes: NonNegativeFloat | None = Field(
        default=None,
        description="The table's horizontal spacing unit in `table` layout, as a multiple of `label_font_size` (default `0.5`): the inner padding inset on each side of a cell, and the gap between adjacent tip pills and before the message. Columns abut, so content-to-content separation between columns is twice this value.",
    )
    colors: dict[IdStr, HexColor] | None = Field(
        default=None,
        description="Replacement branch-palette dict; replaces the current palette wholesale when set.",
    )

    @field_validator(
        "branch_pill_anchor",
        "pull_request_pill_anchor",
        "commit_label_anchor_before",
        "commit_label_anchor_after",
    )
    @classmethod
    def _validate_anchor_components(cls, v: BoxAnchor | None) -> BoxAnchor | None:
        """Reject `BoxAnchor` values with a component outside `[0, 1]` at parse time."""
        return validate_box_anchor(v)
