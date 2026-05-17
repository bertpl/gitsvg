"""End-to-end visually-lossless guarantee: L1 and L2 match L0 across shipped examples.

For each `examples/*.gitsvg.jsonl`, renders at L0, L1, L2 and asserts
DOM equivalence between (L0, L1) and (L0, L2) via the DOM-comparison
helper. L3 is excluded — its font-fallback trim is an opt-in
visual deviation, not a lossless transform.
"""

from pathlib import Path

import pytest

from gitsvg.imports import resolve_imports
from gitsvg.layout import compute_layout
from gitsvg.parse import parse_jsonl_file
from gitsvg.render import compute_minify_config, minify, render
from gitsvg.state import apply_ops, check_end_of_file
from tests.render.test_minify._dom_compare import assert_dom_equivalent

EXAMPLES_DIR = Path(__file__).parent.parent.parent.parent / "examples"
EXAMPLE_FILES = sorted(EXAMPLES_DIR.glob("*.gitsvg.jsonl"))


def _render_at_level(path: Path, level: int) -> str:
    """Render `path` end-to-end through the pipeline at `level`; return SVG markup."""
    parsed_ops, report = parse_jsonl_file(path)
    expanded = resolve_imports(parsed_ops, file=path, report=report)
    state, theme = apply_ops(expanded, report)
    check_end_of_file(state, report)
    assert report.is_clean(), f"{path.name}: unexpected validation errors {[e.format() for e in report.errors]}"
    layout = compute_layout(state)
    _, renderer_settings = theme.split()
    drawing = render(layout, renderer_settings)
    config = compute_minify_config(level)
    if config.level == 0:
        return drawing.as_svg()
    svg = drawing.as_svg(header="", skip_css=True, skip_js=True)
    return minify(svg, config, renderer_settings)


@pytest.mark.parametrize("path", EXAMPLE_FILES, ids=lambda p: p.name)
def test_l1_is_dom_equivalent_to_l0(path: Path) -> None:
    """L1 (lossless basics) must render DOM-equivalent to L0 for every shipped example."""
    # --- act --------------------------
    l0 = _render_at_level(path, 0)
    l1 = _render_at_level(path, 1)

    # --- assert -----------------------
    assert_dom_equivalent(l0, l1, label_a="L0", label_b="L1")


@pytest.mark.parametrize("path", EXAMPLE_FILES, ids=lambda p: p.name)
def test_l2_is_dom_equivalent_to_l0(path: Path) -> None:
    """L2 (lossless+) must render DOM-equivalent to L0 for every shipped example."""
    # --- act --------------------------
    l0 = _render_at_level(path, 0)
    l2 = _render_at_level(path, 2)

    # --- assert -----------------------
    assert_dom_equivalent(l0, l2, label_a="L0", label_b="L2")
