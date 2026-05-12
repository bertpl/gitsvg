"""`build_theme(state)` — bridge state-side presentational hints into a renderer-ready `Theme`.

The `Theme` dataclass and its `DEFAULT_THEME` instance live at the
package root (`gitsvg/_theme.py`) so state can hold a live `Theme`
without inverting the layer direction. This module is the render-side
adapter: it walks state once at the layer boundary and returns the
fully-resolved theme the renderer reads.

The resolution order, lowest → highest precedence:

1. `state.theme` — the live `Theme` accumulated by `theme:` ops.
2. `state.canvas` — `branch_spacing` / `commit_spacing` / `margin_*`
   fields from a `canvas:` op overlay matching theme fields.
3. `state.branches[*].color` — explicit per-branch colour overrides
   write to `theme.branch_color_overrides[branch.id]`.

Steps 2 and 3 are *specific-over-general*: a `canvas:` spacing pin and
a per-branch colour beat anything the theme palette set.
"""

import copy

from gitsvg._theme import Theme
from gitsvg.state import State


def build_theme(state: State) -> Theme:
    """Resolve the `Theme` the renderer should consume for `state`.

    Args:
        state: The validated state to derive presentational hints from.

    Returns:
        A new `Theme` carrying the resolved values; mutating the
        returned object does not affect `state.theme`.
    """
    theme = copy.deepcopy(state.theme)

    # --- per-branch colour overrides ------------------
    for branch in state.branches.values():
        if branch.color is not None:
            theme.branch_color_overrides[branch.id] = branch.color

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
