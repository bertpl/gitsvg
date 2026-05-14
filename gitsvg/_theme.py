"""Theme — every presentational constant for the SVG output.

A `Theme` is the single object the renderer reads, and the single
object state mutates as `theme:` ops apply. It holds every visual
constant (spacing, sizes, colours, fonts, dashes, opacities) plus
two presentational sections that flow in from state ops: per-branch
colour overrides keyed by branch id, and canvas presentational fields
(spacing, margins) sourced from a `canvas:` op.

`Theme` lives at the package root because both state and render depend
on it. State holds a live `Theme` that accumulates `theme:` op
patches; the renderer reads the resolved value. The bridging adapter
`build_theme(state)` lives in `gitsvg/render/_theme.py` (which is the
layer that knows about both halves).

Every field carries a `Classification:` line in its docstring,
enforced by the meta-test in `tests/architecture/`. See
`docs/architecture.md` invariant #2 for the taxonomy.
"""

from dataclasses import dataclass, field


@dataclass(slots=True)
class Theme:
    """Every presentational value the renderer reads.

    Field groups (spacing, geometry, typography, colours, pull-request
    visuals, canvas presentational overrides, branch colour overrides)
    mirror the module-level visual constants that lived in `gitsvg/`
    before they were absorbed into this dataclass.
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
    branch_spacing: int = 100
    """Pixel distance between adjacent branch-axis slots. Classification: axis-bound: branch-axis."""

    commit_spacing: int = 50
    """Pixel distance between adjacent commit-axis slots. Classification: axis-bound: commit-axis."""

    margin_branch_axis_lower: int = 100
    """Branch-axis margin at the lower end (lane 0 side). Classification: axis-bound: branch-axis."""

    margin_branch_axis_upper: int = 100
    """Branch-axis margin at the upper end (highest-lane side). Classification: axis-bound: branch-axis."""

    margin_commit_axis_lower: int = 25
    """Commit-axis margin at the lower end (oldest-commit side). Classification: axis-bound: commit-axis."""

    margin_commit_axis_upper: int = 25
    """Commit-axis margin at the upper end (newest-commit side). Classification: axis-bound: commit-axis."""

    # --------------------------------------------------------------------------
    #  Strokes & geometry (px)
    # --------------------------------------------------------------------------
    # Stroke widths and radii default to ints to match drawsvg's
    # int-formatted attribute output.
    branch_line_width: int = 2
    """Stroke width of branch lines and arcs. Classification: axis-symmetric."""

    commit_radius: int = 5
    """Radius of regular commit dots. Classification: axis-symmetric."""

    commit_stroke_width: float = 1.5
    """Stroke width of the white outline around commit dots. Classification: axis-symmetric."""

    highlight_radius: int = 7
    """Radius of highlighted commit dots (enlarged variant). Classification: axis-symmetric."""

    arc_corner_radius: int = 20
    """Quarter-arc corner radius for branch-off and merge connectors. Classification: axis-symmetric."""

    label_offset: int = 12
    """Pixel offset between a commit dot and its label, along the branch axis. Direction is set by the commit's `label_side`. Classification: direction-bound: branch-axis, set by `label_side`."""

    branch_guide_width: float = 0.7
    """Stroke width of the dashed branch-guide lines. Classification: axis-symmetric."""

    branch_guide_dash: str = "4,4"
    """SVG `stroke-dasharray` value for branch guides. Classification: not-applicable."""

    # --------------------------------------------------------------------------
    #  Typography
    # --------------------------------------------------------------------------
    label_font_family: str = "'Inter', 'Helvetica Neue', Helvetica, Arial, sans-serif"
    """CSS font-family stack for all standard label text. Classification: not-applicable."""

    label_font_family_small: str = "Inter, sans-serif"
    """CSS font-family stack reserved for small-text contexts. Classification: not-applicable."""

    label_font_size: int = 11
    """Font size (px) of the primary commit-message label line. Classification: axis-symmetric."""

    branch_label_font_size: int = 11
    """Font size (px) of the text inside branch-name and PR-title pills. Classification: axis-symmetric."""

    hash_font_size: int = 9
    """Font size (px) of the secondary commit-hash label line. Classification: axis-symmetric."""

    branch_name_pill_offset: int = 25
    """Pixel offset of the branch-name pill below the branch's start point in screen y (toward the lower commit-axis end). Classification: direction-bound: commit-axis, toward lower index."""

    # --------------------------------------------------------------------------
    #  Pull-request visuals
    # --------------------------------------------------------------------------
    pull_request_dash: str = "6,4"
    """SVG `stroke-dasharray` value for pull-request connectors. Classification: not-applicable."""

    pull_request_pill_offset: int = 25
    """Pixel offset of the PR-title pill above the source-tip commit in screen y (toward the upper commit-axis end). Classification: direction-bound: commit-axis, toward upper index."""

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
    """Named hex colours; branches reference these by name. Classification: not-applicable."""

    default_branch_color_cycle: list[str] = field(default_factory=lambda: ["branch1", "branch2", "branch3", "branch4"])
    """Ordered colour names assigned to branches in declaration order when no explicit colour is set. Classification: not-applicable."""

    label_color: str = "#383838"
    """Fill colour for the primary commit-message label line. Classification: not-applicable."""

    hash_color: str = "#707070"
    """Fill colour for the secondary commit-hash label line. Classification: not-applicable."""

    branch_guide_color: str = "#b8b8b8"
    """Stroke colour for the dashed branch-guide lines. Classification: not-applicable."""

    branch_label_bg_opacity: float = 0.85
    """Fill opacity for the branch-name and PR-title pill backgrounds. Classification: not-applicable."""

    # --------------------------------------------------------------------------
    #  SVG background
    # --------------------------------------------------------------------------
    background_color: str | None = None
    """Optional fill for a full-canvas background rect; `None` keeps the SVG transparent. Classification: not-applicable."""

    # --------------------------------------------------------------------------
    #  State-derived per-branch overrides
    # --------------------------------------------------------------------------
    branch_color_overrides: dict[str, str] = field(default_factory=dict)
    """Hex colour overrides, keyed by `BranchState.id` (not name). Classification: not-applicable."""


DEFAULT_THEME = Theme()
"""Frozen reference for the package-default theme. Use `dataclasses.replace(DEFAULT_THEME, ...)` rather than mutating."""
