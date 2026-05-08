"""Schema-export helper tests."""

import pytest

from gitsvg._file_format._schema import list_op_names, op_one_liner, op_schema, schema_index


def test_list_op_names_returns_canonical_order() -> None:
    # --- act --------------------------
    names = list_op_names()

    # --- assert -----------------------
    assert names == ["import", "canvas", "branch", "commit", "merge", "remove", "highlight"]


def test_op_schema_returns_json_schema_dict_for_known_op() -> None:
    # --- act --------------------------
    schema = op_schema("commit")

    # --- assert -----------------------
    assert isinstance(schema, dict)
    assert schema.get("type") == "object"
    assert "properties" in schema
    assert "op" in schema["properties"]
    assert "branch" in schema["properties"]


def test_op_schema_uses_alias_for_merge_from_field() -> None:
    # --- act --------------------------
    schema = op_schema("merge")

    # --- assert -----------------------
    assert "from" in schema["properties"]
    assert "from_" not in schema["properties"]
    assert "as" in schema["properties"]
    assert "as_" not in schema["properties"]


def test_op_schema_unknown_op_raises_keyerror() -> None:
    # --- act / assert -----------------
    with pytest.raises(KeyError):
        op_schema("rebase")


def test_op_one_liner_returns_first_line_of_docstring() -> None:
    # --- act --------------------------
    line = op_one_liner("import")

    # --- assert -----------------------
    assert line.startswith("Replay another file")


def test_schema_index_maps_every_op_to_a_non_empty_one_liner() -> None:
    # --- act --------------------------
    index = schema_index()

    # --- assert -----------------------
    assert list(index.keys()) == list_op_names()
    assert all(v.strip() for v in index.values())
