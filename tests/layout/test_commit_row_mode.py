"""Layout-engine tests for `commit_row_mode` — shared vs unique commit rows."""

from gitsvg.layout import compute_layout
from gitsvg.parse import parse_jsonl_text
from gitsvg.state import apply_ops

# Two branches whose commits interleave in declaration order, so `main`
# and `feat` commits land on the same rows under `shared`.
_INTERLEAVED = (
    '{"op": "branch", "name": "main"}\n'
    '{"op": "commit", "branch": "main", "id": "c1", "msg": "a"}\n'
    '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
    '{"op": "commit", "branch": "feat", "id": "f1", "msg": "b"}\n'
    '{"op": "commit", "branch": "main", "id": "c2", "msg": "c"}\n'
    '{"op": "commit", "branch": "feat", "id": "f2", "msg": "d"}\n'
    '{"op": "commit", "branch": "main", "id": "c3", "msg": "e"}\n'
)


def _rows(text: str) -> dict[str, int]:
    """Parse JSONL → state+theme → layout (with the theme's layout settings); return commit_pos by id."""
    parsed, report = parse_jsonl_text(text, file="x.jsonl")
    state, theme = apply_ops(parsed, report)
    layout_settings, _ = theme.split()
    layout = compute_layout(state, layout_settings)
    return {c.id: c.commit_pos for c in layout.commits.values()}


def test_shared_mode_lets_commits_share_rows() -> None:
    # --- act --------------------------
    rows = _rows(_INTERLEAVED)

    # --- assert -----------------------
    # f1/c2 share row 1 and f2/c3 share row 2 — the compact default.
    assert rows == {"c1": 0, "f1": 1, "c2": 1, "f2": 2, "c3": 2}


def test_unique_mode_gives_every_commit_its_own_row_in_declaration_order() -> None:
    # --- act --------------------------
    rows = _rows(_INTERLEAVED + '{"op": "theme", "commit_row_mode": "unique"}\n')

    # --- assert -----------------------
    # Every commit on its own row, numbered in declaration order.
    assert rows == {"c1": 0, "f1": 1, "c2": 2, "f2": 3, "c3": 4}
    assert len(set(rows.values())) == len(rows)


def test_unique_mode_keeps_commits_below_their_parents() -> None:
    """Unique rows never violate the parent-below constraint, even with a merge."""
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "a"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "feat", "id": "f1", "msg": "b"}\n'
        '{"op": "commit", "branch": "main", "id": "c2", "msg": "c"}\n'
        '{"op": "merge", "from": "feat", "into": "main", "as": "m1", "msg": "m"}\n'
        '{"op": "theme", "commit_row_mode": "unique"}\n'
    )

    # --- act --------------------------
    rows = _rows(text)

    # --- assert -----------------------
    assert len(set(rows.values())) == len(rows)  # all distinct
    assert rows["m1"] > rows["c2"]
    assert rows["m1"] > rows["f1"]


def test_unique_mode_composes_with_gap() -> None:
    """`gap` still leaves empty rows on top of the unique-row assignment."""
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "a"}\n'
        '{"op": "commit", "branch": "main", "id": "c2", "msg": "b", "gap": 2}\n'
        '{"op": "theme", "commit_row_mode": "unique"}\n'
    )

    # --- act --------------------------
    rows = _rows(text)

    # --- assert -----------------------
    # c1 at row 0; c2 leaves 2 empty rows -> row 3.
    assert rows == {"c1": 0, "c2": 3}
