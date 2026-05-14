"""`build_theme(state)` — bridge state-side presentational hints into a renderer-ready `Theme`.

The `Theme` dataclass and its `DEFAULT_THEME` instance live at the
package root (`gitsvg/_theme.py`) so state can hold a live `Theme`
without inverting the layer direction. This module is the render-side
adapter: it walks state once at the layer boundary and returns the
fully-resolved theme the renderer reads.

The resolution order, lowest → highest precedence:

1. `state.theme` — the live `Theme` accumulated by `theme:` ops.
2. `state.branches[*].color` — explicit per-branch colour overrides
   write to `theme.branch_color_overrides[branch.id]`.

Per invariant #6 in `docs/architecture.md`, the `grid:` op is a
layout-only input; spacings, margins, and every other pixel-side
concern live exclusively on `theme:`. Nothing on `state.grid` flows
into the resolved theme.
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

    return theme
