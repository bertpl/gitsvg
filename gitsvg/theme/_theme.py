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

from gitsvg.theme._orientation import OrientationLiteral


@dataclass(slots=True)
class Theme:
    """Every presentational value the renderer reads.

    Field groups (orientation, spacing, geometry, typography, colours,
    pull-request visuals, branch colour overrides) mirror the
    module-level visual constants that lived in `gitsvg/` before they
    were absorbed into this dataclass.
    """

    # --------------------------------------------------------------------------
    #  Orientation
    # --------------------------------------------------------------------------
    # Drives the renderer's grid → pixel mapping and the per-orientation
    # default values for spacings, margins, and pill offsets resolved by
    # `gitsvg/theme/_resolve.py`. Always concrete (never `None`); default
    # `"bt"` preserves byte-identical output for inputs that don't set
    # `theme.orientation` explicitly.
    orientation: OrientationLiteral = "bt"  # axis-symmetric (input-side selector)

    # --------------------------------------------------------------------------
    #  Spacing (px; `None` = use the orientation-resolved default)
    # --------------------------------------------------------------------------
    # `None` means "still default": the resolver in
    # `gitsvg/theme/_resolve.py` fills the value at end of state stage
    # per orientation. Defaults: vertical orientations (`bt`, `tb`)
    # → `branch_spacing=100, commit_spacing=50`; horizontal orientations
    # (`lr`, `rl`) → swapped to `branch_spacing=50, commit_spacing=100`.
    # Stored as int when whole-number so SVG attribute formatting matches
    # the byte-identical baseline (drawsvg writes `width="100"` from int
    # and `width="100.0"` from float).
    branch_spacing: int | None = None  # axis-bound: branch-axis
    commit_spacing: int | None = None  # axis-bound: commit-axis

    # --------------------------------------------------------------------------
    #  Margins (visual-side, px; `None` = use the orientation-resolved default)
    # --------------------------------------------------------------------------
    # Field name is orientation-invariant (`margin_left` is always the
    # visually-left margin). `None` means "still default": the resolver
    # in `gitsvg/theme/_resolve.py` fills the value at end of state stage
    # from `branch_spacing` / `commit_spacing` per the current orientation.
    # User overrides are absolute pixels.
    margin_left: float | None = None  # axis-symmetric (visual-side, px)
    margin_right: float | None = None  # axis-symmetric (visual-side, px)
    margin_top: float | None = None  # axis-symmetric (visual-side, px)
    margin_bottom: float | None = None  # axis-symmetric (visual-side, px)

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
    # Per-orientation default fills via `_resolve.py`: vertical
    # orientations (`bt`, `tb`) use `0.12` (the historical default);
    # horizontal orientations (`lr`, `rl`) use `0.24` so the resolved
    # pixel offset stays at ~12 px (matches BT) instead of halving with
    # the swapped branch_spacing.
    label_offset_branch_axis_in_lanes: float | None = None  # axis-bound: branch-axis, sign from `label_side`
    branch_guide_width: float = 0.7  # axis-symmetric
    branch_guide_dash: str = "4,4"
    # Per-orientation default fills via `_resolve.py`: vertical
    # orientations (`bt`, `tb`) use `0.25`; horizontal orientations
    # (`lr`, `rl`) use `0.5` to give guides enough reach to cover the
    # branch-pill area in the wider start-side margin.
    guide_overshoot_in_rows: float | None = None  # axis-bound: commit-axis (applied symmetrically at both ends)

    # --------------------------------------------------------------------------
    #  Typography
    # --------------------------------------------------------------------------
    label_font_family: str = "'Inter', 'Helvetica Neue', Helvetica, Arial, sans-serif"
    label_font_family_small: str = "Inter, sans-serif"
    label_font_size: int = 11  # axis-symmetric
    branch_label_font_size: int = 11  # axis-symmetric
    hash_font_size: int = 9  # axis-symmetric
    # Pill-offset defaults flip with orientation (resolver fills `None`):
    # vertical orientations use the commit-axis component (`-0.5` rows below
    # the branch start), horizontal orientations use the branch-axis component
    # (`-0.5` lanes above the branch start). Keeps the pill's text always
    # perpendicular to the offset direction, regardless of orientation.
    branch_name_pill_offset_commit_axis_in_rows: float | None = None  # axis-bound: commit-axis (signed)
    branch_name_pill_offset_branch_axis_in_lanes: float | None = None  # axis-bound: branch-axis (signed)
    pill_padding_x_in_font_sizes: float = 12 / 11  # axis-symmetric (extra pill width beyond text)
    pill_padding_y_in_font_sizes: float = 8 / 11  # axis-symmetric (extra pill height beyond font size)
    pill_corner_radius_in_font_sizes: float = 4 / 11  # axis-symmetric (rounded pill corners)
    label_line_padding_in_font_sizes: float = 4 / 11  # axis-symmetric (extra height per line in a multi-line stack)

    # --------------------------------------------------------------------------
    #  Pull-request visuals
    # --------------------------------------------------------------------------
    pull_request_dash: str = "2,6"
    # Same pattern as the branch-name pill, mirrored: vertical orientations
    # use commit-axis (`+0.5` rows above the tip), horizontal orientations
    # use branch-axis (`+0.5` lanes below the tip).
    pull_request_pill_offset_commit_axis_in_rows: float | None = None  # axis-bound: commit-axis (signed)
    pull_request_pill_offset_branch_axis_in_lanes: float | None = None  # axis-bound: branch-axis (signed)

    # --------------------------------------------------------------------------
    #  Colours
    # --------------------------------------------------------------------------
    colors: dict[str, str] = field(
        default_factory=lambda: {
            "main": "#5c6370",
            "branch1": "#6a9f8d",
            "branch2": "#7b8fb2",
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
    # (e.g. `theme.arc_corner_radius`) and get the resolved pixel
    # value, computed lazily from the stored ratio × the relevant
    # spacing. Storage is the user-facing ratio; reads are pixels.
    # `_resolve_int_or_float` casts whole-number results back to int so
    # the SVG attribute formatting matches the pre-ratio defaults exactly
    # (drawsvg writes `width="100"` from int and `width="100.0"` from
    # float; the byte-identical SVG output gate depends on this).
    #
    # Margins are not in this set: they are stored as already-resolved
    # pixel values (filled by `_resolve.resolve_defaults` at end of state
    # stage when the user left them as `None`). See invariant #4 in
    # `docs/architecture.md`.

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
