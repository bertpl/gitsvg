"""Tests for the public `gitsvg.render_text` entry point."""

import pytest

import gitsvg
from gitsvg import GitsvgValidationError, render_text

_VALID_SOURCE = (
    '{"op": "branch", "name": "main"}\n'
    '{"op": "commit", "branch": "main", "id": "c1", "msg": "initial"}\n'
    '{"op": "commit", "branch": "main", "id": "c2", "msg": "second"}\n'
)


def test_render_text_is_part_of_the_public_surface() -> None:
    # --- act / assert -----------------
    assert gitsvg.render_text is render_text
    assert "render_text" in gitsvg.__all__
    assert "GitsvgValidationError" in gitsvg.__all__
    assert "ValidationReport" in gitsvg.__all__


def test_render_text_valid_returns_inline_embeddable_svg() -> None:
    # --- act --------------------------
    svg = render_text(_VALID_SOURCE)

    # --- assert -----------------------
    assert "<svg" in svg
    assert "xmlns" in svg  # the root <svg> carries its namespace for inlining
    assert "<?xml" not in svg  # no prolog
    assert "<style" not in svg  # no injected CSS
    assert "<script" not in svg  # no injected JS


def test_render_text_invalid_raises_carrying_the_report() -> None:
    # --- arrange ----------------------
    source = '{"op": "commit", "branch": "main", "msg": "x"}\n'  # main never declared

    # --- act --------------------------
    with pytest.raises(GitsvgValidationError) as excinfo:
        render_text(source)

    # --- assert -----------------------
    assert not excinfo.value.report.is_clean()
    assert len(excinfo.value.report.errors) > 0


def test_render_text_import_op_fails_without_a_base_path() -> None:
    # --- arrange ----------------------
    source = '{"op": "import", "path": "./nonexistent_base.gitsvg.jsonl"}\n'

    # --- act / assert -----------------
    # An in-memory string has no base path to resolve the import against.
    with pytest.raises(GitsvgValidationError):
        render_text(source)


def test_render_text_id_prefix_is_accepted_and_output_stays_stable() -> None:
    # gitsvg emits no element ids today (empty <defs>), so a prefix can't
    # yet change the output; assert it's accepted and the SVG is unchanged.
    # This becomes a meaningful disjoint-id check when an id-emitting
    # feature lands.
    # --- act --------------------------
    default_svg = render_text(_VALID_SOURCE)
    prefixed_svg = render_text(_VALID_SOURCE, id_prefix="diagram1-")

    # --- assert -----------------------
    assert "<svg" in prefixed_svg
    assert prefixed_svg == default_svg
