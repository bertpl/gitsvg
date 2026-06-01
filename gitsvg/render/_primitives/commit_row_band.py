"""Draw a single commit-row band — a full-span zebra stripe for one row.

Bands sit at the very bottom of the z-order, just above the optional
background rect and below the branch guides. One band is drawn per
alternate commit-axis row when `theme.commit_row_band_color` is visible;
they aid row-tracking the way a git GUI's striped commit list does, and
work in any orientation (the stripe follows the commit axis).
"""

import drawsvg as draw

from gitsvg.render._canvas import RenderCanvas
from gitsvg.render._geometry import commit_row_band_rect


def draw_commit_row_band(d: draw.Drawing, commit_pos: int, color: str, canvas: RenderCanvas) -> None:
    """Append a full-span band rect for a single commit-axis row.

    Args:
        d: The drawing to append the band rect to.
        commit_pos: Commit-axis slot index of the row to band.
        color: Resolved fill (3/4/6/8-digit hex); an alpha channel
            composes the band over the background.
        canvas: Effective canvas spec — supplies the band's span and
            orientation.
    """
    x, y, width, height = commit_row_band_rect(commit_pos, canvas)
    d.append(draw.Rectangle(x, y, width, height, fill=color))
