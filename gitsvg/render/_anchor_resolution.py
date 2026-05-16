"""Renderer-side rotation helper for text-bearing primitives.

`BoxAnchor` values live on `RendererSettings` as user-facing fields
(`branch_pill_anchor`, `pull_request_pill_anchor`,
`commit_label_anchor_before`, `commit_label_anchor_after`); the
primitives read them directly. What stays here is the small wrap
helper that turns a resolved angle plus world point into an SVG
`<g transform="rotate(...)">` group, or a no-op pass-through at 0°.

Under rotation, the world anchor point is also the rotation pivot —
the `BoxAnchor` `(u, v)` chosen for the element determines both where
the un-rotated bounding box sits relative to the world point and
where rotation pivots, so the world point stays pinned regardless of
angle.
"""

import drawsvg as draw


def rotated_target(
    target: draw.Drawing | draw.Group,
    angle: float,
    pivot_x: float,
    pivot_y: float,
) -> draw.Drawing | draw.Group:
    """Return the drawsvg target a primitive should append its elements to.

    At `angle == 0`, returns `target` unchanged so no transform-wrap
    element is emitted and the resulting SVG stays byte-identical to
    the un-rotated path. At any non-zero angle, creates a `<g
    transform="rotate(...)">` group around `(pivot_x, pivot_y)`,
    appends it to `target`, and returns the group so the caller's
    primitives end up inside the rotated frame.

    Centralises the rotation pattern shared across the three text-
    bearing primitives — each wraps its rect + text (or stack of
    text lines) in the same single-rotate-transform group when its
    resolved label angle is non-zero.

    Args:
        target: Parent drawsvg target (a `Drawing` or another `Group`).
        angle: Resolved rotation angle in degrees. `0` skips the wrap.
        pivot_x: Pixel x of the rotation pivot — typically the world
            anchor point, so the `BoxAnchor` stays at that screen
            position under rotation.
        pivot_y: Pixel y of the rotation pivot.

    Returns:
        `target` when `angle == 0`; otherwise a freshly-appended
        rotated `Group`.
    """
    if angle == 0:
        return target
    group = draw.Group(transform=f"rotate({angle}, {pivot_x}, {pivot_y})")
    target.append(group)
    return group
