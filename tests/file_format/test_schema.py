"""Schema-export helper tests."""

import pytest

from gitsvg.file_format._schema import list_op_names, op_one_liner, op_schema, schema_index


def test_list_op_names_returns_canonical_order() -> None:
    # --- act --------------------------
    names = list_op_names()

    # --- assert -----------------------
    assert names == [
        "import",
        "grid",
        "theme",
        "branch",
        "commit",
        "merge",
        "pull_request",
        "remove",
        "highlight",
    ]


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


# ==================================================================================================
#  Descriptions pipeline — class docstring + per-field Field(description=...)
# ==================================================================================================
@pytest.mark.parametrize(
    "op_name", ["import", "grid", "branch", "commit", "merge", "pull_request", "remove", "highlight"]
)
def test_op_schema_carries_class_docstring_as_description(op_name: str) -> None:
    """Every op's class docstring surfaces as the schema's top-level `description`."""
    # --- act --------------------------
    schema = op_schema(op_name)

    # --- assert -----------------------
    assert "description" in schema
    assert schema["description"].strip()


def test_op_schema_carries_per_field_description() -> None:
    """A `Field(description=...)` argument propagates to the field's schema entry."""
    # --- act --------------------------
    schema = op_schema("commit")

    # --- assert -----------------------
    # `branch` is a required field with an explicit description.
    branch_field = schema["properties"]["branch"]
    assert "description" in branch_field
    assert branch_field["description"] == "Branch the commit lives on."


def test_op_schema_optional_field_carries_description() -> None:
    """Optional fields also propagate their `Field(description=...)` to the schema."""
    # --- act --------------------------
    schema = op_schema("pull_request")

    # --- assert -----------------------
    title_field = schema["properties"]["title"]
    assert "description" in title_field
    assert "rendered" in title_field["description"].lower()
