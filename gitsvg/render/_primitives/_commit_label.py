"""Draw a commit's label — `msg` (primary lines) plus optional `hash` (secondary line).

Layout:

- Anchored `theme.label_offset` pixels to the side of the commit dot,
  per the commit's `label_side` (`"left"` or `"right"`).
- Multi-line `msg` is `split("\\n")` — each line drawn with
  `theme.label_font_size` text in `theme.label_color`.
- When `hash` is set, a smaller secondary line follows in
  `theme.hash_font_size` / `theme.hash_color`.
- All lines stack vertically with one consistent line height
  (`theme.label_font_size + 4`), centred on the dot's y.
- Highlighted commits get bold weight (700) on the `msg` lines; the
  hash line stays at regular weight regardless.
"""

import drawsvg as draw

from gitsvg.layout import LayoutCommit
from gitsvg.render._canvas import RenderCanvas
from gitsvg.render._geometry import branch_axis_to_x, commit_axis_to_y
from gitsvg.render._theme import Theme


def draw_commit_label(d: draw.Drawing, commit: LayoutCommit, canvas: RenderCanvas, theme: Theme) -> None:
    """Append a commit's label lines to the drawing.

    Skipped silently when the commit has neither `msg` nor `hash` to
    show.
    """
    lines = _build_lines(commit, theme)
    if not lines:
        return

    cx = branch_axis_to_x(commit.branch_pos, canvas)
    cy = commit_axis_to_y(commit.commit_pos, canvas)

    if commit.label_side == "left":
        anchor = "end"
        x = cx - theme.label_offset
    else:
        anchor = "start"
        x = cx + theme.label_offset

    line_height = theme.label_font_size + 4

    # Vertically centre the stack on the dot's y. Lines are drawn with
    # `dominant_baseline="middle"`, so a single line's y is the dot's y;
    # a stack of N lines spans (N-1) * line_height between centres.
    top_y = cy - (len(lines) - 1) * line_height / 2

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
