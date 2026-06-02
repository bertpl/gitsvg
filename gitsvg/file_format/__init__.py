"""Pydantic models and JSON Schema export for the gitsvg input format.

This package defines the gitsvg operations as pydantic models
(`gitsvg.file_format.ops`) and exposes the schema-export helpers
(`list_op_names`, `op_schema`, `op_one_liner`, `schema_index`) used by
the `gitsvg schema` CLI command.
"""

from gitsvg.file_format._label_side import LabelSide
from gitsvg.file_format._schema import list_op_names, op_one_liner, op_schema, schema_index

__all__ = ["LabelSide", "list_op_names", "op_one_liner", "op_schema", "schema_index"]
