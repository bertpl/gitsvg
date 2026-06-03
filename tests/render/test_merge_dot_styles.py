"""Tests for the merge-dot style builders and end-to-end merge-commit rendering.

Builder-level: each `_draw_<style>` emits the expected primitives. End-to-end:
the `checkmark` style adds the tick only to merge commits, ordinary commits are
untouched, and every (orientation, style) pair renders cleanly.
"""

import drawsvg as draw
import pytest

from gitsvg._shared.value_types import MergeCommitStyle
from gitsvg.layout import compute_layout
from gitsvg.parse import parse_jsonl_text
from gitsvg.render import render
from gitsvg.render._primitives.merge_dot_styles import (
    _CHECKMARK_DOT_RADIUS_SCALE,
    _MERGE_DOT_BUILDERS,
    _draw_checkmark,
    _draw_circle,
)
from gitsvg.state import apply_ops
from gitsvg.theme import DEFAULT_THEME

# Renderer settings for builder-level tests (supplies stroke color / width).
_, _RT = DEFAULT_THEME.split()

# A diagram with a single merge commit (`mg`) on `main`.
_MERGE_JSONL = (
    '{"op": "branch", "name": "main"}\n'
    '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
    '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
    '{"op": "commit", "branch": "feat", "id": "f1", "msg": "y"}\n'
    '{"op": "merge", "from": "feat", "into": "main", "as": "mg", "msg": "merge"}\n'
)


def _render(jsonl: str) -> str:
    parsed, report = parse_jsonl_text(jsonl, file="x.jsonl")
    state, theme = apply_ops(parsed, report)
    assert report.is_clean(), report.errors
    return render(compute_layout(state), theme).as_svg()


def _with_style(style: MergeCommitStyle) -> str:
    return _render(_MERGE_JSONL + f'{{"op": "theme", "merge_commit_style": "{style.value}"}}\n')


# ==================================================================================================
#  Builder-level — each style emits its characteristic primitives
# ==================================================================================================
def test_draw_circle_emits_one_circle_no_path() -> None:
    # --- arrange ----------------------
    d = draw.Drawing(50, 50)

    # --- act --------------------------
    _draw_circle(d, 25, 25, 5, "#123456", _RT)
    svg = d.as_svg()

    # --- assert -----------------------
    assert svg.count("<circle") == 1
    assert "<path" not in svg


def test_draw_checkmark_emits_circle_plus_tick_with_swapped_fill() -> None:
    # --- arrange ----------------------
    d = draw.Drawing(50, 50)

    # --- act --------------------------
    _draw_checkmark(d, 25, 25, 5, "#123456", _RT)
    svg = d.as_svg()

    # --- assert -----------------------
    assert svg.count("<circle") == 1  # the hollow dot
    assert svg.count("<path") == 1  # the tick
    assert 'fill="white"' in svg  # fill swapped to commit_stroke_color
    assert "#123456" in svg  # branch color now the ring + tick


# ==================================================================================================
#  Default-output invariants
# ==================================================================================================
def test_checkmark_dot_radius_scale_is_eleven_tenths() -> None:
    # --- assert -----------------------
    assert _CHECKMARK_DOT_RADIUS_SCALE == 1.1


def test_checkmark_enlarges_dot_but_keeps_tick_fixed() -> None:
    # The ring is drawn 1.1x the base radius (5 -> 5.5) while the tick stays
    # sized to the base radius — the dot grows but the tick doesn't.
    # --- arrange ----------------------
    d = draw.Drawing(50, 50)

    # --- act --------------------------
    _draw_checkmark(d, 25, 25, 5, "#123456", _RT)
    svg = d.as_svg()

    # --- assert -----------------------
    assert 'r="5.5"' in svg  # ring enlarged to 5 * 1.1
    assert 'stroke-width="1.6"' in svg  # tick = 5 * 0.32, sized to the base radius


def test_non_merge_commits_unaffected_by_checkmark_style() -> None:
    """A diagram with no merge renders byte-identically under `checkmark`."""
    # --- arrange ----------------------
    jsonl = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "c2", "msg": "x"}\n'
    )

    # --- act --------------------------
    plain = _render(jsonl)
    checked = _render(jsonl + '{"op": "theme", "merge_commit_style": "checkmark"}\n')

    # --- assert -----------------------
    assert plain == checked


# ==================================================================================================
#  End-to-end — checkmark marks only the merge dot
# ==================================================================================================
def test_checkmark_adds_one_tick_path_versus_circle() -> None:
    # --- act --------------------------
    circle_svg = _with_style(MergeCommitStyle.CIRCLE)
    check_svg = _with_style(MergeCommitStyle.CHECKMARK)

    # --- assert -----------------------
    assert circle_svg.count("<circle") == check_svg.count("<circle")  # same dot count
    assert check_svg.count("<path") == circle_svg.count("<path") + 1  # one tick added


def test_highlighted_checkmark_merge_dot_composes_highlight_and_scale() -> None:
    # highlight base (7) composes with the checkmark dot scale (1.1) → 7.7.
    # --- arrange ----------------------
    jsonl = (
        _MERGE_JSONL + '{"op": "highlight", "commit": "mg"}\n' + '{"op": "theme", "merge_commit_style": "checkmark"}\n'
    )

    # --- act --------------------------
    svg = _render(jsonl)

    # --- assert -----------------------
    assert 'r="7.7"' in svg  # highlight_radius (7) x checkmark radius_scale (1.1)


# ==================================================================================================
#  merge_commit_radius — independent merge-dot sizing
# ==================================================================================================
def test_merge_commit_radius_defaults_to_commit_radius() -> None:
    """Unset, the merge radius equals `commit_radius`, so merge and ordinary dots match."""
    # --- assert -----------------------
    assert DEFAULT_THEME.merge_commit_radius == DEFAULT_THEME.commit_radius


def test_unset_merge_commit_radius_matches_explicit_commit_radius_output() -> None:
    """Leaving `merge_commit_radius` unset renders byte-identically to setting it to `commit_radius`."""
    # --- arrange ----------------------
    base = _MERGE_JSONL + '{"op": "theme", "merge_commit_style": "circle"}\n'
    explicit = _MERGE_JSONL + '{"op": "theme", "merge_commit_style": "circle", "merge_commit_radius": 5}\n'

    # --- act / assert -----------------
    assert _render(base) == _render(explicit)


def test_merge_commit_radius_sizes_only_merge_dots() -> None:
    """A large `merge_commit_radius` over a small `commit_radius` enlarges only the merge dot."""
    # --- arrange ----------------------
    jsonl = (
        _MERGE_JSONL + '{"op": "theme", "merge_commit_style": "circle", "commit_radius": 3, "merge_commit_radius": 8}\n'
    )

    # --- act --------------------------
    svg = _render(jsonl)

    # --- assert -----------------------
    assert 'r="8"' in svg  # the merge dot takes merge_commit_radius
    assert 'r="3"' in svg  # ordinary dots take commit_radius


@pytest.mark.parametrize("orientation", ["bt", "tb", "lr", "rl"])
@pytest.mark.parametrize("style", [s.value for s in MergeCommitStyle])
def test_renders_in_every_orientation_and_style(orientation: str, style: str) -> None:
    # --- arrange ----------------------
    jsonl = _MERGE_JSONL + f'{{"op": "theme", "orientation": "{orientation}", "merge_commit_style": "{style}"}}\n'

    # --- act --------------------------
    svg = _render(jsonl)

    # --- assert -----------------------
    assert "<circle" in svg
