"""Theme — every presentational constant the renderer reads.

`Theme` is the Pydantic base class for the diagram's presentational
surface. Concrete themes (today only `DefaultTheme`) subclass it and
provide a `build(user_set)` factory that resolves a fully-populated
`Theme` from the dict of explicitly-set fields the apply pass
accumulated. Each pipeline stage receives the resolved `Theme`
(layout and renderer both consume the whole `Theme` for now).

Every field is `T | None = None` on the base class — `None` means
"unset" pre-build and "no default-resolved value applies" for the
handful of fields where unset has semantic meaning (e.g.
`background_color = None` = transparent). After `build()` runs every
non-default field carries a concrete value.

Per-field validators capture always-hold invariants (positive
spacings / font sizes, opacities in `[0, 1]`). The apply pass emits
catalog-coded errors with line numbers when the same constraints
fail on user input; the validators are defence in depth at build
time and document the invariants alongside the field.

Position/size fields with a natural anchor stay stored as ratios
(suffixed `_in_lanes` / `_in_rows` / `_in_grid_units` /
`_in_font_sizes`) anchored to the relevant spacing or font size.
Pixel-valued accessors with the corresponding unsuffixed names live
as properties below the field block — read-only resolved values that
downstream consumers (renderer, canvas auto-fit, primitives) read
just as before.
"""

from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator

from gitsvg.file_format import LabelSide
from gitsvg.theme._box_anchor import BoxAnchor, validate_box_anchor
from gitsvg.theme._branch_line_style import BranchLineStyle
from gitsvg.theme._commit_row_mode import CommitRowMode
from gitsvg.theme._merge_commit_style import MergeCommitStyle
from gitsvg.theme._orientation import Orientation


class Theme(BaseModel):
    """Every presentational value the renderer reads.

    Pydantic base class. Every field is `T | None = None`; the
    apply pass collects a `user_set: dict` of explicit overrides and
    a concrete `Theme` subclass (e.g. `DefaultTheme`) resolves the
    full instance via its `build(user_set)` classmethod. Direct
    construction (`Theme(branch_spacing=120)`) is supported for tests
    but typical use goes through `build()`.
    """

    model_config = ConfigDict(extra="forbid")

    # --------------------------------------------------------------------------
    #  Orientation
    # --------------------------------------------------------------------------
    orientation: Orientation | None = None  # axis-symmetric (input-side selector)

    # --------------------------------------------------------------------------
    #  Layout policy (consumed by the layout stage via `LayoutSettings`)
    # --------------------------------------------------------------------------
    commit_row_mode: CommitRowMode | None = None  # axis-bound: commit-axis (row packing)
    auto_lane_change: bool | None = None  # axis-bound: branch-axis (mid-life lane migration)

    # --------------------------------------------------------------------------
    #  Spacing (px)
    # --------------------------------------------------------------------------
    branch_spacing: int | None = None  # axis-bound: branch-axis
    commit_spacing: int | None = None  # axis-bound: commit-axis

    # --------------------------------------------------------------------------
    #  Margins (visual-side, px)
    # --------------------------------------------------------------------------
    margin_left: float | None = None  # axis-symmetric (visual-side, px)
    margin_right: float | None = None  # axis-symmetric (visual-side, px)
    margin_top: float | None = None  # axis-symmetric (visual-side, px)
    margin_bottom: float | None = None  # axis-symmetric (visual-side, px)

    # --------------------------------------------------------------------------
    #  Strokes & geometry (px, except where noted)
    # --------------------------------------------------------------------------
    branch_line_width: int | None = None  # axis-symmetric
    commit_radius: int | None = None  # axis-symmetric
    commit_stroke_width: float | None = None  # axis-symmetric
    highlight_radius: int | None = None  # axis-symmetric
    merge_commit_style: MergeCommitStyle | None = None  # axis-symmetric (merge-dot style)
    arc_corner_radius_in_grid_units: float | None = None  # axis-symmetric
    branch_line_style: BranchLineStyle | None = None  # axis-symmetric (connector shape)
    label_offset_branch_axis_in_lanes: float | None = None  # axis-bound: branch-axis, sign from `label_side`
    branch_guide_width: float | None = None  # axis-symmetric
    branch_guide_dash: str | None = None
    guide_overshoot_in_rows: float | None = None  # axis-bound: commit-axis (applied symmetrically at both ends)

    # --------------------------------------------------------------------------
    #  Typography
    # --------------------------------------------------------------------------
    label_font_family: str | None = None
    label_font_family_small: str | None = None
    label_font_size: float | None = None  # axis-symmetric
    branch_label_font_size: float | None = None  # axis-symmetric
    hash_font_size: float | None = None  # axis-symmetric
    branch_name_pill_offset_commit_axis_in_rows: float | None = None  # axis-bound: commit-axis (signed)
    branch_name_pill_offset_branch_axis_in_lanes: float | None = None  # axis-bound: branch-axis (signed)
    pill_padding_x_in_font_sizes: float | None = None  # axis-symmetric (extra pill width beyond text)
    pill_padding_y_in_font_sizes: float | None = None  # axis-symmetric (extra pill height beyond font size)
    pill_corner_radius_in_font_sizes: float | None = None  # axis-symmetric (rounded pill corners)
    label_line_padding_in_font_sizes: float | None = (
        None  # axis-symmetric (extra height per line in a multi-line stack)
    )

    # --------------------------------------------------------------------------
    #  Pull-request visuals
    # --------------------------------------------------------------------------
    pull_request_dash: str | None = None
    pull_request_pill_offset_commit_axis_in_rows: float | None = None  # axis-bound: commit-axis (signed)
    pull_request_pill_offset_branch_axis_in_lanes: float | None = None  # axis-bound: branch-axis (signed)

    # --------------------------------------------------------------------------
    #  Label angles (degrees)
    # --------------------------------------------------------------------------
    branch_label_angle: float | None = None  # axis-symmetric (renderer rotation)
    commit_label_angle: float | None = None  # axis-symmetric (governs msg + hash + future tag)
    pull_request_label_angle: float | None = None  # axis-symmetric (PR pill)

    # --------------------------------------------------------------------------
    #  Box anchors (text-bearing primitives)
    # --------------------------------------------------------------------------
    # Each `(u, v) ∈ [0, 1]²` says where inside the primitive's un-rotated
    # bounding box the world anchor point sits — and equivalently where
    # rotation pivots, so the world point stays pinned regardless of the
    # resolved label angle. Commit labels split into `_before` / `_after`
    # because the resolver depends on per-commit `label_side`; the renderer
    # picks the field matching each commit's resolved side at draw time.
    branch_pill_anchor: BoxAnchor | None = None  # axis-symmetric (renderer geometry)
    pull_request_pill_anchor: BoxAnchor | None = None  # axis-symmetric (renderer geometry)
    commit_label_anchor_before: BoxAnchor | None = None  # axis-symmetric (renderer geometry; label_side="before")
    commit_label_anchor_after: BoxAnchor | None = None  # axis-symmetric (renderer geometry; label_side="after")

    # --------------------------------------------------------------------------
    #  Colours
    # --------------------------------------------------------------------------
    colors: dict[str, str] | None = None
    default_branch_color_cycle: list[str] | None = None
    label_color: str | None = None
    hash_color: str | None = None
    branch_guide_color: str | None = None
    commit_stroke_color: str | None = None
    branch_label_bg_opacity: float | None = None

    # --------------------------------------------------------------------------
    #  SVG background
    # --------------------------------------------------------------------------
    background_color: str | None = None
    """Optional fill for a full-canvas background rect; `None` keeps the SVG transparent."""

    # --------------------------------------------------------------------------
    #  Label-side defaults
    # --------------------------------------------------------------------------
    label_side_default: LabelSide = LabelSide.AFTER
    """Default `label_side` for branches that didn't set one on the `branch:`
    op. Lives on `Theme` so a future named theme can flip the diagram-wide
    default; not user-input on the `theme:` op today."""

    # --------------------------------------------------------------------------
    #  State-derived per-branch overrides
    # --------------------------------------------------------------------------
    branch_color_overrides: dict[str, str] = Field(default_factory=dict)
    """Hex colour overrides, keyed by `BranchState.id` (not name). Filled by
    the apply pass from `branch:` ops carrying a `color` field, then attached
    to the built `Theme`; not user-input on the `theme:` op."""

    branch_label_side_overrides: dict[str, LabelSide] = Field(default_factory=dict)
    """`label_side` overrides, keyed by `BranchState.id` (not name). Filled by
    the apply pass from `branch:` ops carrying a `label_side` field, then
    attached to the built `Theme`; not user-input on the `theme:` op."""

    # --------------------------------------------------------------------------
    #  Always-hold invariants
    # --------------------------------------------------------------------------
    @field_validator("branch_spacing", "commit_spacing")
    @classmethod
    def _spacings_must_be_positive(cls, v: int | None) -> int | None:
        """Reject `<= 0` spacings — zero collapses lanes / rows onto themselves."""
        if v is not None and v <= 0:
            raise ValueError("must be > 0")
        return v

    @field_validator("label_font_size", "branch_label_font_size", "hash_font_size")
    @classmethod
    def _font_sizes_must_be_positive(cls, v: float | None) -> float | None:
        """Reject `<= 0` font sizes — zero makes text invisible."""
        if v is not None and v <= 0:
            raise ValueError("must be > 0")
        return v

    @field_validator("branch_label_bg_opacity")
    @classmethod
    def _opacity_in_unit_range(cls, v: float | None) -> float | None:
        """Reject opacities outside `[0, 1]`."""
        if v is not None and not (0.0 <= v <= 1.0):
            raise ValueError("must be in [0, 1]")
        return v

    @field_validator(
        "branch_pill_anchor",
        "pull_request_pill_anchor",
        "commit_label_anchor_before",
        "commit_label_anchor_after",
    )
    @classmethod
    def _anchor_components_in_unit_range(cls, v: BoxAnchor | None) -> BoxAnchor | None:
        """Reject `BoxAnchor` values with a component outside `[0, 1]`."""
        return validate_box_anchor(v)

    # --------------------------------------------------------------------------
    #  Factory (subclasses provide a concrete implementation)
    # --------------------------------------------------------------------------
    @classmethod
    def build(cls, user_set: dict[str, Any]) -> Self:
        """Resolve a fully-populated `Theme` from the user-set field dict.

        Concrete subclasses (e.g. `DefaultTheme`) override this to
        orchestrate field-by-field resolution: explicit values from
        `user_set` win; everything else falls through to the
        subclass's `_resolve_<field>` classmethods.

        Args:
            user_set: Mapping from theme-field name to the value the
                user explicitly supplied via a `theme:` op. Fields the
                user didn't touch are absent.

        Returns:
            A fully-populated `Theme` instance.

        Raises:
            NotImplementedError: Always — `Theme` itself has no default-
                logic. Subclass and provide a concrete `build()`.
        """
        raise NotImplementedError(f"{cls.__name__} must implement build()")

    # --------------------------------------------------------------------------
    #  Pipeline boundary
    # --------------------------------------------------------------------------
    def split(self) -> "tuple[LayoutSettings, RendererSettings]":
        """Slice the resolved theme into the two pipeline-stage views.

        The layout stage consumes only `LayoutSettings`; the renderer
        stage consumes only `RendererSettings`. `Theme` itself stays at
        the orchestration layer and is not passed downstream — the
        architecture meta-test under `tests/architecture/` enforces
        that `gitsvg/layout/` and `gitsvg/render/` keep their imports
        narrow.

        `LayoutSettings` carries the layout-policy fields
        (`commit_row_mode`, `auto_lane_change`); `RendererSettings`
        structurally mirrors `Theme` and carries every field — the
        layout-policy ones ride along unused on the renderer slice.

        Returns:
            A `(layout_settings, renderer_settings)` pair carrying the
            two sub-views of the resolved theme.
        """
        # Late import to avoid a package-load cycle: `LayoutSettings` lives
        # under `gitsvg.layout`, `RendererSettings` under `gitsvg.render`,
        # both of which already import from `gitsvg.theme`.
        from gitsvg.layout._layout_settings import LayoutSettings
        from gitsvg.render._renderer_settings import RendererSettings

        return (
            LayoutSettings(commit_row_mode=self.commit_row_mode, auto_lane_change=self.auto_lane_change),
            RendererSettings(**self.model_dump()),
        )

    # --------------------------------------------------------------------------
    #  Resolved-pixel accessors for ratio-stored fields
    # --------------------------------------------------------------------------
    # Read-only: the renderer / canvas auto-fit / primitives read these
    # (e.g. `theme.arc_corner_radius`) and get the resolved pixel value,
    # computed lazily from the stored ratio × the relevant spacing.

    @property
    def arc_corner_radius(self) -> int | float:
        """Resolved pixel corner radius for branch-off / merge arcs."""
        return _resolve_int_or_float(
            self.arc_corner_radius_in_grid_units * min(self.branch_spacing, self.commit_spacing)
        )

    @property
    def label_offset(self) -> int | float:
        """Resolved pixel offset between a commit dot and its label, along the branch axis."""
        return _resolve_int_or_float(self.label_offset_branch_axis_in_lanes * self.branch_spacing)

    @property
    def guide_overshoot(self) -> int | float:
        """Resolved pixel overshoot — how far a branch guide extends past the commit-axis margin edges."""
        return _resolve_int_or_float(self.guide_overshoot_in_rows * self.commit_spacing)

    @property
    def pill_padding_x(self) -> int | float:
        """Resolved pill-padding-x (px) — extra width beyond the rendered text."""
        return _resolve_int_or_float(self.pill_padding_x_in_font_sizes * self.branch_label_font_size)

    @property
    def pill_padding_y(self) -> int | float:
        """Resolved pill-padding-y (px) — extra height beyond the font size."""
        return _resolve_int_or_float(self.pill_padding_y_in_font_sizes * self.branch_label_font_size)

    @property
    def pill_corner_radius(self) -> int | float:
        """Resolved pill corner radius (px) for `rx` / `ry`."""
        return _resolve_int_or_float(self.pill_corner_radius_in_font_sizes * self.branch_label_font_size)

    @property
    def label_line_padding(self) -> int | float:
        """Resolved extra height per line (px) in a multi-line label stack."""
        return _resolve_int_or_float(self.label_line_padding_in_font_sizes * self.label_font_size)

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


def _resolve_int_or_float(value: float) -> int | float:
    """Cast a whole-number float to int; return float otherwise.

    Used by `Theme`'s resolved-pixel properties so the SVG attribute
    formatting matches the pre-ratio defaults exactly (drawsvg writes
    integer values without a decimal point and float values with one).
    """
    return int(value) if value == int(value) else value
