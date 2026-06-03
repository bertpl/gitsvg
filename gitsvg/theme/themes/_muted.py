"""Muted theme — a muted, professional, mechanical look.

`MutedTheme` softens the branch palette and uses the plainer connector
and merge-dot styles. It pins three `_resolve_*` methods — the palette,
the connector style (`rounded`, pinned explicitly so it holds even if
the default's connector changes), and the merge-commit style
(`circle`); every other field inherits from `DefaultTheme`, so the two
stay in lockstep on geometry, spacings, typography, and label angles.

Selecting it is one field on a `theme` op: `{"op": "theme", "name":
"muted"}`.
"""

from gitsvg._value_types import BranchLineStyle, MergeCommitStyle
from gitsvg.theme._default_theme import DefaultTheme


class MutedTheme(DefaultTheme):
    """Muted palette, professional, mechanical look — rounded connectors, circle merge dots.

    Pins `_resolve_colors`, `_resolve_branch_line_style`, and
    `_resolve_merge_commit_style`; every other field inherits from
    `DefaultTheme`.
    """

    @classmethod
    def _resolve_colors(cls) -> dict[str, str]:
        """The muted branch palette — grayer, softer hues than the default."""
        return {
            "main": "#5c6370",
            "branch1": "#6a9f8d",
            "branch2": "#7b8fb2",
            "branch3": "#b07b8f",
            "branch4": "#9b8fb2",
        }

    @classmethod
    def _resolve_branch_line_style(cls) -> BranchLineStyle:
        """The rounded quarter-arc elbow connector."""
        return BranchLineStyle.ROUNDED

    @classmethod
    def _resolve_merge_commit_style(cls) -> MergeCommitStyle:
        """The plain circle merge-commit dot."""
        return MergeCommitStyle.CIRCLE
