"""Architecture guard for the lane-change-style registry.

Every `BranchLineStyle` must have a builder in `_LANE_CHANGE_BUILDERS`, so a
future enum value added without a lane-change builder fails the suite here
rather than `KeyError`-ing at render time. Parallels
`test_connector_style_registry.py` for the branch-off / merge registry.
"""

from gitsvg.render._primitives.connector_styles import _LANE_CHANGE_BUILDERS
from gitsvg.theme import BranchLineStyle


def test_every_branch_line_style_has_a_lane_change_builder() -> None:
    # --- assert -----------------------
    assert set(_LANE_CHANGE_BUILDERS) == set(BranchLineStyle)
