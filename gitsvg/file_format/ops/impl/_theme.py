"""The `theme` operation."""

from typing import Annotated, Literal

from pydantic import BeforeValidator, Field

from gitsvg.file_format.ops.framework._base import OpBase
from gitsvg.file_format.ops.framework._types import (
    HexColor,
    IdStr,
    NonEmptyStr,
    NonNegativeFloat,
    NonNegativeInt,
)
from gitsvg.theme import OrientationLiteral, normalize_orientation

Opacity = Annotated[float, Field(ge=0, le=1)]
"""Float in `[0, 1]` — for opacity fields where SVG semantics are bounded."""

OrientationInput = Annotated[OrientationLiteral, BeforeValidator(normalize_orientation)]
"""Annotated orientation type that normalises permissive input forms (case-insensitive, `-`/`_` interchangeable, Mermaid `TD`, CSS `ltr`/`rtl`, vernacular `top_down`/`bottom_up`) to the canonical short code before the `Literal` validator runs."""


class ThemeOp(OpBase):
    """Apply a theme patch to the diagram's live theme.

    Two patch shapes, composable in a single op:

    - **Explicit field overrides only.** Each field present in the op
      assigns only that field on the current theme; every other field
      keeps its current value.
    - **Named theme.** Setting `name` replaces every field with the
      named theme's values before any explicit fields apply. The set
      of named themes is fixed by the package (only `"default"` exists
      today; built-in palettes ship in a later version).

    A mixed op (`name` plus explicit fields) applies in two steps: the
    named theme replaces all fields, then the explicit fields override
    on top. An op with neither a `name` nor any explicit field is
    rejected (semantic error).
    """

    op: Literal["theme"]
    name: IdStr | None = Field(
        default=None,
        description="Optional named theme; replaces every theme field with that theme's values before explicit overrides apply.",
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
    arc_corner_radius_in_grid_units: NonNegativeFloat | None = Field(
        default=None,
        description="Corner radius for branch-off and merge arcs, expressed as a multiple of `min(branch_spacing, commit_spacing)`. Per-arc clamped at render time to fit the arc's segment lengths, so values larger than 1.0 produce no further effect.",
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
    label_font_size: NonNegativeInt | None = Field(
        default=None,
        description="Font size for commit-message labels.",
    )
    branch_label_font_size: NonNegativeInt | None = Field(
        default=None,
        description="Font size for branch-name pills and pull-request title pills.",
    )
    hash_font_size: NonNegativeInt | None = Field(
        default=None,
        description="Font size for the secondary hash line on commit labels.",
    )
    branch_name_pill_offset_commit_axis_in_rows: float | None = Field(
        default=None,
        description="Branch-name pill offset along the commit axis, expressed as a signed multiple of `commit_spacing`. Positive = toward higher commit-axis index. Default is `-0.5` (pill sits below the branch's start row in bottom-to-top orientation).",
    )
    branch_name_pill_offset_branch_axis_in_lanes: float | None = Field(
        default=None,
        description="Branch-name pill offset along the branch axis, expressed as a signed multiple of `branch_spacing`. Positive = toward higher branch-axis index. Default is `0` (pill is centred on the branch lane in bottom-to-top orientation).",
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
        description="PR title-pill offset along the branch axis, expressed as a signed multiple of `branch_spacing`. Positive = toward higher branch-axis index. Default is `0` (pill is centred on the source branch's lane in bottom-to-top orientation).",
    )

    # --- Colours ----------------------------------------
    label_color: HexColor | None = Field(
        default=None,
        description="Fill colour for commit-message labels.",
    )
    hash_color: HexColor | None = Field(
        default=None,
        description="Fill colour for the secondary hash line on commit labels.",
    )
    branch_guide_color: HexColor | None = Field(
        default=None,
        description="Stroke colour for the faint per-lane vertical guides.",
    )
    branch_label_bg_opacity: Opacity | None = Field(
        default=None,
        description="Background opacity (0–1) for branch-name and PR title pills.",
    )
    background_color: HexColor | None = Field(
        default=None,
        description="Optional full-canvas background colour; unset by default (transparent SVG).",
    )
    colors: dict[IdStr, HexColor] | None = Field(
        default=None,
        description="Replacement branch-palette dict; replaces the current palette wholesale when set.",
    )
