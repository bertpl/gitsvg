"""Constrained pydantic field type aliases shared across op models.

Centralized so the per-field constraints (no-whitespace ids, hex
colors, non-negative integers, etc.) are defined once and referenced
by name in each op model.
"""

from typing import Annotated

from pydantic import Field

# ==================================================================================================
#  String type aliases
# ==================================================================================================
IdStr = Annotated[str, Field(pattern=r"^\S+$")]
"""Non-empty string with no whitespace anywhere.

Used for ids and names that act as references inside the diagram —
commit ids, branch names, pull-request ids, and the `auto` sentinel
on `commit.hash`.
"""


NonEmptyStr = Annotated[str, Field(min_length=1)]
"""Non-empty string with no other constraints.

Used for free-form text fields where whitespace is meaningful — e.g.
commit messages, pull-request titles, file paths.
"""


HexColor = Annotated[str, Field(pattern=r"^#([0-9A-Fa-f]{3,4}|[0-9A-Fa-f]{6}|[0-9A-Fa-f]{8})$")]
"""Hex color with an optional alpha channel — 3-, 4-, 6-, or 8-digit form,
with leading `#`. Case-insensitive. The 4- and 8-digit forms carry a
trailing alpha nibble / byte (`#RGBA`, `#RRGGBBAA`); the 3- and 6-digit
forms are fully opaque. The alpha channel lets a fill compose over
whatever sits behind it — e.g. a zebra band over the background, or a
translucent `background_color`."""


# ==================================================================================================
#  Numeric type aliases
# ==================================================================================================
NonNegativeInt = Annotated[int, Field(ge=0)]
"""Non-negative integer — for slot indices and slot counts."""


NonNegativeFloat = Annotated[float, Field(ge=0)]
"""Non-negative float — for pixel distances.

Zero is allowed because diagrams may be script-generated and corner
cases can legitimately produce zero spacing.
"""
