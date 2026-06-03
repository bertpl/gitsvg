"""Draw a commit's label — `msg` (primary lines) plus optional `hash` (secondary line).

Layout:

- Anchored `theme.label_offset_branch_axis_in_lanes` × lane width to
  the branch-axis side of the commit dot resolved by
  `theme.branch_label_side(commit.branch_id)` (`"before"` = lower-index
  side, `"after"` = higher-index side). The renderer maps that
  axis-relative side to a pixel direction per orientation via the
  geometry module.
- Where the multi-line stack sits relative to that world point comes
  from the box anchor resolved by
  `gitsvg/render/_anchor_resolution.py`. Vertical orientations place
  the stack to the side of the dot horizontally
  (`(1.0, 0.5)` / `(0.0, 0.5)`); horizontal orientations place it
  above or below the dot vertically (`(0.5, 1.0)` / `(0.5, 0.0)`).
- Per-line SVG `text-anchor` is derived from the box anchor's `u`
  (`start` if 0.0, `middle` if 0.5, `end` if 1.0); each line keeps
  `dominant_baseline="middle"`.
- Multi-line `msg` is `split("\\n")` — each line drawn with
  `theme.label_font_size` text in `theme.label_color`.
- When `hash` is set, a smaller secondary line follows in
  `theme.hash_font_size` / `theme.hash_color`.
- All lines stack vertically with one consistent line height
  (`theme.label_font_size + theme.label_line_padding`).
- Highlighted commits get bold weight (700) on the `msg` lines; the
  hash line stays at regular weight regardless.
"""

import drawsvg as draw

from gitsvg._value_types import LabelSide
from gitsvg.layout import LayoutCommit
from gitsvg.render._anchor_resolution import rotated_target
from gitsvg.render._canvas import RenderCanvas
from gitsvg.render._geometry import offset_position
from gitsvg.render._renderer_settings import RendererSettings

# Maps the resolved box-anchor `u` (horizontal fraction in the un-rotated
# bounding box) to the SVG `text-anchor` attribute that aligns each line
# accordingly when drawn at the anchor x. The three canonical values
# (`0.0`, `0.5`, `1.0`) cover every position the commit-label resolver
# returns today; non-canonical `u` would need explicit pixel-x maths
# instead of the discrete SVG attribute and isn't supported today.
_SVG_TEXT_ANCHOR: dict[float, str] = {
    0.0: "start",
    0.5: "middle",
    1.0: "end",
}


def draw_commit_label(d: draw.Drawing, commit: LayoutCommit, canvas: RenderCanvas, theme: RendererSettings) -> None:
    """Append a commit's label lines to the drawing.

    Skipped silently when the commit has neither `msg` nor `hash` to
    show.
    """
    lines = _build_lines(commit, theme)
    if not lines:
        return

    label_side = theme.branch_label_side(commit.branch_id)

    # Branch-axis offset: signed along the branch axis. Positive = toward
    # higher branch-axis index ("after" side); negative = toward lower
    # ("before" side).
    if label_side == LabelSide.BEFORE:
        branch_axis_offset_in_lanes = -theme.label_offset_branch_axis_in_lanes
    else:
        branch_axis_offset_in_lanes = theme.label_offset_branch_axis_in_lanes

    box_u, box_v = (
        theme.commit_label_anchor_before if label_side == LabelSide.BEFORE else theme.commit_label_anchor_after
    )
    text_anchor = _SVG_TEXT_ANCHOR[box_u]

    x, cy = offset_position(
        anchor_branch_pos=commit.branch_pos,
        anchor_commit_pos=commit.commit_pos,
        branch_axis_offset_in_lanes=branch_axis_offset_in_lanes,
        commit_axis_offset_in_rows=0,
        canvas=canvas,
    )

    line_height = theme.label_font_size + theme.label_line_padding
    max_font_size = max(font_size for _, font_size, _, _ in lines)

    # Stack-vertical anchor derived from the resolved `v`: 0 → stack
    # top edge at `cy`, 1 → bottom edge at `cy`, 0.5 → centered. The
    # two-term form keeps the line-span offset and the visible-edge
    # adjustment separate, so for v ∈ {0, 0.5, 1} the resulting float
    # arithmetic matches the legacy three-branch formula bit-for-bit
    # (associativity-sensitive rewrites would shift results by 1 ULP).
    top_y = cy - box_v * (len(lines) - 1) * line_height + (0.5 - box_v) * max_font_size

    target = rotated_target(d, theme.commit_label_angle, x, cy)
    for index, (text, font_size, color, weight) in enumerate(lines):
        target.append(
            draw.Text(
                text,
                font_size,
                x,
                top_y + index * line_height,
                text_anchor=text_anchor,
                dominant_baseline="middle",
                fill=color,
                font_family=theme.label_font_family,
                font_weight=weight,
            )
        )


def _build_lines(commit: LayoutCommit, theme: RendererSettings) -> list[tuple[str, int, str, str]]:
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
