"""RendererSettings — the renderer pipeline stage's slice of the resolved theme.

A standalone, self-contained schema (not a `Theme` subclass): the
renderer only ever reads *resolved* values, so every field here is
concrete — except the two where `None` is itself a resolved value
(`background_color` = transparent, `commit_row_band_color` = no bands).
Constructed in one place, `Theme.split()`, from a fully-resolved
`Theme`'s field dump; every field is required, so an unresolved `None`
slipping through `build()` fails loudly at construction instead of
rendering garbage.

The field block deliberately mirrors `Theme` field-for-field. The
duplication is what lets a static type checker see the renderer's
values as non-Optional — a dynamically derived model would be invisible
to it. The architecture meta-test in `tests/architecture/` asserts the
two field sets stay identical, so they cannot drift apart silently.

Field *semantics* (units, axis-binding, anchor conventions, per-field
prose) are documented once, on `Theme`; this class re-states only the
resolved types. The resolved-pixel accessors and the per-branch
`branch_label_side` lookup live here — they are renderer vocabulary,
reading resolved values.
"""

from pydantic import BaseModel, ConfigDict, field_validator

from gitsvg._shared.numeric import resolve_int_or_float
from gitsvg._shared.value_types import (
    BoxAnchor,
    BranchLineStyle,
    CommitLabelLayout,
    CommitRowMode,
    LabelSide,
    MergeCommitStyle,
    Orientation,
)


class RendererSettings(BaseModel):
    """The renderer pipeline stage's slice of the resolved theme.

    Standalone frozen schema with concrete field types; see the module
    docstring for the relationship to `Theme`. The class identity marks
    the pipeline boundary — renderer code imports `RendererSettings`,
    never `Theme`.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    # --------------------------------------------------------------------------
    #  Orientation
    # --------------------------------------------------------------------------
    orientation: Orientation

    # --------------------------------------------------------------------------
    #  Layout policy (layout-stage fields; ride along unused on this slice)
    # --------------------------------------------------------------------------
    commit_row_mode: CommitRowMode
    auto_lane_change: bool
    merge_lane_clearance: int
    pull_request_extend_target_line: bool

    # --------------------------------------------------------------------------
    #  Spacing (px)
    # --------------------------------------------------------------------------
    branch_spacing: float
    commit_spacing: float

    # --------------------------------------------------------------------------
    #  Margins (visual-side, px)
    # --------------------------------------------------------------------------
    margin_left: float
    margin_right: float
    margin_top: float
    margin_bottom: float

    # --------------------------------------------------------------------------
    #  Strokes & geometry (px, except where noted)
    # --------------------------------------------------------------------------
    branch_line_width: float
    commit_radius: float
    commit_stroke_width: float
    highlight_radius: float
    merge_commit_radius: float
    merge_commit_style: MergeCommitStyle
    arc_corner_radius_in_grid_units: float
    branch_line_style: BranchLineStyle
    label_offset_branch_axis_in_lanes: float
    branch_guide_width: float
    branch_guide_dash: str
    guide_overshoot_in_rows: float

    # --------------------------------------------------------------------------
    #  Typography
    # --------------------------------------------------------------------------
    label_font_family: str
    label_font_family_small: str
    label_font_size: float
    branch_label_font_size: float
    hash_font_size: float
    branch_name_pill_offset_commit_axis_in_rows: float
    branch_name_pill_offset_branch_axis_in_lanes: float
    pill_padding_x_in_font_sizes: float
    pill_padding_y_in_font_sizes: float
    pill_corner_radius_in_font_sizes: float
    label_line_padding_in_font_sizes: float

    # --------------------------------------------------------------------------
    #  Pull-request visuals
    # --------------------------------------------------------------------------
    pull_request_dash: str
    pull_request_pill_offset_commit_axis_in_rows: float
    pull_request_pill_offset_branch_axis_in_lanes: float

    # --------------------------------------------------------------------------
    #  Label angles (degrees)
    # --------------------------------------------------------------------------
    branch_label_angle: float
    commit_label_angle: float
    pull_request_label_angle: float

    # --------------------------------------------------------------------------
    #  Box anchors (text-bearing primitives)
    # --------------------------------------------------------------------------
    branch_pill_anchor: BoxAnchor
    pull_request_pill_anchor: BoxAnchor
    commit_label_anchor_before: BoxAnchor
    commit_label_anchor_after: BoxAnchor

    # --------------------------------------------------------------------------
    #  Colors
    # --------------------------------------------------------------------------
    colors: dict[str, str]
    default_branch_color_cycle: list[str]
    label_color: str
    hash_color: str
    branch_guide_color: str
    commit_stroke_color: str
    branch_label_bg_opacity: float

    # --------------------------------------------------------------------------
    #  SVG background — `None` is a resolved value (transparent)
    # --------------------------------------------------------------------------
    background_color: str | None

    # --------------------------------------------------------------------------
    #  Row banding — `None` is a resolved value (no bands)
    # --------------------------------------------------------------------------
    commit_row_band_color: str | None

    # --------------------------------------------------------------------------
    #  Table layout
    # --------------------------------------------------------------------------
    commit_label_layout: CommitLabelLayout
    table_msg_width: int
    table_hash_width: int
    table_cell_padding_x_in_font_sizes: float

    # --------------------------------------------------------------------------
    #  Label-side defaults + state-derived per-branch overrides
    # --------------------------------------------------------------------------
    label_side_default: LabelSide
    branch_color_overrides: dict[str, str]
    branch_label_side_overrides: dict[str, LabelSide]

    # --------------------------------------------------------------------------
    #  Whole-value normalization
    # --------------------------------------------------------------------------
    @field_validator(
        "branch_spacing",
        "commit_spacing",
        "branch_line_width",
        "commit_radius",
        "highlight_radius",
        "merge_commit_radius",
    )
    @classmethod
    def _whole_values_render_as_int(cls, v: float) -> float:
        """Re-apply `Theme`'s whole-number normalization after pydantic's float coercion.

        Without this, a whole-number size arriving as `int` from the
        resolved theme would coerce to `float` here and render with a
        decimal point (`5.0` instead of `5`), changing SVG output.
        """
        return resolve_int_or_float(v)

    # --------------------------------------------------------------------------
    #  Resolved-pixel accessors for ratio-stored fields
    # --------------------------------------------------------------------------
    # Read-only: the renderer / canvas auto-fit / primitives read these
    # (e.g. `theme.arc_corner_radius`) and get the resolved pixel value,
    # computed lazily from the stored ratio × the relevant spacing.

    @property
    def arc_corner_radius(self) -> int | float:
        """Resolved pixel corner radius for branch-off / merge arcs."""
        return resolve_int_or_float(
            self.arc_corner_radius_in_grid_units * min(self.branch_spacing, self.commit_spacing)
        )

    @property
    def label_offset(self) -> int | float:
        """Resolved pixel offset between a commit dot and its label, along the branch axis."""
        return resolve_int_or_float(self.label_offset_branch_axis_in_lanes * self.branch_spacing)

    @property
    def guide_overshoot(self) -> int | float:
        """Resolved pixel overshoot — how far a branch guide extends past the commit-axis margin edges."""
        return resolve_int_or_float(self.guide_overshoot_in_rows * self.commit_spacing)

    @property
    def pill_padding_x(self) -> int | float:
        """Resolved pill-padding-x (px) — extra width beyond the rendered text."""
        return resolve_int_or_float(self.pill_padding_x_in_font_sizes * self.branch_label_font_size)

    @property
    def pill_padding_y(self) -> int | float:
        """Resolved pill-padding-y (px) — extra height beyond the font size."""
        return resolve_int_or_float(self.pill_padding_y_in_font_sizes * self.branch_label_font_size)

    @property
    def pill_corner_radius(self) -> int | float:
        """Resolved pill corner radius (px) for `rx` / `ry`."""
        return resolve_int_or_float(self.pill_corner_radius_in_font_sizes * self.branch_label_font_size)

    @property
    def label_line_padding(self) -> int | float:
        """Resolved extra height per line (px) in a multi-line label stack."""
        return resolve_int_or_float(self.label_line_padding_in_font_sizes * self.label_font_size)

    @property
    def table_cell_padding_x(self) -> int | float:
        """Resolved table horizontal spacing unit (px) — cell inset and intra-cell gaps."""
        return resolve_int_or_float(self.table_cell_padding_x_in_font_sizes * self.label_font_size)

    # --------------------------------------------------------------------------
    #  Per-branch resolved-value lookups
    # --------------------------------------------------------------------------
    def branch_label_side(self, branch_id: str) -> LabelSide:
        """Resolve a branch's `label_side` — per-branch override, then theme default.

        Args:
            branch_id: The branch's stable internal id (`BranchState.id`).

        Returns:
            The resolved `LabelSide` for the branch. Falls through to
            `self.label_side_default` when the branch never set
            `label_side` on its `branch:` op.
        """
        return self.branch_label_side_overrides.get(branch_id, self.label_side_default)
