"""Tests for the layout engine — axis-position assignment."""

from pathlib import Path

import pytest

from gitsvg.imports import resolve_imports
from gitsvg.layout import compute_layout
from gitsvg.parse import parse_jsonl_file, parse_jsonl_text


# ==================================================================================================
#  Helpers
# ==================================================================================================
def _layout_from(text: str):
    """Parse JSONL, lay out, return the resulting `Layout`."""
    parsed, _ = parse_jsonl_text(text, file="x.jsonl")
    return compute_layout(parsed)


# ==================================================================================================
#  Branch-axis assignment — declaration order
# ==================================================================================================
def test_first_branch_gets_branch_pos_zero() -> None:
    # --- act --------------------------
    layout = _layout_from('{"op": "branch", "name": "main"}\n')

    # --- assert -----------------------
    assert layout.branches["main"].branch_pos == 0


def test_branch_pos_increments_in_declaration_order() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
        '{"op": "branch", "name": "docs", "from_branch": "main"}\n'
    )

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    assert layout.branches["main"].branch_pos == 0
    assert layout.branches["feat"].branch_pos == 1
    assert layout.branches["docs"].branch_pos == 2


# ==================================================================================================
#  Commit-axis assignment — single branch
# ==================================================================================================
def test_first_commit_on_root_branch_lands_at_zero() -> None:
    # --- arrange ----------------------
    text = '{"op": "branch", "name": "main"}\n{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    assert layout.commits["c1"].commit_pos == 0


def test_subsequent_commits_advance_by_one() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "c2", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "c3", "msg": "x"}\n'
    )

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    assert [layout.commits[c].commit_pos for c in ["c1", "c2", "c3"]] == [0, 1, 2]


def test_branch_end_is_latest_commit_position() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "c2", "msg": "x"}\n'
    )

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    assert layout.branches["main"].end == 1


def test_empty_branch_end_equals_start() -> None:
    """A branch declared but never committed-to has end == start."""
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
    )

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    feat = layout.branches["feat"]
    assert feat.end == feat.start


# ==================================================================================================
#  Branch start — parent_commit.commit_pos + 1
# ==================================================================================================
def test_branch_from_branch_starts_one_above_parent_tip() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "m2", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
    )

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    # main.tip = m2 at commit_pos 1; feat.start = 2.
    assert layout.branches["feat"].start == 2


def test_branch_from_commit_starts_one_above_named_commit() -> None:
    """`from_commit` lets the author root a branch on a non-tip commit."""
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "m2", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "m3", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_commit": "m1"}\n'
    )

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    # m1 is at commit_pos 0; feat.start = 1, even though main has progressed past m1.
    assert layout.branches["feat"].start == 1


def test_first_commit_on_fork_branch_lands_at_start() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "feat", "id": "f1", "msg": "x"}\n'
    )

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    feat = layout.branches["feat"]
    assert feat.start == 1
    assert layout.commits["f1"].commit_pos == 1


# ==================================================================================================
#  Gap propagation
# ==================================================================================================
def test_gap_on_first_commit_shifts_landing_position() -> None:
    # --- arrange ----------------------
    text = '{"op": "branch", "name": "main"}\n{"op": "commit", "branch": "main", "id": "c1", "msg": "x", "gap": 2}\n'

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    # Branch starts at 0; first commit with gap=2 lands at 0 + 2 = 2.
    assert layout.commits["c1"].commit_pos == 2


def test_gap_on_subsequent_commit_shifts_only_that_commit_and_beyond() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "c2", "msg": "x", "gap": 1}\n'
        '{"op": "commit", "branch": "main", "id": "c3", "msg": "x"}\n'
    )

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    # c1 at 0. c2 at tip(0) + 1 + gap(1) = 2. c3 at tip(2) + 1 = 3.
    assert layout.commits["c1"].commit_pos == 0
    assert layout.commits["c2"].commit_pos == 2
    assert layout.commits["c3"].commit_pos == 3


# ==================================================================================================
#  Merge
# ==================================================================================================
def test_merge_commit_lands_above_both_tips() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "feat", "id": "f1", "msg": "x"}\n'
        '{"op": "commit", "branch": "feat", "id": "f2", "msg": "x"}\n'
        '{"op": "merge", "from": "feat", "into": "main", "as": "m2"}\n'
    )

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    # main.tip = m1 at 0; feat.tip = f2 at 2. Merge at max(0, 2) + 1 = 3.
    assert layout.commits["m2"].commit_pos == 3
    assert layout.commits["m2"].branch_pos == 0  # merge sits on `into`'s lane


def test_merge_with_gap_shifts_above_natural_anchor() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "feat", "id": "f1", "msg": "x"}\n'
        '{"op": "merge", "from": "feat", "into": "main", "as": "m2", "gap": 2}\n'
    )

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    # max(m1=0, f1=1) + 1 + gap(2) = 4.
    assert layout.commits["m2"].commit_pos == 4


# ==================================================================================================
#  Replaces (squash)
# ==================================================================================================
def test_replaces_commit_takes_first_replaced_position() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "c2", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "c3", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "csquash", "msg": "squash", "replaces": ["c2", "c3"]}\n'
    )

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    # csquash takes c2's position = 1. c2 and c3 are removed.
    assert layout.commits["csquash"].commit_pos == 1
    assert "c2" not in layout.commits
    assert "c3" not in layout.commits
    # main.end rolls back to csquash's position.
    assert layout.branches["main"].end == 1


def test_replaces_preserves_upstream_gap() -> None:
    """When intermediate commits had non-zero gaps, the squash inherits the
    first replaced commit's position, preserving the gap."""
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "c2", "msg": "x", "gap": 2}\n'
        '{"op": "commit", "branch": "main", "id": "c3", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "csquash", "msg": "squash", "replaces": ["c2", "c3"]}\n'
    )

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    # c1=0, c2=3 (gap=2 → 0+1+2), c3=4. csquash takes c2's position = 3.
    assert layout.commits["csquash"].commit_pos == 3


def test_commit_after_replaces_continues_from_squash_tip() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "c2", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "c3", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "csquash", "msg": "squash", "replaces": ["c2", "c3"]}\n'
        '{"op": "commit", "branch": "main", "id": "c4", "msg": "x"}\n'
    )

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    # csquash at 1; c4 lands at csquash + 1 = 2.
    assert layout.commits["c4"].commit_pos == 2


# ==================================================================================================
#  Auto-id parity with state engine
# ==================================================================================================
def test_auto_id_uses_underscore_c_n_namespace() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "msg": "x"}\n'
    )

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    # User-supplied `c1` does not collide with `_c<N>` auto-id namespace —
    # same convention as the state engine.
    assert "c1" in layout.commits
    assert "_c1" in layout.commits
    assert "_c2" in layout.commits


def test_auto_id_skips_already_used_underscore_c_n_ids() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "_c2", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "msg": "x"}\n'
    )

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    assert {"_c2", "_c1", "_c3"}.issubset(layout.commits.keys())


# ==================================================================================================
#  Positions are non-negative integers
# ==================================================================================================
def test_all_positions_are_non_negative_ints() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "feat", "id": "f1", "msg": "x"}\n'
        '{"op": "merge", "from": "feat", "into": "main", "as": "m2"}\n'
    )

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    for commit in layout.commits.values():
        assert isinstance(commit.commit_pos, int) and commit.commit_pos >= 0
        assert isinstance(commit.branch_pos, int) and commit.branch_pos >= 0
    for branch in layout.branches.values():
        assert isinstance(branch.start, int) and branch.start >= 0
        assert isinstance(branch.end, int) and branch.end >= branch.start
        assert isinstance(branch.branch_pos, int) and branch.branch_pos >= 0


# ==================================================================================================
#  Local corpus walk — every test_examples file lays out cleanly
# ==================================================================================================
_CORPUS_DIR = Path(__file__).resolve().parent.parent.parent / "local" / "test_examples"


def _corpus_files() -> list[Path]:
    """Return every `.gitsvg.jsonl` file under `local/test_examples/`, or [] when absent."""
    if not _CORPUS_DIR.exists():
        return []
    return sorted(_CORPUS_DIR.rglob("*.gitsvg.jsonl"))


@pytest.mark.skipif(not _corpus_files(), reason="local/test_examples corpus is gitignored and not present")
@pytest.mark.parametrize("path", _corpus_files(), ids=lambda p: p.relative_to(_CORPUS_DIR).as_posix())
def test_layout_completes_for_every_corpus_file(path: Path) -> None:
    # --- arrange ----------------------
    parsed, report = parse_jsonl_file(path)
    expanded = resolve_imports(parsed, file=path, report=report)
    assert report.is_clean(), f"{path} parse/import errors: {report.errors}"

    # --- act --------------------------
    layout = compute_layout(expanded)

    # --- assert -----------------------
    for commit in layout.commits.values():
        assert commit.commit_pos >= 0, f"{path}: {commit.id} has negative commit_pos"
        assert commit.branch_pos >= 0, f"{path}: {commit.id} has negative branch_pos"
    for branch in layout.branches.values():
        assert branch.start >= 0, f"{path}: {branch.name}.start negative"
        assert branch.end >= branch.start, f"{path}: {branch.name}.end < start"
        assert branch.branch_pos >= 0, f"{path}: {branch.name}.branch_pos negative"
