"""Visual constants for the renderer.

Hard-coded; will become theme-able when the deferred `theme:` op lands.
"""

# ==================================================================================================
#  Spacing (px)
# ==================================================================================================
BRANCH_SPACING = 100
COMMIT_SPACING = 50
MARGIN_BRANCH_AXIS_LOWER = 100
MARGIN_BRANCH_AXIS_UPPER = 100
MARGIN_COMMIT_AXIS_LOWER = 25
MARGIN_COMMIT_AXIS_UPPER = 25


# ==================================================================================================
#  Strokes & geometry (px)
# ==================================================================================================
BRANCH_LINE_WIDTH = 2
COMMIT_RADIUS = 5
COMMIT_STROKE_WIDTH = 1.5
HIGHLIGHT_RADIUS = 7
ARC_CORNER_RADIUS = 20
LABEL_OFFSET = 12
BRANCH_GUIDE_WIDTH = 0.7
BRANCH_GUIDE_DASH = "4,4"


# ==================================================================================================
#  Typography
# ==================================================================================================
LABEL_FONT_FAMILY = "'Inter', 'Helvetica Neue', Helvetica, Arial, sans-serif"
LABEL_FONT_FAMILY_SMALL = "Inter, sans-serif"
LABEL_FONT_SIZE = 11
BRANCH_LABEL_FONT_SIZE = 11
HASH_FONT_SIZE = 9
BRANCH_NAME_PILL_OFFSET = 25


# ==================================================================================================
#  Pull-request visuals
# ==================================================================================================
# Folded into the theme registry in v0.1.4 alongside the rest of this module.
PULL_REQUEST_DASH = "6,4"
"""Stroke dash pattern for the pull-request arc-and-line — visually distinguishes it from a real merge arc."""
PULL_REQUEST_PILL_OFFSET = 25
"""Pixel distance from the source-tip commit to the PR title pill; pill sits *above* the source tip (mirroring branch pills, which sit below their branch's start)."""


# ==================================================================================================
#  Colors
# ==================================================================================================
COLORS: dict[str, str] = {
    "main": "#5c6370",
    "branch1": "#7b8fb2",
    "branch2": "#6a9f8d",
    "branch3": "#b07b8f",
    "branch4": "#9b8fb2",
}
"""Hex colors keyed by the symbolic palette names used in `branch.color`."""

DEFAULT_BRANCH_COLORS: list[str] = ["branch1", "branch2", "branch3", "branch4"]
"""Cycle order for non-main branches when `branch.color` is omitted.

The first declared branch (typically `main`) defaults to `COLORS["main"]`;
subsequent branches cycle through these keys in declaration order,
wrapping back to the first key after the fourth.
"""

LABEL_COLOR = "#383838"
HASH_COLOR = "#707070"
BRANCH_GUIDE_COLOR = "#b8b8b8"
BRANCH_LABEL_BG_OPACITY = 0.85
