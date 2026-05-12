"""Renderer-side theme — every presentational constant for the SVG output.

A `Theme` is the single object the renderer reads. It holds every
visual constant (spacing, sizes, colours, fonts, dashes, opacities)
plus two state-derived sections: per-branch colour overrides keyed by
branch id, and canvas presentational fields (spacing, margins) sourced
from a `canvas:` op.

The renderer never imports `State`. `build_theme(state)` is the bridge:
it walks state once at the layer boundary, copies the relevant
presentational hints onto a fresh `Theme`, and hands it to `render()`.
"""

from dataclasses import dataclass, field, replace

from gitsvg.state import State


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
    commit_spacing: int = 50
    margin_branch_axis_lower: int = 100
    margin_branch_axis_upper: int = 100
    margin_commit_axis_lower: int = 25
    margin_commit_axis_upper: int = 25

    # --------------------------------------------------------------------------
    #  Strokes & geometry (px)
    # --------------------------------------------------------------------------
    # Stroke widths and radii default to ints to match drawsvg's
    # int-formatted attribute output.
    branch_line_width: int = 2
    commit_radius: int = 5
    commit_stroke_width: float = 1.5
    highlight_radius: int = 7
    arc_corner_radius: int = 20
    label_offset: int = 12
    branch_guide_width: float = 0.7
    branch_guide_dash: str = "4,4"

    # --------------------------------------------------------------------------
    #  Typography
    # --------------------------------------------------------------------------
    label_font_family: str = "'Inter', 'Helvetica Neue', Helvetica, Arial, sans-serif"
    label_font_family_small: str = "Inter, sans-serif"
    label_font_size: int = 11
    branch_label_font_size: int = 11
    hash_font_size: int = 9
    branch_name_pill_offset: int = 25

    # --------------------------------------------------------------------------
    #  Pull-request visuals
    # --------------------------------------------------------------------------
    pull_request_dash: str = "6,4"
    pull_request_pill_offset: int = 25

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


DEFAULT_THEME = Theme()
"""Frozen reference for the package-default theme. Use `replace(DEFAULT_THEME, ...)` rather than mutating."""


def build_theme(state: State) -> Theme:
    """Resolve the `Theme` the renderer should consume for `state`.

    Starts from `DEFAULT_THEME` and folds in state-side presentational
    hints:

    - `state.branches[*].color` → `theme.branch_color_overrides[branch.id]`
      (keyed by id, not name — names can be reused across `remove`).
    - `state.canvas.branch_spacing` / `commit_spacing` / `margin_*` →
      matching `theme.*` fields (only when the user pinned them; `None`
      means "keep the default").

    Args:
        state: The validated state to derive presentational hints from.

    Returns:
        A new `Theme` that the renderer can consume directly.
    """
    theme = replace(DEFAULT_THEME)

    # --- per-branch colour overrides ------------------
    overrides: dict[str, str] = {}
    for branch in state.branches.values():
        if branch.color is not None:
            overrides[branch.id] = branch.color
    theme.branch_color_overrides = overrides

    # --- canvas presentational fields -----------------
    canvas = state.canvas
    if canvas is not None:
        if canvas.branch_spacing is not None:
            theme.branch_spacing = canvas.branch_spacing
        if canvas.commit_spacing is not None:
            theme.commit_spacing = canvas.commit_spacing
        if canvas.margin_branch_axis_lower is not None:
            theme.margin_branch_axis_lower = canvas.margin_branch_axis_lower
        if canvas.margin_branch_axis_upper is not None:
            theme.margin_branch_axis_upper = canvas.margin_branch_axis_upper
        if canvas.margin_commit_axis_lower is not None:
            theme.margin_commit_axis_lower = canvas.margin_commit_axis_lower
        if canvas.margin_commit_axis_upper is not None:
            theme.margin_commit_axis_upper = canvas.margin_commit_axis_upper

    return theme
