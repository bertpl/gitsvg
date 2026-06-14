"""Tests for the public `gitsvg.render_text` entry point."""

import json
from pathlib import Path

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


def test_render_text_rejects_import_ops_with_e306() -> None:
    # --- arrange ----------------------
    source = '{"op": "import", "path": "./some_base.gitsvg.jsonl"}\n'

    # --- act --------------------------
    with pytest.raises(GitsvgValidationError) as excinfo:
        render_text(source)

    # --- assert -----------------------
    assert "E306" in {e.code for e in excinfo.value.report.errors}


def test_render_text_never_reads_an_existing_file_via_import(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """An import whose target exists (CWD-relative or absolute) is rejected, not read."""
    # --- arrange ----------------------
    # A real, valid file both reachable relative to CWD and via its absolute path.
    foreign = tmp_path / "foreign.gitsvg.jsonl"
    foreign.write_text('{"op": "branch", "name": "exfiltrated-branch"}\n')
    monkeypatch.chdir(tmp_path)
    relative_source = '{"op": "import", "path": "./foreign.gitsvg.jsonl"}\n'
    # Build via json.dumps so the absolute path is JSON-escaped — on Windows
    # it contains backslashes that would otherwise be invalid JSON escapes.
    absolute_source = json.dumps({"op": "import", "path": str(foreign)}) + "\n"

    for source in (relative_source, absolute_source):
        # --- act ----------------------
        with pytest.raises(GitsvgValidationError) as excinfo:
            render_text(source)

        # --- assert -------------------
        codes = {e.code for e in excinfo.value.report.errors}
        assert "E306" in codes
        # Rejected before any read: no parse/read errors for the foreign
        # file, and its content never surfaces anywhere in the failure.
        assert not codes & {"E001", "E302"}
        assert "exfiltrated-branch" not in str(excinfo.value)


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
