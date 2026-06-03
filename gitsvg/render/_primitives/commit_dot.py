"""Draw a single commit dot at its layout position."""

import drawsvg as draw

from gitsvg._shared.value_types import MergeCommitStyle
from gitsvg.layout import LayoutCommit
from gitsvg.render._canvas import RenderCanvas
from gitsvg.render._geometry import grid_to_pixel
from gitsvg.render._renderer_settings import RendererSettings

from .merge_dot_styles import _MERGE_DOT_BUILDERS


def draw_commit_dot(
    d: draw.Drawing, commit: LayoutCommit, color: str, canvas: RenderCanvas, theme: RendererSettings
) -> None:
    """Append a commit dot to the drawing.

    Ordinary commits draw the plain `circle` dot. Merge commits draw the
    style `theme.merge_commit_style` selects (`circle` / `checkmark`),
    dispatched through the `merge_dot_styles` registry. The base radius is
    `theme.highlight_radius` when highlighted, else `theme.merge_commit_radius`
    for a merge commit, else `theme.commit_radius`; the `checkmark` dot enlarges
    its ring from there while its tick stays at the base size. The bold label is
    wired separately in the label primitive.
    """
    x, y = grid_to_pixel(commit.branch_pos, commit.commit_pos, canvas)
    style = theme.merge_commit_style if commit.is_merge else MergeCommitStyle.CIRCLE
    if commit.highlight:
        radius = theme.highlight_radius
    elif commit.is_merge:
        radius = theme.merge_commit_radius
    else:
        radius = theme.commit_radius
    _MERGE_DOT_BUILDERS[style](d, x, y, radius, color, theme)
