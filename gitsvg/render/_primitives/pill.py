"""Shared pill primitive — a filled rounded rectangle with centered white text.

Used by the branch-name pill (drawn at a branch's start in `inline` mode) and
by the table tip pills (a branch's name at its ref-target commit, inside the
message column in `table` mode). Callers compute the rect's top-left corner;
this appends the rect + centered label to the given target (a `draw.Drawing`
or a rotation group).
"""

import drawsvg as draw

from gitsvg.render._renderer_settings import RendererSettings


def draw_pill_box(
    target: draw.Drawing | draw.Group,
    *,
    left: float,
    top: float,
    width: float,
    height: float,
    text: str,
    color: str,
    theme: RendererSettings,
    font_size: float | None = None,
) -> None:
    """Append a pill (rounded rect + centered white text) to `target`.

    Args:
        target: A `draw.Drawing` or rotation `Group` to append to.
        left: Rect left edge in pixels.
        top: Rect top edge in pixels.
        width: Rect width in pixels.
        height: Rect height in pixels.
        text: Label text, centered inside the rect.
        color: Fill color for the rect.
        theme: Supplies corner radius, background opacity, and font family.
        font_size: Text size; defaults to `theme.branch_label_font_size`.
    """
    fs = theme.branch_label_font_size if font_size is None else font_size
    corner = theme.pill_corner_radius
    target.append(
        draw.Rectangle(
            left,
            top,
            width,
            height,
            rx=corner,
            ry=corner,
            fill=color,
            opacity=theme.branch_label_bg_opacity,
        )
    )
    target.append(
        draw.Text(
            text,
            fs,
            left + width / 2,
            top + height / 2,
            text_anchor="middle",
            dominant_baseline="middle",
            fill="white",
            font_family=theme.label_font_family,
            font_weight="500",
        )
    )
