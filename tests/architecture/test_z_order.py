"""Architecture guard for the renderer's cross-element z-order.

Draw order is implicit — it emerges from the sequence of append calls in
`render()` — and documented as the back-to-front list in the
`gitsvg.render._renderer` module docstring. These guards pin the two
invariants that list promises, so a future reorder that violates them
fails here rather than silently shipping a layering regression:

- commit dots sit above every line-type element (guides, arcs, branch
  lines, PR arcs — all `<path>`);
- commit dots sit below every text-bearing element (pills and labels —
  all `<text>`).
"""

import xml.etree.ElementTree as ET

from gitsvg.layout import compute_layout
from gitsvg.parse import parse_jsonl_text
from gitsvg.render import render
from gitsvg.state import apply_ops
from tests._jsonl import build_jsonl

# A diagram exercising every element type: two branches, a branch-off, a
# merge, an open pull request, and commit messages (so dots, lines, arcs,
# pills, and labels are all emitted).
_ALL_ELEMENTS_DIAGRAM = build_jsonl(
    {"op": "branch", "name": "main"},
    {"op": "commit", "branch": "main", "id": "c1", "msg": "init"},
    {"op": "branch", "name": "feature", "from_branch": "main"},
    {"op": "commit", "branch": "feature", "id": "f1", "msg": "wip"},
    {"op": "pull_request", "id": "pr1", "from": "feature", "into": "main", "title": "PR 1"},
    {"op": "commit", "branch": "feature", "id": "f2", "msg": "more"},
    {"op": "merge", "from": "feature", "into": "main", "as": "m1", "msg": "merge"},
)


def _drawable_tags_in_order(text: str) -> list[str]:
    """Render `text` and return the local tag names of drawn elements in document order."""
    parsed, report = parse_jsonl_text(text, file="x.jsonl")
    state, theme = apply_ops(parsed, report)
    svg = render(compute_layout(state), theme.split()[1]).as_svg()
    drawables = {"path", "circle", "rect", "text", "line"}
    return [el.tag.split("}")[-1] for el in ET.fromstring(svg).iter() if el.tag.split("}")[-1] in drawables]


def test_commit_dots_sit_above_all_lines() -> None:
    # --- arrange ----------------------
    tags = _drawable_tags_in_order(_ALL_ELEMENTS_DIAGRAM)

    # --- act --------------------------
    last_path = max(i for i, t in enumerate(tags) if t == "path")
    first_circle = min(i for i, t in enumerate(tags) if t == "circle")

    # --- assert -----------------------
    # Every line-type element (guides, arcs, branch lines, PR arcs) is a
    # <path>; commit dots are <circle>. All paths precede all circles.
    assert last_path < first_circle


def test_commit_dots_sit_below_all_text() -> None:
    # --- arrange ----------------------
    tags = _drawable_tags_in_order(_ALL_ELEMENTS_DIAGRAM)

    # --- act --------------------------
    last_circle = max(i for i, t in enumerate(tags) if t == "circle")
    first_text = min(i for i, t in enumerate(tags) if t == "text")

    # --- assert -----------------------
    # All text-bearing elements (pill text + commit labels) are <text>
    # and come after every commit dot.
    assert last_circle < first_text
