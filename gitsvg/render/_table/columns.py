"""Column geometry for the table label layout — pure, pixel-space, stateless.

Given the configured field widths, compute which fields are active (width > 0),
pack them left-to-right in the fixed `message · hash` order with an inter-field
gutter, and report each column's left-edge offset (relative to the table
region's origin) plus the total region width. A `0`-width field is omitted
entirely and its space reclaimed — the next field shifts left as if the disabled
one never existed.

The branch name is *not* a column: it renders as a colored pill prefixed before
the message on its branch's tip-commit row (a renderer concern, not geometry).
The columns here are the commit metadata fields only — message and hash.

These functions know nothing about `Theme`, `Layout`, or the renderer; they
operate on plain pixel widths so they can be unit-tested in isolation. The
renderer supplies the resolved widths + gutter and adds the absolute table
origin on top of the returned offsets.
"""

from dataclasses import dataclass
from enum import StrEnum


class TableField(StrEnum):
    """One metadata field of a commit, rendered as a table column.

    Fixed render order is `MESSAGE`, then `HASH` (Fork-like: the subject
    column first, the short id after).
    """

    MESSAGE = "message"
    HASH = "hash"


# Fixed left-to-right field order; column order is not configurable.
_FIELD_ORDER: tuple[TableField, ...] = (TableField.MESSAGE, TableField.HASH)


@dataclass(slots=True)
class TableColumn:
    """One active table column — its field, content width, and left-edge offset.

    Attributes:
        field: Which commit metadata field this column carries.
        width: Column content width in pixels (always `> 0`; `0`-width
            fields are dropped before a column is created).
        x_offset: Pixels from the table region's origin to this column's
            left edge.
    """

    field: TableField
    width: float
    x_offset: float


@dataclass(slots=True)
class TableColumns:
    """The laid-out active columns plus the total table region width.

    Attributes:
        columns: Active columns (width > 0) in fixed field order, each
            carrying its left-edge `x_offset` relative to the table origin.
        width: Total table region width in pixels — the sum of active
            column widths plus the inter-column gutters; `0` when no field
            is active.
    """

    columns: list[TableColumn]
    width: float


def compute_table_columns(
    message_width: float,
    hash_width: float,
    *,
    gutter: float,
) -> TableColumns:
    """Lay out the active table columns and report the region width.

    Fields with a width of `0` are dropped (the column is omitted and its
    space reclaimed); surviving fields keep the fixed `message · hash`
    order, packed left-to-right with `gutter` pixels between adjacent
    columns (no gutter before the first or after the last).

    Args:
        message_width: Message-column width in pixels (`0` disables it).
        hash_width: Hash-column width in pixels (`0` disables the column).
        gutter: Pixel spacing between adjacent active columns.

    Returns:
        A `TableColumns` with the active columns (each carrying its
        left-edge offset) and the total region width.
    """
    widths = {TableField.MESSAGE: message_width, TableField.HASH: hash_width}
    active = [field for field in _FIELD_ORDER if widths[field] > 0]

    columns: list[TableColumn] = []
    x = 0.0
    for i, field in enumerate(active):
        width = float(widths[field])
        columns.append(TableColumn(field=field, width=width, x_offset=x))
        x += width
        if i < len(active) - 1:
            x += gutter
    return TableColumns(columns=columns, width=x)
