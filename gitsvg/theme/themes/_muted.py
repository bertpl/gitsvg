"""Muted theme — the pre-refresh default look, preserved as a named theme.

`MutedTheme` is the escape hatch back to the appearance the package
default carried before the saturation / merge-dot refresh. It pins
three `_resolve_*` methods to their pre-refresh values — the branch
palette, the connector style, and the merge-commit style; every other
field inherits from `DefaultTheme`, so the two themes stay in lockstep
on geometry, spacings, typography, and label angles. (The connector
pin currently coincides with the default's `rounded`; pinning it keeps
`muted` stable if the default's connector style changes later.)

Selecting it is one field on a `theme` op: `{"op": "theme", "name":
"muted"}`.
"""

from gitsvg.theme._branch_line_style import BranchLineStyle
from gitsvg.theme._default_theme import DefaultTheme
from gitsvg.theme._merge_commit_style import MergeCommitStyle


class MutedTheme(DefaultTheme):
    """The pre-refresh default look — softer palette, rounded connectors, circle merge dots.

    Pins `_resolve_colors`, `_resolve_branch_line_style`, and
    `_resolve_merge_commit_style` to the values the package default
    carried before the refresh. Every other field inherits from
    `DefaultTheme`.
    """

    @classmethod
    def _resolve_colors(cls) -> dict[str, str]:
        """The pre-refresh branch palette — same hues, a touch greyer/softer than today's default."""
        return {
            "main": "#5c6370",
            "branch1": "#6a9f8d",
            "branch2": "#7b8fb2",
            "branch3": "#b07b8f",
            "branch4": "#9b8fb2",
        }

    @classmethod
    def _resolve_branch_line_style(cls) -> BranchLineStyle:
        """The pre-refresh connector shape — the rounded quarter-arc elbow."""
        return BranchLineStyle.ROUNDED

    @classmethod
    def _resolve_merge_commit_style(cls) -> MergeCommitStyle:
        """The pre-refresh merge-commit dot style — the plain circle dot."""
        return MergeCommitStyle.CIRCLE
