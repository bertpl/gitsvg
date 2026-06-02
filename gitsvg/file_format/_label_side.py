"""LabelSide enum — branch-axis-index side commit labels render on.

Two values, both branch-axis-index relative (orientation-invariant on
the layout side; the renderer maps to a pixel side per the active
`theme.orientation`):

- `LabelSide.BEFORE` — lower-index side of the branch axis.
- `LabelSide.AFTER` — higher-index side.

User-facing on the `branch:` op (`label_side` field); resolved into a
concrete value by the layout engine (`after` is the package default
when a branch op omits the field); consumed by the renderer at
draw time when picking commit-label positioning.

Members carry the canonical short-code string values (`"before"`,
`"after"`) so the enum interoperates transparently with JSON / Pydantic
serialization and with code that still compares against raw strings.
"""

from enum import StrEnum


class LabelSide(StrEnum):
    """Branch-axis-index side commit labels render on."""

    BEFORE = "before"
    AFTER = "after"
