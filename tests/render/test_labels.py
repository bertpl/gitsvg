"""Tests for commit labels and branch-name pills."""

from gitsvg.layout import compute_layout
from gitsvg.parse import parse_jsonl_text
from gitsvg.render import render
from gitsvg.state import apply_ops


def _render_from(text: str):
    parsed, report = parse_jsonl_text(text, file="x.jsonl")
    state, theme = apply_ops(parsed, report)
    layout = compute_layout(state)
    return render(layout, theme)


# ==================================================================================================
#  Branch-name pills
# ==================================================================================================
def test_branch_pill_emits_one_rect_and_one_text_per_branch() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "feat", "id": "f1", "msg": "x"}\n'
    )

    # --- act --------------------------
    svg_text = _render_from(text).as_svg()

    # --- assert -----------------------
    # 2 branches → 2 pills → 2 rectangles + 2 text elements (one per pill).
    # Plus commit-label texts (msg "x" on each commit).
    assert svg_text.count("<rect") == 2
    # Pills text + commit msg text:
    # 2 pills × 1 text + 2 commits × 1 line = 4 texts.
    assert svg_text.count("<text") == 4


def test_branch_pill_text_is_branch_name() -> None:
    # --- arrange ----------------------
    text = '{"op": "branch", "name": "feature/x"}\n'

    # --- act --------------------------
    svg_text = _render_from(text).as_svg()

    # --- assert -----------------------
    assert ">feature/x</text>" in svg_text


def test_branch_pill_uses_branch_color() -> None:
    # --- arrange ----------------------
    text = '{"op": "branch", "name": "main", "color": "#aabbcc"}\n'

    # --- act --------------------------
    svg_text = _render_from(text).as_svg()

    # --- assert -----------------------
    # The pill's fill matches the branch color.
    assert 'fill="#aabbcc"' in svg_text


# ==================================================================================================
#  Commit labels
# ==================================================================================================
def test_commit_with_msg_only_emits_one_text_line() -> None:
    # --- arrange ----------------------
    text = '{"op": "branch", "name": "main"}\n{"op": "commit", "branch": "main", "id": "c1", "msg": "initial"}\n'

    # --- act --------------------------
    svg_text = _render_from(text).as_svg()

    # --- assert -----------------------
    # 1 pill text + 1 commit msg text.
    assert svg_text.count("<text") == 2
    assert ">initial</text>" in svg_text


def test_commit_with_msg_and_hash_emits_two_text_lines() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "fix", "hash": "deadbef"}\n'
    )

    # --- act --------------------------
    svg_text = _render_from(text).as_svg()

    # --- assert -----------------------
    # 1 pill + 2 lines (msg + hash) = 3 text elements.
    assert svg_text.count("<text") == 3
    assert ">fix</text>" in svg_text
    assert ">deadbef</text>" in svg_text


def test_commit_with_multiline_msg_emits_one_text_per_line() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "line one\\nline two\\nline three"}\n'
    )

    # --- act --------------------------
    svg_text = _render_from(text).as_svg()

    # --- assert -----------------------
    # 1 pill + 3 msg lines = 4 text elements.
    assert svg_text.count("<text") == 4
    assert ">line one</text>" in svg_text
    assert ">line two</text>" in svg_text
    assert ">line three</text>" in svg_text


def test_commit_with_no_msg_no_hash_emits_no_label() -> None:
    """A `merge:` op produces a commit with neither msg nor hash by default,
    so the renderer should emit no commit-label text for it."""
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
    # 2 pills + 2 commit msgs ("x" on m1 and f1) + 0 for the merge commit (no msg, no hash) = 4.
    assert svg_text.count("<text") == 4


def test_label_side_before_uses_text_anchor_end() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main", "label_side": "before"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
    )

    # --- act --------------------------
    svg_text = _render_from(text).as_svg()

    # --- assert -----------------------
    # The commit label text should carry text_anchor="end".
    assert 'text-anchor="end"' in svg_text


def test_commit_label_anchor_per_side_dispatch() -> None:
    """The renderer picks the matching `commit_label_anchor_*` field per commit's side.

    Overriding only one side leaves the other at its per-orientation
    default — the renderer must dispatch on `commit.label_side` at draw
    time, not on a single global anchor.
    """
    # --- arrange ----------------------
    # main with label_side=before; feature with label_side=after. Override
    # only the `_before` side to a centered (0.5, 0.5) anchor; the `_after`
    # side should keep its BT default (0.0, 0.5).
    text = (
        '{"op": "theme", "commit_label_anchor_before": [0.5, 0.5]}\n'
        '{"op": "branch", "name": "main", "label_side": "before"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
        '{"op": "branch", "name": "feature", "from_branch": "main", "label_side": "after"}\n'
        '{"op": "commit", "branch": "feature", "id": "c2", "msg": "y"}\n'
    )

    # --- act --------------------------
    svg_text = _render_from(text).as_svg()

    # --- assert -----------------------
    # `before` override (u=0.5) → text-anchor=middle for the "x" label.
    # `after` default (u=0.0)   → text-anchor=start for the "y" label.
    assert 'text-anchor="middle"' in svg_text
    assert 'text-anchor="start"' in svg_text


def test_highlight_renders_bold_msg_label() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "winner", "highlight": true}\n'
    )

    # --- act --------------------------
    svg_text = _render_from(text).as_svg()

    # --- assert -----------------------
    # The msg line for the highlighted commit gets font-weight 700.
    assert 'font-weight="700"' in svg_text
    # The pill text uses 500, so 500 should also appear.
    assert 'font-weight="500"' in svg_text


def test_highlight_enlarges_commit_dot() -> None:
    """A highlighted commit's dot uses HIGHLIGHT_RADIUS instead of COMMIT_RADIUS."""
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "winner", "highlight": true}\n'
        '{"op": "commit", "branch": "main", "id": "c2", "msg": "normal"}\n'
    )

    # --- act --------------------------
    svg_text = _render_from(text).as_svg()

    # --- assert -----------------------
    # Two circles: one with r=7 (highlight) and one with r=5 (normal).
    assert 'r="7"' in svg_text
    assert 'r="5"' in svg_text


# ==================================================================================================
#  Hash secondary line uses HASH_FONT_SIZE
# ==================================================================================================
def test_hash_secondary_line_uses_smaller_font_size() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "fix", "hash": "deadbef"}\n'
    )

    # --- act --------------------------
    svg_text = _render_from(text).as_svg()

    # --- assert -----------------------
    # Both LABEL_FONT_SIZE (11) and HASH_FONT_SIZE (9) appear: 11 for msg + pill, 9 for hash.
    # Floats render with a trailing `.0` since the font-size fields are typed `float`.
    assert 'font-size="11.0"' in svg_text
    assert 'font-size="9.0"' in svg_text
