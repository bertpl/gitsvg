"""Tests for the layout engine — `compute_layout(state) → Layout`."""

import re
from pathlib import Path

import pytest

from gitsvg._visual_constants import (
    BRANCH_SPACING,
    COLORS,
    COMMIT_SPACING,
    DEFAULT_BRANCH_COLORS,
    MARGIN_BRANCH_AXIS_LOWER,
    MARGIN_BRANCH_AXIS_UPPER,
    MARGIN_COMMIT_AXIS_LOWER,
    MARGIN_COMMIT_AXIS_UPPER,
)
from gitsvg.errors import ValidationReport
from gitsvg.imports import resolve_imports
from gitsvg.layout import Layout, compute_layout
from gitsvg.parse import parse_jsonl_file, parse_jsonl_text
from gitsvg.state import apply_ops


def _layout_from(text: str) -> Layout:
    """Parse JSONL → state → layout."""
    parsed, report = parse_jsonl_text(text, file="x.jsonl")
    state = apply_ops(parsed, report)
    return compute_layout(state)


# ==================================================================================================
#  Branch-axis assignment — declaration order
# ==================================================================================================
def test_first_branch_gets_branch_pos_zero() -> None:
    # --- act --------------------------
    layout = _layout_from('{"op": "branch", "name": "main"}\n')

    # --- assert -----------------------
    assert layout.branches[0].name == "main"
    assert layout.branches[0].branch_pos == 0


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
    by_name = {b.name: b for b in layout.branches}
    assert by_name["main"].branch_pos == 0
    assert by_name["feat"].branch_pos == 1
    assert by_name["docs"].branch_pos == 2


# ==================================================================================================
#  Commit-axis assignment — uniform `tip + 1 + gap` rule
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
    main = next(b for b in layout.branches if b.name == "main")
    assert main.end == 1


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
    feat = next(b for b in layout.branches if b.name == "feat")
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
    feat = next(b for b in layout.branches if b.name == "feat")
    assert feat.start == 2


def test_branch_from_commit_starts_one_above_named_commit() -> None:
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
    feat = next(b for b in layout.branches if b.name == "feat")
    assert feat.start == 1


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
    feat = next(b for b in layout.branches if b.name == "feat")
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
    assert layout.commits["c1"].commit_pos == 0
    assert layout.commits["c2"].commit_pos == 2
    assert layout.commits["c3"].commit_pos == 3


# ==================================================================================================
#  Merge commits land above both parents
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
    assert layout.commits["m2"].commit_pos == 3
    assert layout.commits["m2"].branch_pos == 0


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
    assert layout.commits["m2"].commit_pos == 4


# ==================================================================================================
#  Replaces (squash) — uniform rule + gap inheritance
# ==================================================================================================
def test_replaces_commit_inherits_position_via_inherited_gap() -> None:
    """When the squash inherits the earliest replaced commit's gap, it lands at
    that commit's original position."""
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
    # c2 was at position 0 + 1 + 2 = 3 originally; csquash inherits gap=2 and lands
    # at c1.pos + 1 + 2 = 3.
    assert layout.commits["csquash"].commit_pos == 3
    assert "c2" not in layout.commits
    assert "c3" not in layout.commits


def test_replaces_compact_when_no_gap_in_chain() -> None:
    """The common case: gap=0 throughout. Squash compacts."""
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
    assert layout.commits["csquash"].commit_pos == 1
    main = next(b for b in layout.branches if b.name == "main")
    assert main.end == 1


# ==================================================================================================
#  Resolved colours
# ==================================================================================================
def test_explicit_branch_color_used_verbatim() -> None:
    # --- arrange ----------------------
    layout = _layout_from('{"op": "branch", "name": "main", "color": "#abcdef"}\n')

    # --- assert -----------------------
    main = next(b for b in layout.branches if b.name == "main")
    assert main.color == "#abcdef"


def test_first_branch_defaults_to_main_color() -> None:
    # --- arrange ----------------------
    layout = _layout_from('{"op": "branch", "name": "main"}\n')

    # --- assert -----------------------
    main = next(b for b in layout.branches if b.name == "main")
    assert main.color == COLORS["main"]


def test_subsequent_branches_cycle_default_palette() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "branch", "name": "f1", "from_branch": "main"}\n'
        '{"op": "branch", "name": "f2", "from_branch": "main"}\n'
        '{"op": "branch", "name": "f3", "from_branch": "main"}\n'
        '{"op": "branch", "name": "f4", "from_branch": "main"}\n'
        '{"op": "branch", "name": "f5", "from_branch": "main"}\n'
    )

    # --- act --------------------------
    layout = _layout_from(text)
    by_name = {b.name: b for b in layout.branches}

    # --- assert -----------------------
    assert by_name["f1"].color == COLORS[DEFAULT_BRANCH_COLORS[0]]
    assert by_name["f2"].color == COLORS[DEFAULT_BRANCH_COLORS[1]]
    assert by_name["f3"].color == COLORS[DEFAULT_BRANCH_COLORS[2]]
    assert by_name["f4"].color == COLORS[DEFAULT_BRANCH_COLORS[3]]
    # f5 wraps back to position 0.
    assert by_name["f5"].color == COLORS[DEFAULT_BRANCH_COLORS[0]]


def test_commit_color_matches_its_branch_color() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main", "color": "#aabbcc"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
    )

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    assert layout.commits["c1"].color == "#aabbcc"


# ==================================================================================================
#  Resolved label_side
# ==================================================================================================
def test_label_side_defaults_to_right() -> None:
    # --- arrange ----------------------
    layout = _layout_from('{"op": "branch", "name": "main"}\n')

    # --- assert -----------------------
    main = next(b for b in layout.branches if b.name == "main")
    assert main.label_side == "right"


def test_label_side_explicit_override() -> None:
    # --- arrange ----------------------
    layout = _layout_from('{"op": "branch", "name": "main", "label_side": "left"}\n')

    # --- assert -----------------------
    main = next(b for b in layout.branches if b.name == "main")
    assert main.label_side == "left"


# ==================================================================================================
#  Arcs — branch-off and merge
# ==================================================================================================
def test_branch_off_arc_emitted_for_each_non_root_branch() -> None:
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
    branch_off_arcs = [a for a in layout.arcs if a.kind == "branch_off"]
    assert len(branch_off_arcs) == 1
    arc = branch_off_arcs[0]
    assert arc.from_branch_pos == 0  # main lane
    assert arc.from_commit_pos == 0  # m1
    assert arc.to_branch_pos == 1  # feat lane
    assert arc.to_commit_pos == 1  # feat.start
    assert arc.vertical_first is False


def test_branch_off_arc_color_is_target_branch_color() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main", "color": "#aabbcc"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main", "color": "#112233"}\n'
    )

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    arc = next(a for a in layout.arcs if a.kind == "branch_off")
    assert arc.color == "#112233"


def test_merge_arc_emitted_with_source_branch_color() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main", "color": "#aabbcc"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main", "color": "#112233"}\n'
        '{"op": "commit", "branch": "feat", "id": "f1", "msg": "x"}\n'
        '{"op": "merge", "from": "feat", "into": "main", "as": "m2"}\n'
    )

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    merge_arcs = [a for a in layout.arcs if a.kind == "merge"]
    assert len(merge_arcs) == 1
    arc = merge_arcs[0]
    assert arc.color == "#112233"  # source branch's color
    assert arc.vertical_first is True


# ==================================================================================================
#  Branch guides — one per occupied lane
# ==================================================================================================
def test_one_guide_per_unique_branch_pos() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
        '{"op": "branch", "name": "docs", "from_branch": "main"}\n'
    )

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    assert len(layout.guides) == 3
    assert sorted(g.branch_pos for g in layout.guides) == [0, 1, 2]


# ==================================================================================================
#  Canvas dimensions
# ==================================================================================================
def test_canvas_size_for_single_branch_three_commits() -> None:
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
    canvas = layout.canvas
    assert canvas.n_commits == 3
    assert canvas.width == MARGIN_BRANCH_AXIS_LOWER + 0 * BRANCH_SPACING + MARGIN_BRANCH_AXIS_UPPER
    assert canvas.height == MARGIN_COMMIT_AXIS_UPPER + (3 - 1) * COMMIT_SPACING + MARGIN_COMMIT_AXIS_LOWER


def test_canvas_widens_for_two_branches() -> None:
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
    assert layout.canvas.width == MARGIN_BRANCH_AXIS_LOWER + 1 * BRANCH_SPACING + MARGIN_BRANCH_AXIS_UPPER


def test_canvas_includes_empty_branch_start_in_height() -> None:
    """An empty fork branch with start > max(commit_pos) extends the canvas."""
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
    assert layout.canvas.n_commits == 3


# ==================================================================================================
#  Resolved hash flows through to the layout
# ==================================================================================================
def test_resolved_auto_hash_in_layout_commit() -> None:
    """A commit declared with `hash: "auto"` shows up in layout with the
    resolved 7-char hex string."""
    # --- arrange ----------------------
    text = '{"op": "branch", "name": "main"}\n{"op": "commit", "branch": "main", "id": "c1", "hash": "auto"}\n'

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    resolved = layout.commits["c1"].hash
    assert resolved is not None
    assert resolved != "auto"
    assert re.fullmatch(r"[0-9a-f]{7}", resolved) is not None


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
    state = apply_ops(expanded, report)
    assert report.is_clean(), f"{path} parse/import/apply errors: {report.errors}"

    # --- act --------------------------
    layout = compute_layout(state)

    # --- assert -----------------------
    for commit in layout.commits.values():
        assert commit.commit_pos >= 0
        assert commit.branch_pos >= 0
    for branch in layout.branches:
        assert branch.start >= 0
        assert branch.end >= branch.start
        assert branch.branch_pos >= 0
    assert layout.canvas.width > 0
    assert layout.canvas.height > 0


# Defensive — the corpus walker uses ValidationReport implicitly via the parser;
# the import keeps the path resolution in test discovery.
_ = ValidationReport
