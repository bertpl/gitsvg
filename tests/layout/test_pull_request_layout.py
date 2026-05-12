"""Tests for the layout-time construction of `LayoutPullRequest` entries."""

from gitsvg.layout import Layout, compute_layout
from gitsvg.parse import parse_jsonl_text
from gitsvg.state import apply_ops


def _layout_from(text: str) -> Layout:
    """Parse JSONL → state → layout, asserting clean validation."""
    parsed, report = parse_jsonl_text(text, file="x.jsonl")
    state = apply_ops(parsed, report)
    assert report.is_clean(), f"unexpected errors: {[e.format() for e in report.errors]}"
    return compute_layout(state)


# ==================================================================================================
#  No PRs → empty list
# ==================================================================================================
def test_layout_without_prs_has_empty_pull_requests_list() -> None:
    # --- act --------------------------
    layout = _layout_from(
        '{"op": "branch", "name": "main"}\n{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
    )

    # --- assert -----------------------
    assert layout.pull_requests == []


# ==================================================================================================
#  One PR — endpoint resolution
# ==================================================================================================
def test_pr_endpoints_track_current_branch_tips() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "first"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "feat", "id": "f1", "msg": "wip"}\n'
        '{"op": "pull_request", "id": "pr1", "from": "feat", "into": "main", "title": "Add the thing"}\n'
    )

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    assert len(layout.pull_requests) == 1
    pr = layout.pull_requests[0]
    assert pr.id == "pr1"
    assert pr.title == "Add the thing"

    # Resolve branch positions out of the layout.
    by_name = {b.name: b for b in layout.branches}
    feat = by_name["feat"]
    main = by_name["main"]

    # Arc starts at source tip — the row of feat's latest commit (f1).
    assert pr.from_branch_pos == feat.branch_pos
    assert pr.from_commit_pos == feat.end

    # Arc lands on into's lane at the projected merge row.
    assert pr.to_branch_pos == main.branch_pos
    assert pr.to_commit_pos == max(feat.end, main.end) + 1

    # Colour-tagging points at the source branch's id.
    assert pr.color_branch_id == feat.id


def test_pr_without_title_has_none_title() -> None:
    # --- act --------------------------
    layout = _layout_from(
        '{"op": "branch", "name": "main"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
        '{"op": "pull_request", "from": "feat", "into": "main"}\n'
    )

    # --- assert -----------------------
    assert len(layout.pull_requests) == 1
    assert layout.pull_requests[0].title is None


# ==================================================================================================
#  Live-tracking — adding commits after the PR shifts its endpoints
# ==================================================================================================
def test_pr_endpoints_advance_when_commits_land_after_pr_op() -> None:
    """Both endpoints recompute from the *final* state, not the state at PR-op time."""
    # --- arrange ----------------------
    early = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "feat", "id": "f1", "msg": "wip"}\n'
        '{"op": "pull_request", "id": "pr1", "from": "feat", "into": "main"}\n'
    )
    later = early + (
        '{"op": "commit", "branch": "feat", "id": "f2", "msg": "polish"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "side fix"}\n'
    )

    # --- act --------------------------
    early_pr = _layout_from(early).pull_requests[0]
    later_pr = _layout_from(later).pull_requests[0]

    # --- assert -----------------------
    assert later_pr.from_commit_pos > early_pr.from_commit_pos
    assert later_pr.to_commit_pos > early_pr.to_commit_pos


# ==================================================================================================
#  Canvas auto-fit accommodates the projected merge row
# ==================================================================================================
def test_pr_projected_merge_row_extends_canvas_auto_fit() -> None:
    """A PR's projected merge row sits one beyond the latest commit; canvas grows to fit it."""
    # --- arrange ----------------------
    text_without_pr = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "first"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "feat", "id": "f1", "msg": "wip"}\n'
    )
    text_with_pr = text_without_pr + ('{"op": "pull_request", "id": "pr1", "from": "feat", "into": "main"}\n')

    # --- act --------------------------
    layout_without = _layout_from(text_without_pr)
    layout_with = _layout_from(text_with_pr)

    # --- assert -----------------------
    assert layout_with.canvas.n_commits > layout_without.canvas.n_commits


# ==================================================================================================
#  Pinned canvas — declared n_commits wins even if the PR endpoint exceeds it
# ==================================================================================================
def test_pinned_n_commits_wins_over_pr_endpoint() -> None:
    """When `canvas.n_commits` is pinned, the PR's projected merge row does not extend it."""
    # --- arrange / act ----------------
    layout = _layout_from(
        '{"op": "canvas", "n_commits": 3}\n'
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "first"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "feat", "id": "f1", "msg": "wip"}\n'
        '{"op": "pull_request", "id": "pr1", "from": "feat", "into": "main"}\n'
    )

    # --- assert -----------------------
    assert layout.canvas.n_commits == 3


# ==================================================================================================
#  Multiple PRs preserve declaration order
# ==================================================================================================
def test_multiple_prs_preserve_declaration_order() -> None:
    # --- arrange / act ----------------
    layout = _layout_from(
        '{"op": "branch", "name": "main"}\n'
        '{"op": "branch", "name": "a", "from_branch": "main"}\n'
        '{"op": "branch", "name": "b", "from_branch": "main"}\n'
        '{"op": "pull_request", "id": "pr_a", "from": "a", "into": "main"}\n'
        '{"op": "pull_request", "id": "pr_b", "from": "b", "into": "main"}\n'
    )

    # --- assert -----------------------
    ids = [pr.id for pr in layout.pull_requests]
    assert ids == ["pr_a", "pr_b"]
