"""Per-op happy-path and field-shape tests for the seven v0.0.x operations."""

import pytest
from pydantic import ValidationError

from gitsvg._file_format.ops import (
    OP_ADAPTER,
    OP_BY_NAME,
    OP_NAMES,
    BranchOp,
    CanvasOp,
    CommitOp,
    HighlightOp,
    ImportOp,
    MergeOp,
    RemoveOp,
)


# ==================================================================================================
#  Happy-path: minimal valid input per op
# ==================================================================================================
@pytest.mark.parametrize(
    "raw, expected_cls",
    [
        ({"op": "import", "path": "./other.gitsvg.jsonl"}, ImportOp),
        ({"op": "canvas"}, CanvasOp),
        ({"op": "branch", "name": "main"}, BranchOp),
        ({"op": "commit", "branch": "main", "msg": "initial"}, CommitOp),
        ({"op": "merge", "from": "feat", "into": "main"}, MergeOp),
        ({"op": "remove", "commits": ["c1"]}, RemoveOp),
        ({"op": "highlight", "commit": "c1"}, HighlightOp),
    ],
)
def test_minimal_valid_input_dispatches_to_correct_op(raw: dict, expected_cls: type) -> None:
    # --- act --------------------------
    op = OP_ADAPTER.validate_python(raw)

    # --- assert -----------------------
    assert isinstance(op, expected_cls)
    assert op.op == raw["op"]


# ==================================================================================================
#  Per-op specifics
# ==================================================================================================
def test_import_path_round_trip() -> None:
    # --- arrange ----------------------
    raw = {"op": "import", "path": "./prev.gitsvg.jsonl"}

    # --- act --------------------------
    op = ImportOp.model_validate(raw)

    # --- assert -----------------------
    assert op.path == "./prev.gitsvg.jsonl"


def test_canvas_all_optional_fields() -> None:
    # --- arrange ----------------------
    raw = {"op": "canvas", "n_commits": 10, "n_branches": 3, "commit_spacing": 12.5, "branch_spacing": 40}

    # --- act --------------------------
    op = CanvasOp.model_validate(raw)

    # --- assert -----------------------
    assert op.n_commits == 10
    assert op.n_branches == 3
    assert op.commit_spacing == 12.5
    assert op.branch_spacing == 40


def test_branch_with_from_branch_and_visual_overrides() -> None:
    # --- arrange ----------------------
    raw = {
        "op": "branch",
        "name": "feat/x",
        "from_branch": "main",
        "color": "#7b8fb2",
        "label_side": "left",
        "branch_pos": 2,
    }

    # --- act --------------------------
    op = BranchOp.model_validate(raw)

    # --- assert -----------------------
    assert op.from_branch == "main"
    assert op.color == "#7b8fb2"
    assert op.label_side == "left"
    assert op.branch_pos == 2


def test_branch_label_side_rejects_unknown_value() -> None:
    # --- arrange ----------------------
    raw = {"op": "branch", "name": "main", "label_side": "top"}

    # --- act / assert -----------------
    with pytest.raises(ValidationError):
        BranchOp.model_validate(raw)


def test_commit_hash_auto_sentinel_accepted() -> None:
    # --- arrange ----------------------
    raw = {"op": "commit", "branch": "main", "msg": "wip", "hash": "auto"}

    # --- act --------------------------
    op = CommitOp.model_validate(raw)

    # --- assert -----------------------
    assert op.hash == "auto"


def test_commit_with_replaces_and_parents() -> None:
    # --- arrange ----------------------
    raw = {
        "op": "commit",
        "branch": "main",
        "id": "c5",
        "msg": "squash A B C",
        "replaces": ["c2", "c3", "c4"],
        "parents": ["c1"],
    }

    # --- act --------------------------
    op = CommitOp.model_validate(raw)

    # --- assert -----------------------
    assert op.replaces == ["c2", "c3", "c4"]
    assert op.parents == ["c1"]


def test_merge_uses_from_and_as_aliases() -> None:
    # --- arrange ----------------------
    raw = {"op": "merge", "from": "feat/x", "into": "main", "as": "m1", "msg": "merge feat/x"}

    # --- act --------------------------
    op = MergeOp.model_validate(raw)

    # --- assert -----------------------
    assert op.from_ == "feat/x"
    assert op.as_ == "m1"


def test_merge_python_reserved_field_names_are_not_accepted_directly() -> None:
    # --- arrange ----------------------
    raw = {"op": "merge", "from_": "feat/x", "into": "main"}

    # --- act / assert -----------------
    with pytest.raises(ValidationError):
        MergeOp.model_validate(raw)


def test_remove_with_branches_list() -> None:
    # --- arrange ----------------------
    raw = {"op": "remove", "branches": ["feat/x"]}

    # --- act --------------------------
    op = RemoveOp.model_validate(raw)

    # --- assert -----------------------
    assert op.branches == ["feat/x"]
    assert op.commits is None


def test_highlight_targets_a_commit_id() -> None:
    # --- arrange ----------------------
    raw = {"op": "highlight", "commit": "c3"}

    # --- act --------------------------
    op = HighlightOp.model_validate(raw)

    # --- assert -----------------------
    assert op.commit == "c3"


# ==================================================================================================
#  Cross-cutting: extra="forbid" and discriminator behaviour
# ==================================================================================================
@pytest.mark.parametrize("op_name", OP_NAMES)
def test_unknown_field_is_rejected_for_every_op(op_name: str) -> None:
    # --- arrange ----------------------
    minimal_inputs = {
        "import": {"op": "import", "path": "./x.jsonl"},
        "canvas": {"op": "canvas"},
        "branch": {"op": "branch", "name": "main"},
        "commit": {"op": "commit", "branch": "main", "msg": "x"},
        "merge": {"op": "merge", "from": "a", "into": "b"},
        "remove": {"op": "remove", "commits": ["c1"]},
        "highlight": {"op": "highlight", "commit": "c1"},
    }
    raw = {**minimal_inputs[op_name], "definitely_unknown_field": 42}

    # --- act / assert -----------------
    with pytest.raises(ValidationError):
        OP_ADAPTER.validate_python(raw)


def test_unknown_op_name_is_rejected() -> None:
    # --- arrange ----------------------
    raw = {"op": "fast_forward", "from": "a", "into": "b"}

    # --- act / assert -----------------
    with pytest.raises(ValidationError):
        OP_ADAPTER.validate_python(raw)


def test_missing_op_field_is_rejected() -> None:
    # --- arrange ----------------------
    raw = {"path": "./x.jsonl"}

    # --- act / assert -----------------
    with pytest.raises(ValidationError):
        OP_ADAPTER.validate_python(raw)


def test_op_by_name_registry_matches_canonical_order() -> None:
    # --- act --------------------------
    actual_order = list(OP_BY_NAME.keys())

    # --- assert -----------------------
    assert actual_order == OP_NAMES
    assert actual_order == ["import", "canvas", "branch", "commit", "merge", "remove", "highlight"]
