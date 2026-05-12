"""Branch colour resolution at render time.

The single helper `resolve_branch_color(branch_id, declaration_index, theme)`
implements the cycle: explicit per-branch override wins, otherwise the
first branch (index 0) takes the theme's `"main"` palette colour and
subsequent branches cycle through `default_branch_color_cycle`. Primitives
call this as they emit each branch / commit / arc / PR.
"""

from gitsvg._theme import Theme


def resolve_branch_color(branch_id: str, declaration_index: int, theme: Theme) -> str:
    """Return the hex colour for a branch.

    Args:
        branch_id: Stable `BranchState.id` for the branch in question.
            Used to look up an explicit override in
            `theme.branch_color_overrides`.
        declaration_index: 0-based position of the branch in
            declaration order (matching `state.branch_order` /
            `Layout.branches` order). Drives the default cycle.
        theme: The resolved theme; supplies the palette and overrides.

    Returns:
        A hex colour string the renderer can use directly.
    """
    explicit = theme.branch_color_overrides.get(branch_id)
    if explicit is not None:
        return explicit
    if declaration_index == 0:
        return theme.colors["main"]
    cycle = theme.default_branch_color_cycle
    return theme.colors[cycle[(declaration_index - 1) % len(cycle)]]
