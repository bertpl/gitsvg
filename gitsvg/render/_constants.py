"""Visual constants for the v0.0.3 renderer.

Hard-coded for v0.0.3; post-0.1.0 these become theme-able through the
deferred `theme:` op. Names and values match
`design/v0_0_3_seed_inventory.md` § "TL;DR".
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
LABEL_FONT_SIZE = 11
BRANCH_LABEL_FONT_SIZE = 11
HASH_FONT_SIZE = 9
BRANCH_NAME_PILL_OFFSET = 25


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
