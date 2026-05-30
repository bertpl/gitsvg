"""Merge-dot style builders — per-style commit-dot rendering and the registry.

`theme.merge_commit_style` selects how a merge commit's dot is drawn
(ordinary commits always use the plain `circle` dot):

- `circle` (default) — the plain dot: branch-colour fill,
  `commit_stroke_color` outline. Identical to an ordinary commit, so merge
  dots stay byte-identical to prior versions.
- `checkmark` — a hollow dot: fill and stroke swap (fill =
  `commit_stroke_color`, stroke = the branch colour at branch-line weight)
  with a branch-colour checkmark overlaid, marking the commit as a merge.

Each style is a `_draw_<style>(d, x, y, radius, color, theme)` builder that
owns the dot's full rendering at the given base radius; `_MERGE_DOT_BUILDERS`
maps each `MergeCommitStyle` to its builder, mirroring `_connector_styles`.
The `checkmark` dot ring is drawn `_CHECKMARK_DOT_RADIUS_SCALE`x the base
radius (a touch larger), while its tick stays sized to the base radius — so
the dot reads larger but the tick doesn't. Adding a style is a localized
change: a new enum member, a new `_draw_*`, and a new registry entry. The
exhaustiveness guard under `tests/architecture/` fails if a member lacks a
builder.
"""

from collections.abc import Callable

import drawsvg as draw

from gitsvg.render._renderer_settings import RendererSettings
from gitsvg.theme import MergeCommitStyle

# `checkmark` dot ring radius as a multiple of the base radius — the hollow
# merge dot reads a touch larger than an ordinary dot; its tick stays sized to
# the base radius, so the dot grows but the tick doesn't.
_CHECKMARK_DOT_RADIUS_SCALE = 1.1

# `checkmark` tick stroke width as a fraction of the base dot radius.
_CHECKMARK_TICK_WIDTH_IN_RADII = 0.32  # axis-symmetric (perceptual)

# `checkmark` tick vertices as (x, y) fractions of the base dot radius, relative
# to the dot centre (SVG y-down): a short arm down to the vertex, a long arm up
# to the right — the canonical check shape, sized to sit inside the dot and
# nudged slightly below centre so it reads optically centred.
_CHECKMARK_TICK_POINTS = (
    (-0.50, 0.08),
    (-0.16, 0.42),
    (0.52, -0.32),
)  # axis-symmetric (perceptual)


# ==================================================================================================
#  Style builders — each owns its full dot rendering at the given base radius
# ==================================================================================================
def _draw_circle(d: draw.Drawing, x: float, y: float, radius: float, color: str, theme: RendererSettings) -> None:
    """The plain dot: branch-colour fill, `commit_stroke_color` outline.

    Ordinary commits and `circle`-style merge commits share this body, so
    default output stays byte-identical to prior versions.
    """
    d.append(
        draw.Circle(
            x,
            y,
            radius,
            fill=color,
            stroke=theme.commit_stroke_color,
            stroke_width=theme.commit_stroke_width,
        )
    )


def _draw_checkmark(d: draw.Drawing, x: float, y: float, radius: float, color: str, theme: RendererSettings) -> None:
    """A hollow merge dot: swapped fill / stroke plus a branch-colour checkmark.

    The ring is `_CHECKMARK_DOT_RADIUS_SCALE`x the base radius, in the branch
    colour at branch-line weight, with `commit_stroke_color` fill; the tick
    stays sized to the base radius — so the dot reads larger but the tick
    doesn't.
    """
    d.append(
        draw.Circle(
            x,
            y,
            round(radius * _CHECKMARK_DOT_RADIUS_SCALE, 3),
            fill=theme.commit_stroke_color,
            stroke=color,
            stroke_width=theme.branch_line_width,
        )
    )
    (x0, y0), (x1, y1), (x2, y2) = _CHECKMARK_TICK_POINTS
    tick = draw.Path(
        stroke=color,
        stroke_width=radius * _CHECKMARK_TICK_WIDTH_IN_RADII,
        fill="none",
        stroke_linecap="round",
        stroke_linejoin="round",
    )
    tick.M(x + x0 * radius, y + y0 * radius)
    tick.L(x + x1 * radius, y + y1 * radius)
    tick.L(x + x2 * radius, y + y2 * radius)
    d.append(tick)


_MERGE_DOT_BUILDERS: dict[
    MergeCommitStyle, Callable[[draw.Drawing, float, float, float, str, RendererSettings], None]
] = {
    MergeCommitStyle.CIRCLE: _draw_circle,
    MergeCommitStyle.CHECKMARK: _draw_checkmark,
}
