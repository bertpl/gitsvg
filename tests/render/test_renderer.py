"""End-to-end tests for the renderer — produces valid SVG with expected primitives."""

from gitsvg.layout import compute_layout
from gitsvg.parse import parse_jsonl_text
from gitsvg.render import render
from gitsvg.state import apply_ops


def _render_from(text: str):
    parsed, report = parse_jsonl_text(text, file="x.jsonl")
    state = apply_ops(parsed, report)
    layout = compute_layout(state)
    return render(layout)


def test_render_produces_valid_svg_with_correct_root_dimensions() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "c2", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "c3", "msg": "x"}\n'
    )

    # --- act --------------------------
    drawing = _render_from(text)
    svg_text = drawing.as_svg()

    # --- assert -----------------------
    assert svg_text.startswith("<?xml") or svg_text.startswith("<svg")
    # Single branch with 3 commits: width 200 (margins 100 + 100), height
    # auto-fits to include pill room below the lowest dot.
    assert 'width="200"' in svg_text
    assert 'height="' in svg_text  # auto-fit value depends on label widths


def test_render_emits_expected_path_and_circle_counts() -> None:
    """drawsvg renders both `Line` and `Path` as `<path>`. With two branches and
    a fork, the SVG carries: 2 guides + 1 branch-off arc + 2 branch lines = 5
    paths, plus one circle per commit."""
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "feat", "id": "f1", "msg": "x"}\n'
        '{"op": "commit", "branch": "feat", "id": "f2", "msg": "x"}\n'
    )

    # --- act --------------------------
    svg_text = _render_from(text).as_svg()

    # --- assert -----------------------
    assert svg_text.count("<path") == 5  # 2 guides + 1 arc + 2 lines
    assert svg_text.count("<circle") == 3  # c1 + f1 + f2


def test_empty_branch_still_emits_a_path_element() -> None:
    """A declared branch with no commits gets a zero-length path — a degenerate
    placeholder that becomes visible once labels are drawn at its start."""
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
    )

    # --- act --------------------------
    svg_text = _render_from(text).as_svg()

    # --- assert -----------------------
    # 2 guides + 1 branch-off arc (degenerate, same row) + 2 branch lines.
    assert svg_text.count("<path") == 5


def test_render_preserves_branch_colour_in_dot_fill() -> None:
    """Each commit's dot is filled with its branch's resolved colour."""
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main", "color": "#aabbcc"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
    )

    # --- act --------------------------
    svg_text = _render_from(text).as_svg()

    # --- assert -----------------------
    # The override colour appears on the branch line and the commit dot.
    assert "#aabbcc" in svg_text
