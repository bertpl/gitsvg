"""Tests for branch-off and merge arcs in the rendered SVG."""

from gitsvg.layout import compute_layout
from gitsvg.parse import parse_jsonl_text
from gitsvg.render import render
from gitsvg.render._theme import build_theme
from gitsvg.state import apply_ops


def _render_from(text: str):
    parsed, report = parse_jsonl_text(text, file="x.jsonl")
    state = apply_ops(parsed, report)
    theme = build_theme(state)
    layout = compute_layout(state)
    return render(layout, theme)


# ==================================================================================================
#  Branch-off arcs
# ==================================================================================================
def test_branch_off_emits_one_extra_path_per_non_root_branch() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "m2", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "feat", "id": "f1", "msg": "x"}\n'
        '{"op": "commit", "branch": "feat", "id": "f2", "msg": "x"}\n'
    )

    # --- act --------------------------
    svg_text = _render_from(text).as_svg()

    # --- assert -----------------------
    # 2 guides + 1 branch-off arc + 2 branch lines = 5 paths.
    assert svg_text.count("<path") == 5


def test_branch_off_arc_color_matches_target_branch() -> None:
    """The branch-off arc takes the *new* (target) branch's colour, matching
    the seed convention."""
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main", "color": "#aabbcc"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main", "color": "#112233"}\n'
        '{"op": "commit", "branch": "feat", "id": "f1", "msg": "x"}\n'
    )

    # --- act --------------------------
    svg_text = _render_from(text).as_svg()

    # --- assert -----------------------
    # The feat branch's colour appears at least 3× (line, dot, branch-off arc).
    assert svg_text.count("#112233") >= 3


def test_branch_off_from_explicit_commit_uses_that_commits_position() -> None:
    """`from_commit:` lets the author root a branch on a non-tip commit; the
    branch-off arc should originate at that commit, not at the parent's tip."""
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "m2", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_commit": "m1"}\n'
    )

    # --- act --------------------------
    svg_text = _render_from(text).as_svg()

    # --- assert -----------------------
    # The arc should originate at m1's y (commit_pos=0 → bottom of canvas)
    # and target feat.start (commit_pos=1). `feat` is empty so its line is
    # suppressed: 2 guides + 1 arc + 1 line (main only) = 4 paths.
    assert svg_text.count("<path") == 4


# ==================================================================================================
#  Merge arcs
# ==================================================================================================
def test_merge_emits_an_extra_path_for_the_merge_arc() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "feat", "id": "f1", "msg": "x"}\n'
        '{"op": "merge", "from": "feat", "into": "main", "as": "m2"}\n'
    )

    # --- act --------------------------
    svg_text = _render_from(text).as_svg()

    # --- assert -----------------------
    # main has 2 commits (m1 + merge m2) so its line is drawn; feat has
    # just f1 so its line is suppressed. 2 guides + 1 branch-off arc +
    # 1 merge arc + 1 line (main) = 5 paths.
    assert svg_text.count("<path") == 5


def test_merge_arc_color_matches_source_branch() -> None:
    """The merge arc takes the *source* (from) branch's colour, matching the
    seed convention — opposite of branch-off (which uses target)."""
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main", "color": "#aabbcc"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main", "color": "#112233"}\n'
        '{"op": "commit", "branch": "feat", "id": "f1", "msg": "x"}\n'
        '{"op": "merge", "from": "feat", "into": "main", "as": "m2"}\n'
    )

    # --- act --------------------------
    svg_text = _render_from(text).as_svg()

    # --- assert -----------------------
    # The feat branch's colour appears on its line, dot, branch-off arc, AND
    # the merge arc — 4 occurrences minimum.
    assert svg_text.count("#112233") >= 4


# ==================================================================================================
#  Branch guides
# ==================================================================================================
def test_branch_guide_count_equals_unique_lane_count() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "feat", "id": "f1", "msg": "x"}\n'
    )

    # --- act --------------------------
    svg_text = _render_from(text).as_svg()

    # --- assert -----------------------
    # 2 lanes → 2 dashed guide lines. drawsvg renders Line as a `<path>`,
    # but guides also carry the `stroke-dasharray` attribute, which is
    # unique to them.
    assert svg_text.count("stroke-dasharray") == 2


def test_branch_guide_is_dashed_with_expected_pattern() -> None:
    # --- arrange ----------------------
    text = '{"op": "branch", "name": "main"}\n'

    # --- act --------------------------
    svg_text = _render_from(text).as_svg()

    # --- assert -----------------------
    assert 'stroke-dasharray="4,4"' in svg_text


# ==================================================================================================
#  Z-order: guides first, dots last
# ==================================================================================================
def test_z_order_guides_precede_lines_precede_dots() -> None:
    # --- arrange ----------------------
    # Two commits so the branch line is drawn (one-commit branches now
    # suppress their line as a degenerate zero-length path).
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "c2", "msg": "x"}\n'
    )

    # --- act --------------------------
    svg_text = _render_from(text).as_svg()

    # --- assert -----------------------
    # Guide (dashed line) → branch line (solid path) → commit dot (circle).
    guide_index = svg_text.index("stroke-dasharray")
    line_index = svg_text.index("stroke-linecap")  # solid branch line
    dot_index = svg_text.index("<circle")
    assert guide_index < line_index < dot_index
