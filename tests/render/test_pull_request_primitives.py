"""Render-level tests for the pull-request primitives.

Asserts on SVG output text (substring/count checks) rather than parsed
shapes — the render pipeline already uses drawsvg, and the goal here
is to confirm the renderer wires the new primitives in correctly.
"""

from gitsvg.layout import compute_layout
from gitsvg.parse import parse_jsonl_text
from gitsvg.render import render
from gitsvg.state import apply_ops


def _render(text: str) -> str:
    """Parse → state → layout → render → SVG string."""
    parsed, report = parse_jsonl_text(text, file="x.jsonl")
    state, _theme = apply_ops(parsed, report)
    assert report.is_clean(), f"unexpected errors: {[e.format() for e in report.errors]}"
    return render(compute_layout(state)).as_svg()


# ==================================================================================================
#  Dashed arc emission
# ==================================================================================================
def test_open_pr_renders_a_dashed_path() -> None:
    """A `<path>` with a `stroke-dasharray` attribute appears once per open PR."""
    # --- arrange / act ----------------
    svg = _render(
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "first"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "feat", "id": "f1", "msg": "wip"}\n'
        '{"op": "pull_request", "from": "feat", "into": "main"}\n'
    )

    # --- assert -----------------------
    # `stroke-dasharray` appears in the branch-guide primitive too, so
    # we check for the PR-specific dash value `6,4` (not `4,4`).
    assert 'stroke-dasharray="6,4"' in svg


def test_no_pr_renders_no_pr_dash() -> None:
    """No PR ops → no `6,4` dash anywhere in the output."""
    # --- arrange / act ----------------
    svg = _render('{"op": "branch", "name": "main"}\n{"op": "commit", "branch": "main", "id": "m1", "msg": "first"}\n')

    # --- assert -----------------------
    assert "6,4" not in svg


# ==================================================================================================
#  Title pill emission
# ==================================================================================================
def test_pr_with_title_renders_pill_text() -> None:
    """A PR with `title:` produces a `<text>` containing the title string."""
    # --- arrange / act ----------------
    svg = _render(
        '{"op": "branch", "name": "main"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
        '{"op": "pull_request", "from": "feat", "into": "main", "title": "Add the thing"}\n'
    )

    # --- assert -----------------------
    assert ">Add the thing<" in svg


def test_pr_without_title_renders_no_pill_text() -> None:
    """A PR without `title:` produces no extra `<text>` element beyond what other ops emit."""
    # --- arrange / act ----------------
    svg_without = _render('{"op": "branch", "name": "main"}\n{"op": "branch", "name": "feat", "from_branch": "main"}\n')
    svg_with_pr = _render(
        '{"op": "branch", "name": "main"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
        '{"op": "pull_request", "from": "feat", "into": "main"}\n'
    )

    # --- assert -----------------------
    # Same number of `<text` elements: the PR added no pill text.
    assert svg_with_pr.count("<text") == svg_without.count("<text")
