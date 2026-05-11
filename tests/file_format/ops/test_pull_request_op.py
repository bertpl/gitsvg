"""Schema tests for the `pull_request` op model."""

import pytest
from pydantic import ValidationError

from gitsvg.file_format.ops import OP_ADAPTER, PullRequestOp


# ==================================================================================================
#  Happy path
# ==================================================================================================
def test_minimal_valid_pull_request() -> None:
    # --- arrange ----------------------
    raw = {"op": "pull_request", "from": "feat", "into": "main"}

    # --- act --------------------------
    op = OP_ADAPTER.validate_python(raw)

    # --- assert -----------------------
    assert isinstance(op, PullRequestOp)
    assert op.from_ == "feat"
    assert op.into == "main"
    assert op.id is None
    assert op.title is None


def test_all_fields_set() -> None:
    # --- arrange ----------------------
    raw = {
        "op": "pull_request",
        "id": "pr1",
        "from": "feat",
        "into": "main",
        "title": "Add the thing",
    }

    # --- act --------------------------
    op = PullRequestOp.model_validate(raw)

    # --- assert -----------------------
    assert op.id == "pr1"
    assert op.from_ == "feat"
    assert op.into == "main"
    assert op.title == "Add the thing"


def test_from_field_uses_alias() -> None:
    """The `from` JSON key maps to the `from_` model attribute (Python keyword clash)."""
    # --- arrange ----------------------
    raw = {"op": "pull_request", "from": "feat", "into": "main"}

    # --- act --------------------------
    op = PullRequestOp.model_validate(raw)

    # --- assert -----------------------
    assert op.from_ == "feat"
    assert not hasattr(op, "from")


# ==================================================================================================
#  Required-field validation
# ==================================================================================================
@pytest.mark.parametrize(
    "raw",
    [
        {"op": "pull_request"},
        {"op": "pull_request", "from": "feat"},
        {"op": "pull_request", "into": "main"},
    ],
)
def test_missing_required_field_rejected(raw: dict) -> None:
    # --- act / assert -----------------
    with pytest.raises(ValidationError):
        OP_ADAPTER.validate_python(raw)


# ==================================================================================================
#  Unknown-field rejection (extra="forbid")
# ==================================================================================================
def test_unknown_field_rejected() -> None:
    # --- arrange ----------------------
    raw = {"op": "pull_request", "from": "feat", "into": "main", "foo": "bar"}

    # --- act / assert -----------------
    with pytest.raises(ValidationError):
        OP_ADAPTER.validate_python(raw)


# ==================================================================================================
#  Field-type checks
# ==================================================================================================
def test_empty_title_rejected() -> None:
    # --- arrange ----------------------
    raw = {"op": "pull_request", "from": "feat", "into": "main", "title": ""}

    # --- act / assert -----------------
    with pytest.raises(ValidationError):
        OP_ADAPTER.validate_python(raw)


@pytest.mark.parametrize("field", ["id", "from", "into"])
def test_whitespace_in_id_or_branch_name_rejected(field: str) -> None:
    """IdStr fields reject any whitespace, including a single space."""
    # --- arrange ----------------------
    raw = {"op": "pull_request", "from": "feat", "into": "main"}
    raw[field] = "has space"

    # --- act / assert -----------------
    with pytest.raises(ValidationError):
        OP_ADAPTER.validate_python(raw)
