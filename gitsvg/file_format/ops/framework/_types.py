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


HexColor = Annotated[str, Field(pattern=r"^#([0-9A-Fa-f]{3}|[0-9A-Fa-f]{6})$")]
"""Hex color, 3- or 6-digit form, with leading `#`. Case-insensitive."""


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
