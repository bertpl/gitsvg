"""JSON Schema export helpers for the gitsvg input format.

These helpers back the `gitsvg schema` CLI command. The export is
per-op (one schema per operation) — file-level constraints
(import-first, etc.) are documented in prose rather than encoded in
JSON Schema.
"""

from typing import Any

from gitsvg._format.ops import OP_BY_NAME, OP_NAMES


# ==================================================================================================
#  Public API
# ==================================================================================================
def list_op_names() -> list[str]:
    """Return the names of all operations, in canonical order."""
    return list(OP_NAMES)


def op_schema(op_name: str) -> dict[str, Any]:
    """Return the JSON Schema for a single operation.

    Args:
        op_name: One of the names returned by `list_op_names()`.

    Returns:
        A JSON Schema dict describing a valid line for that op, with
        field aliases (e.g. `from`, `as`) used in place of Python
        attribute names.

    Raises:
        KeyError: If `op_name` is not a known operation.
    """
    if op_name not in OP_BY_NAME:
        raise KeyError(op_name)
    return OP_BY_NAME[op_name].model_json_schema(by_alias=True)


def op_one_liner(op_name: str) -> str:
    """Return the one-line description of an operation.

    Sourced from the first non-empty line of the model's class
    docstring.

    Args:
        op_name: One of the names returned by `list_op_names()`.

    Returns:
        The first line of the model's docstring, or an empty string if
        no docstring is set.

    Raises:
        KeyError: If `op_name` is not a known operation.
    """
    if op_name not in OP_BY_NAME:
        raise KeyError(op_name)
    doc = (OP_BY_NAME[op_name].__doc__ or "").strip()
    return doc.splitlines()[0] if doc else ""


def schema_index() -> dict[str, str]:
    """Return a mapping of op_name to one-line description, in canonical order."""
    return {name: op_one_liner(name) for name in OP_NAMES}
