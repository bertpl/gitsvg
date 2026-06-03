"""Draw the table label region — message + hash columns with branch tip pills.

`table` mode replaces the free-floating commit labels and the branch-start
pills with a fixed-column table beside the graph (right of the rightmost
lane). One row per commit (table mode forces unique rows), reusing the
commit-axis y-transform so each row aligns with its dot. A commit may be the
ref target of several branches, so its message cell can carry several tip
pills — each in its branch's color, in declaration order — before the
(ellipsis-truncated) message.
"""

from collections.abc import Callable

import drawsvg as draw

from gitsvg.layout import Layout, LayoutBranch
from gitsvg.render._canvas import RenderCanvas
from gitsvg.render._geometry import grid_to_pixel
from gitsvg.render._label_widths import pill_width
from gitsvg.render._renderer_settings import RendererSettings
from gitsvg.render._table import TableColumns, TableField, fit_text, flatten_message

from .pill import draw_pill_box


def draw_commit_table(
    d: draw.Drawing,
    layout: Layout,
    columns: TableColumns,
    table_x_origin: float,
    canvas: RenderCanvas,
    theme: RendererSettings,
    color_of: Callable[[str], str],
) -> None:
    """Append the table label region (columns + tip pills) to the drawing.

    Args:
        d: The drawing to append to.
        layout: The resolved layout — commits to render, branches for the
            tip pills (read in declaration order).
        columns: The active columns + region width from `compute_table_columns`.
        table_x_origin: Pixel x of the table region's left edge.
        canvas: Effective canvas spec; supplies each row's y via the
            commit-axis transform.
        theme: Resolved theme — fonts, colors, pill metrics, column widths.
        color_of: Maps a branch id to its rendered color (for the tip pills).
    """
    # Branches whose ref points at each commit, in declaration order
    # (`layout.branches` is declaration order). A commit may host several.
    pills_by_commit: dict[str, list[LayoutBranch]] = {}
    for branch in layout.branches:
        if branch.tip_commit_id is not None:
            pills_by_commit.setdefault(branch.tip_commit_id, []).append(branch)

    # Half of the pill's internal horizontal padding reads as a tighter gap
    # between adjacent pills and before the message than the full padding.
    # One horizontal unit: cell content is inset by it on each side, and it's
    # the gap between adjacent pills and before the message.
    pad = theme.table_cell_padding_x
    pill_height = theme.branch_label_font_size + theme.pill_padding_y

    for commit in layout.commits.values():
        row_y = grid_to_pixel(0, commit.commit_pos, canvas)[1]
        for column in columns.columns:
            content_left = table_x_origin + column.x_offset + pad
            content_width = column.width - 2 * pad
            if column.field == TableField.MESSAGE:
                # Tip pills first, then the message in the width that remains.
                x = content_left
                for branch in pills_by_commit.get(commit.id, []):
                    width = pill_width(branch.name, theme)
                    draw_pill_box(
                        d,
                        left=x,
                        top=row_y - pill_height / 2,
                        width=width,
                        height=pill_height,
                        text=branch.name,
                        color=color_of(branch.id),
                        theme=theme,
                    )
                    x += width + pad
                pill_run = x - content_left
                _draw_cell_text(
                    d,
                    text=flatten_message(commit.msg) if commit.msg else "",
                    x=content_left + pill_run,
                    y=row_y,
                    max_width=content_width - pill_run,
                    font_size=theme.label_font_size,
                    color=theme.label_color,
                    bold=commit.highlight,
                    theme=theme,
                )
            elif column.field == TableField.HASH:
                _draw_cell_text(
                    d,
                    text=commit.hash or "",
                    x=content_left,
                    y=row_y,
                    max_width=content_width,
                    font_size=theme.hash_font_size,
                    color=theme.hash_color,
                    bold=False,
                    theme=theme,
                )


def _draw_cell_text(
    d: draw.Drawing,
    *,
    text: str,
    x: float,
    y: float,
    max_width: float,
    font_size: float,
    color: str,
    bold: bool,
    theme: RendererSettings,
) -> None:
    """Append one left-anchored, vertically-centered table cell, ellipsized to `max_width`.

    Args:
        d: The drawing to append to.
        text: Cell text (already flattened for the message column).
        x: Left edge of the text in pixels.
        y: Row center in pixels (text is centered on it).
        max_width: Available width in pixels; a non-positive value draws nothing.
        font_size: Text size in pixels.
        color: Fill color.
        bold: Whether to render bold (highlighted message).
        theme: Supplies the font family.
    """
    if not text or max_width <= 0:
        return
    fitted = fit_text(text, max_width, theme.label_font_family, font_size, bold=bold)
    if not fitted:
        return
    d.append(
        draw.Text(
            fitted,
            font_size,
            x,
            y,
            text_anchor="start",
            dominant_baseline="middle",
            fill=color,
            font_family=theme.label_font_family,
            font_weight="700" if bold else "400",
        )
    )
