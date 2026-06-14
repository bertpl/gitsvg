"""Fractional values for the numeric size fields (`branch_spacing`,
`commit_spacing`, `branch_line_width`, `commit_radius`, `highlight_radius`,
`merge_commit_radius`).

These were `int` on `Theme` while `float` on the `theme:` op, so a fractional
override flowed untyped through `build()` and crashed the terminal Pydantic
constructor with a raw traceback. They are now `float`; whole values are
normalized back to `int` so the SVG renders them without a trailing `.0`
(byte-identical to pre-float diagrams), while fractional values pass through
for sub-pixel output.
"""

import pytest

from gitsvg.layout import compute_layout
from gitsvg.parse import parse_jsonl_text
from gitsvg.render import render
from gitsvg.state import apply_ops
from gitsvg.theme import DefaultTheme
from tests._jsonl import build_jsonl

_SIZE_FIELDS = [
    "branch_spacing",
    "commit_spacing",
    "branch_line_width",
    "commit_radius",
    "highlight_radius",
    "merge_commit_radius",
]


@pytest.mark.parametrize("field", _SIZE_FIELDS)
def test_fractional_size_override_is_accepted_as_float(field: str) -> None:
    """A fractional size no longer crashes `build()` (it used to raise a raw
    `pydantic` ValidationError) and is stored as a float for sub-pixel output."""
    # --- arrange / act ----------------
    theme = DefaultTheme.build({field: 5.5})

    # --- assert -----------------------
    value = getattr(theme, field)
    assert value == 5.5
    assert isinstance(value, float)


@pytest.mark.parametrize("field", _SIZE_FIELDS)
def test_whole_size_override_normalizes_to_int(field: str) -> None:
    """A whole-number size is stored as `int`, so the SVG renders it without a
    trailing `.0` — keeping output byte-identical to pre-float diagrams."""
    # --- arrange / act ----------------
    theme = DefaultTheme.build({field: 8})

    # --- assert -----------------------
    value = getattr(theme, field)
    assert value == 8
    assert isinstance(value, int)


@pytest.mark.parametrize(("value", "expected_type"), [(8, int), (5.5, float)])
def test_split_preserves_size_value_type_on_renderer_slice(value: float, expected_type: type) -> None:
    """The whole→int / fractional→float normalization survives the
    `RendererSettings` round-trip in `split()`, so the renderer formats the
    value identically to the resolved theme."""
    # --- arrange ----------------------
    theme = DefaultTheme.build({"commit_radius": value})

    # --- act --------------------------
    _layout_settings, renderer_settings = theme.split()

    # --- assert -----------------------
    assert renderer_settings.commit_radius == value
    assert isinstance(renderer_settings.commit_radius, expected_type)


def test_fractional_theme_op_validates_cleanly_through_apply() -> None:
    """The exact scenario that used to crash `gitsvg validate` / `render` with a
    raw traceback: a `theme:` op with a fractional spacing now resolves cleanly
    through the apply pass."""
    # --- arrange / act ----------------
    parsed, report = parse_jsonl_text(build_jsonl({"op": "theme", "branch_spacing": 100.5}), file="x.jsonl")
    _state, theme = apply_ops(parsed, report)

    # --- assert -----------------------
    assert report.is_clean(), [e.format() for e in report.errors]
    assert theme.branch_spacing == 100.5


@pytest.mark.parametrize(
    ("radius", "expected_attr", "forbidden_attr"),
    [(7.5, 'r="7.5"', None), (6, 'r="6"', 'r="6.0"')],
)
def test_commit_radius_render_formatting(radius: float, expected_attr: str, forbidden_attr: str | None) -> None:
    """A fractional `commit_radius` reaches the SVG as a sub-pixel value; a whole
    one renders without a trailing `.0` (byte-identical to pre-float output)."""
    # --- arrange ----------------------
    jsonl = build_jsonl(
        {"op": "theme", "commit_radius": radius},
        {"op": "branch", "name": "main"},
        {"op": "commit", "branch": "main", "msg": "x"},
    )
    parsed, report = parse_jsonl_text(jsonl, file="x.jsonl")
    state, theme = apply_ops(parsed, report)
    assert report.is_clean(), [e.format() for e in report.errors]

    # --- act --------------------------
    svg = render(compute_layout(state), theme.split()[1]).as_svg()

    # --- assert -----------------------
    assert expected_attr in svg
    if forbidden_attr is not None:
        assert forbidden_attr not in svg
