"""Draw a commit's label — `msg` (primary lines) plus optional `hash` (secondary line).

Layout:

- Anchored `theme.label_offset` pixels to the side of the commit dot,
  per the commit's `label_side` (`"before"` or `"after"` — the
  branch-axis-index side; the renderer maps to a pixel side per
  orientation, currently bottom-to-top only).
- Multi-line `msg` is `split("\\n")` — each line drawn with
  `theme.label_font_size` text in `theme.label_color`.
- When `hash` is set, a smaller secondary line follows in
  `theme.hash_font_size` / `theme.hash_color`.
- All lines stack vertically with one consistent line height
  (`theme.label_font_size + theme.label_line_padding`), centred on
  the dot's y.
- Highlighted commits get bold weight (700) on the `msg` lines; the
  hash line stays at regular weight regardless.
"""

import drawsvg as draw

from gitsvg.layout import LayoutCommit
from gitsvg.render._canvas import RenderCanvas
from gitsvg.render._geometry import offset_position
from gitsvg.theme import Theme


def draw_commit_label(d: draw.Drawing, commit: LayoutCommit, canvas: RenderCanvas, theme: Theme) -> None:
    """Append a commit's label lines to the drawing.

    Skipped silently when the commit has neither `msg` nor `hash` to
    show.
    """
    lines = _build_lines(commit, theme)
    if not lines:
        return

    # Branch-axis offset: signed along the branch axis. Positive = toward
    # higher branch-axis index ("after" side); negative = toward lower
    # ("before" side).
    if commit.label_side == "before":
        branch_axis_offset_in_lanes = -theme.label_offset_branch_axis_in_lanes
    else:
        branch_axis_offset_in_lanes = theme.label_offset_branch_axis_in_lanes

    # Text-anchor depends on orientation. In vertical orientations
    # (`bt`, `tb`) the branch axis is screen-x, so the anchor sits left or
    # right of the dot and the text flows outward horizontally — `text-
    # anchor="end"` aligns the text's right edge to a `before`-side
    # anchor (text extends leftward), `start` aligns the left edge to an
    # `after`-side anchor (text extends rightward). In horizontal
    # orientations (`lr`, `rl`) the branch axis is screen-y, so the
    # anchor sits above or below the dot and the text should be centred
    # horizontally on the dot's x — `text-anchor="middle"` is the right
    # choice. (`text_anchor` is always horizontal alignment in SVG; it
    # doesn't rotate with our notion of branch axis.)
    is_vertical = canvas.orientation in ("bt", "tb")
    if is_vertical:
        anchor = "end" if commit.label_side == "before" else "start"
    else:
        anchor = "middle"

    x, cy = offset_position(
        anchor_branch_pos=commit.branch_pos,
        anchor_commit_pos=commit.commit_pos,
        branch_axis_offset_in_lanes=branch_axis_offset_in_lanes,
        commit_axis_offset_in_rows=0,
        canvas=canvas,
    )

    line_height = theme.label_font_size + theme.label_line_padding

    # Stack-vertical anchor:
    #
    # - **Vertical orientations** (`bt`, `tb`): the branch line is also
    #   vertical and the stack extends horizontally outward (left/right
    #   of the dot via `text_anchor=end/start`), so the stack's vertical
    #   extent never crosses the line. Centre the stack on the dot's y
    #   — `top_y = cy - (N-1) * line_height / 2`. (Lines use
    #   `dominant_baseline="middle"`, so each line's y is its vertical
    #   centre; a stack of N lines spans `(N-1) * line_height` between
    #   the outermost line centres.)
    #
    # - **Horizontal orientations** (`lr`, `rl`): the branch line is
    #   horizontal and the stack also extends vertically — centring the
    #   stack on `cy` would push half the lines across the branch line.
    #   Anchor the stack edge nearest the line at `cy` instead, so
    #   `theme.label_offset_branch_axis_in_lanes` becomes the minimum
    #   gap between the line and the nearest text edge regardless of
    #   line count. `before` → stack extends *upward* from `cy` (bottom-
    #   line bottom edge sits at `cy`); `after` → stack extends
    #   *downward* (top-line top edge sits at `cy`).
    if is_vertical:
        top_y = cy - (len(lines) - 1) * line_height / 2
    else:
        max_font_size = max(font_size for _, font_size, _, _ in lines)
        if commit.label_side == "before":
            top_y = cy - max_font_size / 2 - (len(lines) - 1) * line_height
        else:
            top_y = cy + max_font_size / 2

    for index, (text, font_size, color, weight) in enumerate(lines):
        d.append(
            draw.Text(
                text,
                font_size,
                x,
                top_y + index * line_height,
                text_anchor=anchor,
                dominant_baseline="middle",
                fill=color,
                font_family=theme.label_font_family,
                font_weight=weight,
            )
        )


def _build_lines(commit: LayoutCommit, theme: Theme) -> list[tuple[str, int, str, str]]:
    """Return the line stack as `(text, font_size, color, font_weight)` tuples.

    Order: each `msg` split on `"\\n"` becomes a primary line; the
    optional `hash` follows as a single secondary line.
    """
    lines: list[tuple[str, int, str, str]] = []
    msg_weight = "700" if commit.highlight else "400"
    if commit.msg is not None:
        for msg_line in commit.msg.split("\n"):
            lines.append((msg_line, theme.label_font_size, theme.label_color, msg_weight))
    if commit.hash is not None:
        lines.append((commit.hash, theme.hash_font_size, theme.hash_color, "400"))
    return lines
