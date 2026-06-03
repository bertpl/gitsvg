"""Smoke tests for the shipped `examples/` folder.

Walks every `*.gitsvg.jsonl` file under `examples/`, runs the full
validate + layout + render pipeline, and asserts that each one
produces a non-empty SVG. Guards against bit-rot in the example
sources without requiring a visual-regression check.
"""

from pathlib import Path

import pytest

from gitsvg.cli._pipeline import apply_and_validate
from gitsvg.errors import ValidationReport
from gitsvg.imports import resolve_imports
from gitsvg.layout import compute_layout
from gitsvg.parse import parse_jsonl_file
from gitsvg.render import compute_minify_config, minify, render

EXAMPLES_DIR = Path(__file__).parent.parent.parent / "examples"


# ==================================================================================================
#  Discovery
# ==================================================================================================
def _example_files() -> list[Path]:
    """Return all `*.gitsvg.jsonl` files in the `examples/` folder, sorted."""
    return sorted(EXAMPLES_DIR.glob("*.gitsvg.jsonl"))


EXAMPLE_FILES = _example_files()


def test_examples_folder_is_non_empty() -> None:
    """Sanity check: the discovery glob actually finds something."""
    # --- assert -----------------------
    assert EXAMPLE_FILES, f"no examples found under {EXAMPLES_DIR}"


# ==================================================================================================
#  Per-file pipeline
# ==================================================================================================
@pytest.mark.parametrize("path", EXAMPLE_FILES, ids=lambda p: p.name)
def test_example_validates_and_renders(path: Path) -> None:
    """Each example must validate cleanly and render to non-empty SVG."""
    # --- arrange ----------------------
    report = ValidationReport()

    # --- act --------------------------
    parsed_ops, report = parse_jsonl_file(path)
    expanded = resolve_imports(parsed_ops, file=path, report=report)
    state, theme = apply_and_validate(expanded, report)
    layout_settings, _ = theme.split()
    layout = compute_layout(state, layout_settings)
    drawing = render(layout, theme)
    svg_text = drawing.as_svg()

    # --- assert -----------------------
    assert report.is_clean(), f"{path.name}: unexpected validation errors {[e.format() for e in report.errors]}"
    assert svg_text.strip(), f"{path.name}: rendered SVG is empty"
    assert "<svg" in svg_text, f"{path.name}: rendered output is not an SVG document"


@pytest.mark.parametrize("path", EXAMPLE_FILES, ids=lambda p: p.name)
def test_example_renders_smaller_under_small_flag(path: Path) -> None:
    """Each example must produce a strictly smaller output under bare `--small` (L2)."""
    # --- arrange / act ----------------
    parsed_ops, report = parse_jsonl_file(path)
    expanded = resolve_imports(parsed_ops, file=path, report=report)
    state, theme = apply_and_validate(expanded, report)
    layout_settings, renderer_settings = theme.split()
    drawing = render(compute_layout(state, layout_settings), renderer_settings)
    default_svg = drawing.as_svg()
    config = compute_minify_config(2)
    small_svg = minify(drawing.as_svg(header="", skip_css=True, skip_js=True), config, renderer_settings)

    # --- assert -----------------------
    assert report.is_clean(), f"{path.name}: unexpected validation errors"
    assert len(small_svg) < len(default_svg), (
        f"{path.name}: --small output ({len(small_svg)} bytes) is not smaller than default ({len(default_svg)} bytes)"
    )
    assert "<svg" in small_svg, f"{path.name}: --small output is not a valid SVG"
