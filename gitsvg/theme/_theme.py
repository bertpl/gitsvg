"""Theme — every presentational constant for the SVG output.

A `Theme` is a first-class pipeline output alongside `State`. It
accumulates as the input file's `theme:` ops apply and as `branch:`
ops carry colour overrides, then flows to the renderer as the
resolved set of visual constants (spacings, sizes, colours, fonts,
dashes, opacities). Per-branch colour overrides live on
`branch_color_overrides`, keyed by `BranchState.id`.

Position/size fields with a natural anchor are stored as ratios
(suffixed `_in_lanes` / `_in_rows` / `_in_grid_units` /
`_in_font_sizes`) anchored to the relevant spacing or font size.
Pixel-valued accessors with the corresponding unsuffixed names
live as properties below the field block — read-only resolved
values that downstream consumers (renderer, canvas auto-fit,
primitives) read just as before. See `docs/architecture.md`
invariant #4 for the rule.
"""

from dataclasses import dataclass, field


@dataclass(slots=True)
class Theme:
    """Every presentational value the renderer reads.

    Field groups (spacing, geometry, typography, colours, pull-request
    visuals, branch colour overrides) mirror the module-level visual
    constants that lived in `gitsvg/` before they were absorbed into
    this dataclass.
    """

    # --------------------------------------------------------------------------
    #  Spacing (px)
    # --------------------------------------------------------------------------
    # Int defaults preserve byte-identical SVG attribute formatting:
    # drawsvg writes `width="300"` from int and `"300.0"` from float,
    # and the previous module-level constants were ints, producing the
    # int-formatted output that downstream consumers may be checking
    # against. `compute_canvas` re-introduces a float cast on
    # `margin_commit_axis_upper` so coordinate transforms keep producing
    # float y's.
    branch_spacing: int = 100  # axis-bound: branch-axis
    commit_spacing: int = 50  # axis-bound: commit-axis

    # --------------------------------------------------------------------------
    #  Margins (ratios; resolved via the unsuffixed-name properties below)
    # --------------------------------------------------------------------------
    margin_branch_axis_lower_in_lanes: float = 1.0  # axis-bound: branch-axis
    margin_branch_axis_upper_in_lanes: float = 1.0  # axis-bound: branch-axis
    margin_commit_axis_lower_in_rows: float = 0.5  # axis-bound: commit-axis
    margin_commit_axis_upper_in_rows: float = 0.5  # axis-bound: commit-axis

    # --------------------------------------------------------------------------
    #  Strokes & geometry (px, except where noted)
    # --------------------------------------------------------------------------
    # Stroke widths and pixel-valued radii default to ints to match
    # drawsvg's int-formatted attribute output.
    branch_line_width: int = 2  # axis-symmetric
    commit_radius: int = 5  # axis-symmetric
    commit_stroke_width: float = 1.5  # axis-symmetric
    highlight_radius: int = 7  # axis-symmetric
    arc_corner_radius_in_grid_units: float = 0.4  # axis-symmetric
    label_offset_branch_axis_in_lanes: float = 0.12  # direction-bound: branch-axis, sign from `label_side`
    branch_guide_width: float = 0.7  # axis-symmetric
    branch_guide_dash: str = "4,4"
    guide_overshoot_in_rows: float = 0.2  # axis-bound: commit-axis (applied symmetrically at both ends)

    # --------------------------------------------------------------------------
    #  Typography
    # --------------------------------------------------------------------------
    label_font_family: str = "'Inter', 'Helvetica Neue', Helvetica, Arial, sans-serif"
    label_font_family_small: str = "Inter, sans-serif"
    label_font_size: int = 11  # axis-symmetric
    branch_label_font_size: int = 11  # axis-symmetric
    hash_font_size: int = 9  # axis-symmetric
    branch_name_pill_offset_commit_axis_in_rows: float = -0.5  # axis-bound: commit-axis (signed)
    branch_name_pill_offset_branch_axis_in_lanes: float = 0.0  # axis-bound: branch-axis (signed)
    pill_padding_x_in_font_sizes: float = 12 / 11  # axis-symmetric (extra pill width beyond text)
    pill_padding_y_in_font_sizes: float = 8 / 11  # axis-symmetric (extra pill height beyond font size)
    pill_corner_radius_in_font_sizes: float = 4 / 11  # axis-symmetric (rounded pill corners)
    label_line_padding_in_font_sizes: float = 4 / 11  # axis-symmetric (extra height per line in a multi-line stack)

    # --------------------------------------------------------------------------
    #  Pull-request visuals
    # --------------------------------------------------------------------------
    pull_request_dash: str = "6,4"
    pull_request_pill_offset_commit_axis_in_rows: float = 0.5  # axis-bound: commit-axis (signed)
    pull_request_pill_offset_branch_axis_in_lanes: float = 0.0  # axis-bound: branch-axis (signed)

    # --------------------------------------------------------------------------
    #  Colours
    # --------------------------------------------------------------------------
    colors: dict[str, str] = field(
        default_factory=lambda: {
            "main": "#5c6370",
            "branch1": "#7b8fb2",
            "branch2": "#6a9f8d",
            "branch3": "#b07b8f",
            "branch4": "#9b8fb2",
        }
    )
    default_branch_color_cycle: list[str] = field(default_factory=lambda: ["branch1", "branch2", "branch3", "branch4"])
    label_color: str = "#383838"
    hash_color: str = "#707070"
    branch_guide_color: str = "#b8b8b8"
    branch_label_bg_opacity: float = 0.85

    # --------------------------------------------------------------------------
    #  SVG background
    # --------------------------------------------------------------------------
    background_color: str | None = None
    """Optional fill for a full-canvas background rect; `None` keeps the SVG transparent."""

    # --------------------------------------------------------------------------
    #  State-derived per-branch overrides
    # --------------------------------------------------------------------------
    branch_color_overrides: dict[str, str] = field(default_factory=dict)
    """Hex colour overrides, keyed by `BranchState.id` (not name)."""

    # --------------------------------------------------------------------------
    #  Resolved-pixel accessors for ratio-stored fields
    # --------------------------------------------------------------------------
    # Read-only: the renderer / canvas auto-fit / primitives read these
    # (e.g. `theme.margin_branch_axis_lower`) and get the resolved pixel
    # value, computed lazily from the stored ratio × the relevant
    # spacing. Storage is the user-facing ratio; reads are pixels.
    # `_resolve_int_or_float` casts whole-number results back to int so
    # the SVG attribute formatting matches the pre-ratio defaults exactly
    # (drawsvg writes `width="100"` from int and `width="100.0"` from
    # float; the byte-identical SVG output gate depends on this).

    @property
    def margin_branch_axis_lower(self) -> int | float:
        """Resolved pixel margin at the lower branch-axis end."""
        return _resolve_int_or_float(self.margin_branch_axis_lower_in_lanes * self.branch_spacing)

    @property
    def margin_branch_axis_upper(self) -> int | float:
        """Resolved pixel margin at the upper branch-axis end."""
        return _resolve_int_or_float(self.margin_branch_axis_upper_in_lanes * self.branch_spacing)

    @property
    def margin_commit_axis_lower(self) -> int | float:
        """Resolved pixel margin at the lower commit-axis end."""
        return _resolve_int_or_float(self.margin_commit_axis_lower_in_rows * self.commit_spacing)

    @property
    def margin_commit_axis_upper(self) -> int | float:
        """Resolved pixel margin at the upper commit-axis end."""
        return _resolve_int_or_float(self.margin_commit_axis_upper_in_rows * self.commit_spacing)

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


def _resolve_int_or_float(value: float) -> int | float:
    """Cast a whole-number float to int; return float otherwise.

    Used by `Theme`'s resolved-pixel properties so the SVG attribute
    formatting matches the pre-ratio defaults exactly (drawsvg writes
    integer values without a decimal point and float values with one).
    """
    return int(value) if value == int(value) else value


DEFAULT_THEME = Theme()
"""Frozen reference for the package-default theme. Use `dataclasses.replace(DEFAULT_THEME, ...)` rather than mutating; ratio fields use the `_in_*` suffixed names."""
