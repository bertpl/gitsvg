"""Per-op happy-path and field-schema tests for the seven v0.0.x operations."""

import pytest
from pydantic import ValidationError

from gitsvg.file_format.ops import (
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
    raw = {
        "op": "canvas",
        "n_commits": 10,
        "n_branches": 3,
        "commit_spacing": 12.5,
        "branch_spacing": 40,
        "margin_commit_axis_lower": 30,
        "margin_commit_axis_upper": 30,
        "margin_branch_axis_lower": 80,
        "margin_branch_axis_upper": 100,
    }

    # --- act --------------------------
    op = CanvasOp.model_validate(raw)

    # --- assert -----------------------
    assert op.n_commits == 10
    assert op.n_branches == 3
    assert op.commit_spacing == 12.5
    assert op.branch_spacing == 40
    assert op.margin_commit_axis_lower == 30
    assert op.margin_commit_axis_upper == 30
    assert op.margin_branch_axis_lower == 80
    assert op.margin_branch_axis_upper == 100


def test_branch_with_from_branch_and_visual_overrides() -> None:
    # --- arrange ----------------------
    raw = {
        "op": "branch",
        "name": "feat/x",
        "from_branch": "main",
        "color": "#7b8fb2",
        "label_side": "left",
    }

    # --- act --------------------------
    op = BranchOp.model_validate(raw)

    # --- assert -----------------------
    assert op.from_branch == "main"
    assert op.color == "#7b8fb2"
    assert op.label_side == "left"


def test_branch_label_side_rejects_unknown_value() -> None:
    # --- arrange ----------------------
    raw = {"op": "branch", "name": "main", "label_side": "top"}

    # --- act / assert -----------------
    with pytest.raises(ValidationError):
        BranchOp.model_validate(raw)


@pytest.mark.parametrize("branch_pos", [0, 1, 7, 42])
def test_branch_pos_accepts_non_negative_int(branch_pos: int) -> None:
    # --- arrange ----------------------
    raw = {"op": "branch", "name": "feat/x", "from_branch": "main", "branch_pos": branch_pos}

    # --- act --------------------------
    op = BranchOp.model_validate(raw)

    # --- assert -----------------------
    assert op.branch_pos == branch_pos


def test_branch_pos_omitted_defaults_to_none() -> None:
    # --- arrange ----------------------
    raw = {"op": "branch", "name": "main"}

    # --- act --------------------------
    op = BranchOp.model_validate(raw)

    # --- assert -----------------------
    assert op.branch_pos is None


@pytest.mark.parametrize("branch_pos", [-1, -42])
def test_branch_pos_rejects_negative(branch_pos: int) -> None:
    # --- arrange ----------------------
    raw = {"op": "branch", "name": "feat/x", "from_branch": "main", "branch_pos": branch_pos}

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
        "theme": {"op": "theme"},
        "branch": {"op": "branch", "name": "main"},
        "commit": {"op": "commit", "branch": "main", "msg": "x"},
        "merge": {"op": "merge", "from": "a", "into": "b"},
        "pull_request": {"op": "pull_request", "from": "a", "into": "b"},
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
    assert actual_order == [
        "import",
        "canvas",
        "theme",
        "branch",
        "commit",
        "merge",
        "pull_request",
        "remove",
        "highlight",
    ]


# ==================================================================================================
#  Field-level schema constraints — string contents
# ==================================================================================================
@pytest.mark.parametrize(
    "raw",
    [
        {"op": "import", "path": ""},
        {"op": "branch", "name": ""},
        {"op": "branch", "name": "has space"},
        {"op": "branch", "name": "main", "from_branch": "with space"},
        {"op": "commit", "branch": "", "msg": "x"},
        {"op": "commit", "branch": "has space", "msg": "x"},
        {"op": "commit", "branch": "main", "id": "has space", "msg": "x"},
        {"op": "commit", "branch": "main", "msg": "x", "hash": "has space"},
        {"op": "commit", "branch": "main", "msg": ""},
        {"op": "merge", "from": "", "into": "main"},
        {"op": "merge", "from": "feat", "into": "has space"},
        {"op": "merge", "from": "feat", "into": "main", "as": "has space"},
        {"op": "merge", "from": "feat", "into": "main", "msg": ""},
        {"op": "remove", "commits": ["has space"]},
        {"op": "remove", "branches": [""]},
        {"op": "highlight", "commit": ""},
        {"op": "highlight", "commit": "has space"},
    ],
)
def test_string_constraints_reject_empty_or_whitespace(raw: dict) -> None:
    # --- act / assert -----------------
    with pytest.raises(ValidationError):
        OP_ADAPTER.validate_python(raw)


@pytest.mark.parametrize(
    "color",
    ["#abc", "#ABC", "#7b8fb2", "#7B8FB2"],
)
def test_branch_color_accepts_valid_hex_forms(color: str) -> None:
    # --- arrange ----------------------
    raw = {"op": "branch", "name": "main", "color": color}

    # --- act --------------------------
    op = BranchOp.model_validate(raw)

    # --- assert -----------------------
    assert op.color == color


@pytest.mark.parametrize(
    "color",
    ["7b8fb2", "#xyz", "#1234", "#1234567", "blue", ""],
)
def test_branch_color_rejects_invalid_hex_forms(color: str) -> None:
    # --- arrange ----------------------
    raw = {"op": "branch", "name": "main", "color": color}

    # --- act / assert -----------------
    with pytest.raises(ValidationError):
        BranchOp.model_validate(raw)


# ==================================================================================================
#  Field-level schema constraints — numeric ranges
# ==================================================================================================
@pytest.mark.parametrize(
    "raw",
    [
        {"op": "canvas", "n_commits": -1},
        {"op": "canvas", "n_branches": -1},
        {"op": "canvas", "commit_spacing": -0.1},
        {"op": "canvas", "branch_spacing": -1.0},
        {"op": "canvas", "margin_commit_axis_lower": -1},
        {"op": "canvas", "margin_commit_axis_upper": -1},
        {"op": "canvas", "margin_branch_axis_lower": -1},
        {"op": "canvas", "margin_branch_axis_upper": -1},
        {"op": "commit", "branch": "main", "msg": "x", "gap": -1},
        {"op": "merge", "from": "feat", "into": "main", "gap": -1},
    ],
)
def test_numeric_fields_reject_negative_values(raw: dict) -> None:
    # --- act / assert -----------------
    with pytest.raises(ValidationError):
        OP_ADAPTER.validate_python(raw)


@pytest.mark.parametrize(
    "raw",
    [
        {"op": "canvas", "n_commits": 0, "commit_spacing": 0, "branch_spacing": 0},
        {"op": "canvas", "margin_commit_axis_lower": 0, "margin_branch_axis_upper": 0},
        {"op": "commit", "branch": "main", "msg": "x", "gap": 0},
        {"op": "merge", "from": "feat", "into": "main", "gap": 0},
    ],
)
def test_numeric_fields_accept_zero(raw: dict) -> None:
    # --- act --------------------------
    op = OP_ADAPTER.validate_python(raw)

    # --- assert -----------------------
    assert op.op == raw["op"]


# ==================================================================================================
#  Field-level schema constraints — list non-emptiness and item schema
# ==================================================================================================
@pytest.mark.parametrize(
    "raw",
    [
        {"op": "commit", "branch": "main", "msg": "x", "parents": []},
        {"op": "commit", "branch": "main", "msg": "x", "replaces": []},
        {"op": "remove", "commits": []},
        {"op": "remove", "branches": []},
    ],
)
def test_list_fields_reject_empty_lists(raw: dict) -> None:
    # --- act / assert -----------------
    with pytest.raises(ValidationError):
        OP_ADAPTER.validate_python(raw)


@pytest.mark.parametrize(
    "raw",
    [
        {"op": "commit", "branch": "main", "msg": "x", "parents": ["has space"]},
        {"op": "commit", "branch": "main", "msg": "x", "replaces": [""]},
        {"op": "remove", "commits": ["", "ok"]},
    ],
)
def test_list_fields_reject_empty_or_whitespace_items(raw: dict) -> None:
    # --- act / assert -----------------
    with pytest.raises(ValidationError):
        OP_ADAPTER.validate_python(raw)


# ==================================================================================================
#  Inter-field schema constraints (model_validator)
# ==================================================================================================
def test_branch_rejects_both_from_branch_and_from_commit() -> None:
    # --- arrange ----------------------
    raw = {"op": "branch", "name": "feat/x", "from_branch": "main", "from_commit": "c1"}

    # --- act / assert -----------------
    with pytest.raises(ValidationError):
        BranchOp.model_validate(raw)


def test_commit_rejects_neither_msg_nor_hash() -> None:
    # --- arrange ----------------------
    raw = {"op": "commit", "branch": "main"}

    # --- act / assert -----------------
    with pytest.raises(ValidationError):
        CommitOp.model_validate(raw)


def test_commit_accepts_hash_only_without_msg() -> None:
    # --- arrange ----------------------
    raw = {"op": "commit", "branch": "main", "hash": "auto"}

    # --- act --------------------------
    op = CommitOp.model_validate(raw)

    # --- assert -----------------------
    assert op.msg is None
    assert op.hash == "auto"


def test_remove_rejects_neither_commits_nor_branches() -> None:
    # --- arrange ----------------------
    raw = {"op": "remove"}

    # --- act / assert -----------------
    with pytest.raises(ValidationError):
        RemoveOp.model_validate(raw)


def test_remove_rejects_both_commits_and_branches() -> None:
    # --- arrange ----------------------
    raw = {"op": "remove", "commits": ["c1"], "branches": ["feat/x"]}

    # --- act / assert -----------------
    with pytest.raises(ValidationError):
        RemoveOp.model_validate(raw)


def test_commit_gap_round_trip() -> None:
    # --- arrange ----------------------
    raw = {"op": "commit", "branch": "main", "msg": "x", "gap": 2}

    # --- act --------------------------
    op = CommitOp.model_validate(raw)

    # --- assert -----------------------
    assert op.gap == 2


def test_merge_gap_round_trip() -> None:
    # --- arrange ----------------------
    raw = {"op": "merge", "from": "feat", "into": "main", "gap": 1}

    # --- act --------------------------
    op = MergeOp.model_validate(raw)

    # --- assert -----------------------
    assert op.gap == 1


def test_commit_accepts_gap_with_replaces() -> None:
    """`gap` and `replaces:` may both be set on the same commit op.

    The state engine resolves the squash commit's effective `gap`:
    `op.gap` overrides; otherwise it inherits the earliest replaced
    commit's gap.
    """
    # --- arrange ----------------------
    raw = {
        "op": "commit",
        "branch": "main",
        "id": "c5",
        "msg": "squash",
        "replaces": ["c2", "c3"],
        "gap": 1,
    }

    # --- act --------------------------
    op = CommitOp.model_validate(raw)

    # --- assert -----------------------
    assert op.gap == 1
    assert op.replaces == ["c2", "c3"]
