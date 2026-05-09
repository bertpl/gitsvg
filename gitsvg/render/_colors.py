"""Resolve a branch's display colour from its declaration order and overrides.

Order of precedence (per `format.md` § "Defaults and themes"):

1. Explicit `branch.color` from the op input.
2. The first declared branch defaults to `COLORS["main"]`.
3. Subsequent branches cycle through `DEFAULT_BRANCH_COLORS` in declaration
   order, wrapping after the fourth.
"""

from gitsvg.render._constants import COLORS, DEFAULT_BRANCH_COLORS
from gitsvg.state import State


def resolve_branch_color(state: State, branch_name: str) -> str:
    """Return the hex colour string to use for `branch_name`.

    Args:
        state: Current state engine output (carries declaration order
            and any explicit colour overrides per branch).
        branch_name: The branch whose colour to resolve.

    Returns:
        A hex colour string (always set; falls back to the main colour
        when the branch is unknown — defensive only).
    """
    branch = state.branches.get(branch_name)
    if branch is None:
        return COLORS["main"]
    if branch.color is not None:
        return branch.color

    declaration_index = state.branch_order.index(branch_name) if branch_name in state.branch_order else 0
    if declaration_index == 0:
        return COLORS["main"]

    cycle_index = (declaration_index - 1) % len(DEFAULT_BRANCH_COLORS)
    return COLORS[DEFAULT_BRANCH_COLORS[cycle_index]]
