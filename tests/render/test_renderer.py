"""End-to-end tests for the renderer — produces valid SVG with expected primitives."""

import xml.etree.ElementTree as ET

from gitsvg.layout import compute_layout
from gitsvg.parse import parse_jsonl_text
from gitsvg.render import render
from gitsvg.state import apply_ops


def _render_from(text: str):
    parsed, report = parse_jsonl_text(text, file="x.jsonl")
    state, theme = apply_ops(parsed, report)
    layout = compute_layout(state)
    return render(layout, theme)


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
    # auto-fits to include pill room below the lowest dot. Width may be
    # rendered as int or float depending on whether any auto-fit margin
    # widened past the integer theme default.
    assert ('width="200"' in svg_text) or ('width="200.0"' in svg_text)
    assert 'height="' in svg_text  # auto-fit value depends on label widths


def test_render_emits_expected_path_and_circle_counts() -> None:
    """drawsvg renders both `Line` and `Path` as `<path>`. With two branches and
    a fork (main has one commit so its line is suppressed; feat has two so its
    line shows), the SVG carries: 2 guides + 1 branch-off arc + 1 branch line
    = 4 paths, plus one circle per commit."""
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
    assert svg_text.count("<path") == 4  # 2 guides + 1 arc + 1 line (feat)
    assert svg_text.count("<circle") == 3  # c1 + f1 + f2


def test_empty_branch_emits_no_branch_line() -> None:
    """A declared branch with no commits gets no branch-line element — empty
    branches are visually represented by their name pill alone."""
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "c2", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
    )

    # --- act --------------------------
    svg_text = _render_from(text).as_svg()

    # --- assert -----------------------
    # 2 guides (main lane + feat lane) + 1 branch-off arc + 1 branch line
    # (main only; feat is empty so its line is suppressed) = 4 paths. If
    # the empty branch's line were still emitted as a degenerate path the
    # count would be 5.
    assert svg_text.count("<path") == 4


def test_connectors_are_grouped_per_branch_in_declaration_order() -> None:
    """Each branch's connectors and line draw as one contiguous color group.

    The renderer loops branches in declaration order and draws all of a
    branch's arcs + line + PR arcs before moving to the next, so the
    branch-colored `<path>` strokes appear grouped — every `main` stroke
    before every `feature` stroke — rather than interleaved by element
    type."""
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main", "color": "#111111"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "a"}\n'
        '{"op": "commit", "branch": "main", "id": "c2", "msg": "b"}\n'
        '{"op": "branch", "name": "feature", "from_branch": "main", "color": "#222222"}\n'
        '{"op": "commit", "branch": "feature", "id": "f1", "msg": "c"}\n'
        '{"op": "commit", "branch": "feature", "id": "f2", "msg": "d"}\n'
        '{"op": "merge", "from": "feature", "into": "main", "as": "m1", "msg": "m"}\n'
    )

    # --- act --------------------------
    # Collect path strokes in the line band only — everything before the
    # first commit dot (<circle>), so the default checkmark merge tick
    # (a branch-colored path drawn later, in the dots layer) doesn't
    # leak into the band-grouping assertion.
    svg = _render_from(text).as_svg()
    band_strokes: list[str | None] = []
    for el in ET.fromstring(svg).iter():
        tag = el.tag.split("}")[-1]
        if tag == "circle":
            break
        if tag == "path":
            band_strokes.append(el.get("stroke"))
    branch_strokes = [s for s in band_strokes if s in ("#111111", "#222222")]

    # --- assert -----------------------
    # main's branch line (#111111) precedes feature's branch-off arc,
    # line, and merge arc (#222222) — grouped, not interleaved.
    assert branch_strokes == ["#111111", "#222222", "#222222", "#222222"]


def test_render_preserves_branch_color_in_dot_fill() -> None:
    """Each commit's dot is filled with its branch's resolved color."""
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main", "color": "#aabbcc"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
    )

    # --- act --------------------------
    svg_text = _render_from(text).as_svg()

    # --- assert -----------------------
    # The override color appears on the branch line and the commit dot.
    assert "#aabbcc" in svg_text
