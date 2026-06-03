"""Table label layout — pure pixel geometry + cell-text preparation.

The renderer's `table`-mode label layout (commit `hash` / branch / message
as fixed-width columns beside the graph) is built from two stateless
pieces, both unaware of `Theme` / `Layout`:

- `_columns` — which fields are active, their order, per-column left-edge
  offsets, and the total table region width.
- `_text` — flattening a multi-line message to one line and ellipsizing a
  cell to its column width.

The renderer supplies resolved widths, fonts, and the absolute table
origin; this package owns the math.
"""

from .columns import TableColumn, TableColumns, TableField, compute_table_columns
from .text import fit_text, flatten_message

__all__ = [
    "TableColumn",
    "TableColumns",
    "TableField",
    "compute_table_columns",
    "fit_text",
    "flatten_message",
]
