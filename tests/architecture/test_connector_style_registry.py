"""Architecture guard for the connector-style registry.

Every `BranchLineStyle` must have a builder in `_CONNECTOR_BUILDERS`, so a
future enum value added without a builder fails the suite here rather
than `KeyError`-ing at render time.
"""

from gitsvg.render._primitives.connector_styles import _CONNECTOR_BUILDERS
from gitsvg.theme import BranchLineStyle


def test_every_branch_line_style_has_a_builder() -> None:
    # --- assert -----------------------
    assert set(_CONNECTOR_BUILDERS) == set(BranchLineStyle)
