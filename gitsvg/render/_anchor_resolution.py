"""Resolve per-element anchor points for text-bearing render primitives.

Each text-bearing primitive (branch-name pill, PR-title pill, commit
label stack) has an un-rotated bounding box and a world anchor point
the box is positioned against. This module returns a single
`BoxAnchor` value — a normalised `(u, v)` point in `[0, 1]²` saying
where in the un-rotated bounding box the world anchor point sits:

- `(0, 0)` = top-left corner of the un-rotated bounding box.
- `(1, 1)` = bottom-right.
- `(0.5, 0.5)` = centre.

Under rotation, the same `(u, v)` is also the rotation pivot — so the
world point stays pinned regardless of angle. The label-angle work
that consumes this lives outside v0.1.8; the rotation surface lands
in a separate step. Today every angle is 0°, so primitives use only
the placement aspect of `BoxAnchor`.

This module replaces the orientation-conditional anchor logic that
previously lived inline in each primitive (`_branch_pill.py`,
`_commit_label.py`): a single point of resolution per element kind,
so future angle / anchor configurability can plug in without
re-touching every primitive.

Renderer-internal: nothing about `BoxAnchor` surfaces on the `Theme`.
The shape is deliberately compatible with the user-facing
`RendererSettings` fields planned for the Theme architecture refactor
that follows v0.1.8; graduation should be exposing what's already here
rather than redesigning.
"""

from typing import Literal

from gitsvg.theme import OrientationLiteral

# ==================================================================================================
#  Public types
# ==================================================================================================
BoxAnchor = tuple[float, float]
"""Normalised `(u, v)` in `[0, 1]²` — where in an un-rotated bounding
box the world anchor point sits (and equivalently where rotation
pivots around)."""

LabelSideLiteral = Literal["before", "after"]
"""Branch-axis-index side. `"before"` = lower-index side; `"after"` =
higher-index side. Consumed by commit-label anchor resolution; the
two pill resolvers ignore it."""


# ==================================================================================================
#  Per-element resolvers
# ==================================================================================================
def resolve_branch_pill_anchor(orientation: OrientationLiteral) -> BoxAnchor:
    """Resolve the branch-name pill's box anchor for the given orientation.

    Vertical orientations (`bt`, `tb`): pill centred on the world
    point — `(0.5, 0.5)`. Horizontal orientations: pill anchored on
    its edge nearest the start commit, so the resolved offset becomes
    a minimum gap and a long branch name extends further into the
    start-side margin without crowding the start commit dot.
    `lr` → right-edge anchored (`(1.0, 0.5)`);
    `rl` → left-edge anchored (`(0.0, 0.5)`).

    Args:
        orientation: Active diagram orientation.

    Returns:
        The `(u, v)` saying where in the pill rect the world point
        sits.
    """
    if orientation == "lr":
        return (1.0, 0.5)
    if orientation == "rl":
        return (0.0, 0.5)
    return (0.5, 0.5)


def resolve_pr_pill_anchor(orientation: OrientationLiteral) -> BoxAnchor:
    """Resolve the PR-title pill's box anchor.

    Always `(0.5, 0.5)` — the PR pill's offset point lives away from
    the start-side margin concern the branch pill addresses, so it
    centres on the offset point in every orientation.

    Args:
        orientation: Active diagram orientation. Unused today;
            accepted so callers can route both pill resolvers through
            a common pattern.

    Returns:
        Always `(0.5, 0.5)`.
    """
    del orientation
    return (0.5, 0.5)


def resolve_commit_label_anchor(
    orientation: OrientationLiteral,
    label_side: LabelSideLiteral,
) -> BoxAnchor:
    """Resolve the commit-label stack's box anchor.

    Vertical orientations (`bt`, `tb`) place the stack to the side of
    the commit dot along the branch axis (screen-x). The stack
    extends outward horizontally; vertically it stays centred on the
    dot. `before` → stack's right-middle at the world point
    (`(1.0, 0.5)`); `after` → left-middle (`(0.0, 0.5)`).

    Horizontal orientations (`lr`, `rl`) place the stack above or
    below the commit dot along the branch axis (screen-y). The stack
    extends outward vertically; horizontally it stays centred on the
    dot. `before` → stack's bottom-middle at the world point
    (`(0.5, 1.0)`); `after` → top-middle (`(0.5, 0.0)`).

    Args:
        orientation: Active diagram orientation.
        label_side: Branch-axis-index side resolved by the layout
            engine.

    Returns:
        The `(u, v)` saying where in the stack's un-rotated bounding
        box the world point sits.
    """
    if orientation in ("bt", "tb"):
        return (1.0, 0.5) if label_side == "before" else (0.0, 0.5)
    return (0.5, 1.0) if label_side == "before" else (0.5, 0.0)
