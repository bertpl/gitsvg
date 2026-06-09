r"""`BoxAnchor` — normalized `(u, v)` location inside an un-rotated bounding box.

A `BoxAnchor` is a `(u, v)` pair in `[0, 1]²` that says where inside a
text-bearing primitive's un-rotated bounding box the world anchor
point sits:

- `(0, 0)` = top-left corner of the un-rotated bounding box.
- `(1, 1)` = bottom-right.
- `(0.5, 0.5)` = center.

Under rotation, the same `(u, v)` is also the rotation pivot — so the
world point stays pinned regardless of the resolved label angle.

User-facing on the `theme:` op (`branch_pill_anchor`,
`pull_request_pill_anchor`, `commit_label_anchor_before`,
`commit_label_anchor_after`); each defaults to a per-orientation value
chosen for un-rotated text in `DefaultTheme._resolve_*_anchor`. JSONL
input accepts a two-element array (e.g. `\"branch_pill_anchor\": [0.5, 0.5]`).

Stored as a plain `tuple[float, float]` so Pydantic accepts a JSON
array directly; per-component invariants (`u, v ∈ [0, 1]`) are
enforced by validators on the carrier model.
"""

BoxAnchor = tuple[float, float]
"""`(u, v)` in `[0, 1]²` — where inside an un-rotated bounding box the
world anchor point (and equivalent rotation pivot) sits."""


def validate_box_anchor(value: BoxAnchor | None) -> BoxAnchor | None:
    """Reject `BoxAnchor` values with a component outside `[0, 1]`.

    Args:
        value: A two-element tuple of floats, or `None` (unset).

    Returns:
        The value unchanged when valid.

    Raises:
        ValueError: When either component is outside `[0, 1]`.
    """
    if value is None:
        return value
    u, v = value
    if not (0.0 <= u <= 1.0 and 0.0 <= v <= 1.0):
        raise ValueError(f"BoxAnchor components must be in [0, 1] (got {value})")
    return value
