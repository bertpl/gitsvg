"""Tests for the did-you-mean `suggestion` on E200 / E201 — computed from the
names declared so far and rendered by `ValidationError.format()`."""

import pytest

from tests.state._helpers import build_state_from_jsonl


# ==================================================================================================
#  E200 — branch not declared
# ==================================================================================================
@pytest.mark.parametrize(
    ("declared", "typo", "expected"),
    [
        ("main", "mian", "main"),  # classic transposition  # codespell:ignore mian
        ("dev", "div", "dev"),  # short name — passes only at difflib's 0.6 cutoff
        ("main", "zzqq", None),  # nothing close
    ],
)
def test_e200_suggestion_from_declared_branches(declared: str, typo: str, expected: str | None) -> None:
    # --- arrange ----------------------
    text = f'{{"op": "branch", "name": "{declared}"}}\n{{"op": "commit", "branch": "{typo}", "msg": "x"}}\n'

    # --- act --------------------------
    _, report = build_state_from_jsonl(text)

    # --- assert -----------------------
    assert [e.code for e in report.errors] == ["E200"]
    assert report.errors[0].suggestion == expected


def test_e200_suggestion_renders_in_formatted_output() -> None:
    # --- arrange ----------------------
    text = '{"op": "branch", "name": "main"}\n{"op": "commit", "branch": "mian", "msg": "x"}\n'  # codespell:ignore mian

    # --- act --------------------------
    _, report = build_state_from_jsonl(text)

    # --- assert -----------------------
    assert "did you mean 'main'?" in report.errors[0].format()


def test_e200_suggestion_considers_only_branches_declared_so_far() -> None:
    """A branch declared *after* the failing op is not a candidate."""
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "trunk"}\n'
        '{"op": "commit", "branch": "feat", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "trunk"}\n'
    )

    # --- act --------------------------
    _, report = build_state_from_jsonl(text)

    # --- assert -----------------------
    e200 = next(e for e in report.errors if e.code == "E200")
    assert e200.suggestion is None


def test_e200_hint_and_suggestion_co_render() -> None:
    """The `branch` op's from_commit hint and a name suggestion answer different
    questions and may both appear."""
    # --- arrange ----------------------
    # A commit literally named "mian" exists (fires the from_commit hint) and  # codespell:ignore mian
    # branch "main" is the closest declared branch (fires the suggestion).
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "mian", "msg": "x"}\n'  # codespell:ignore mian
        '{"op": "branch", "name": "feat", "from_branch": "mian"}\n'  # codespell:ignore mian
    )

    # --- act --------------------------
    _, report = build_state_from_jsonl(text)

    # --- assert -----------------------
    assert [e.code for e in report.errors] == ["E200"]
    rendered = report.errors[0].format()
    assert "did you mean 'from_commit'?" in rendered  # the hint, inside the message
    assert rendered.endswith("— did you mean 'main'?")  # the suggestion tail
    assert report.errors[0].suggestion == "main"


# ==================================================================================================
#  E201 — commit not declared
# ==================================================================================================
def test_e201_highlight_suggests_closest_commit() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "feature-1", "msg": "x"}\n'
        '{"op": "highlight", "commit": "feature1"}\n'
    )

    # --- act --------------------------
    _, report = build_state_from_jsonl(text)

    # --- assert -----------------------
    assert [e.code for e in report.errors] == ["E201"]
    assert report.errors[0].suggestion == "feature-1"


def test_e201_replaces_suggests_closest_commit() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c2", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "c3", "msg": "y", "replaces": ["c2x"]}\n'
    )

    # --- act --------------------------
    _, report = build_state_from_jsonl(text)

    # --- assert -----------------------
    e201 = next(e for e in report.errors if e.code == "E201")
    assert e201.field == "replaces"
    assert e201.suggestion == "c2"


def test_e201_remove_suggests_closest_commit() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "setup-ci", "msg": "x"}\n'
        '{"op": "remove", "commits": ["setup-cl"]}\n'
    )

    # --- act --------------------------
    _, report = build_state_from_jsonl(text)

    # --- assert -----------------------
    e201 = next(e for e in report.errors if e.code == "E201")
    assert e201.suggestion == "setup-ci"
