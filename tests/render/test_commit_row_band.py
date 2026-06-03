"""Tests for commit-row banding — the `commit_row_band_color` zebra stripes."""

import xml.etree.ElementTree as ET

from gitsvg._value_types import Orientation
from gitsvg.layout import compute_layout
from gitsvg.parse import parse_jsonl_text
from gitsvg.render import render
from gitsvg.render._canvas import RenderCanvas
from gitsvg.render._geometry import commit_row_band_rect
from gitsvg.state import apply_ops
from gitsvg.theme import DEFAULT_THEME, DefaultTheme

# A single branch with four commits → commit rows 0, 1, 2, 3 (n_commits == 4),
# so odd-index rows 1 and 3 carry a band.
_FOUR_ROWS = (
    '{"op": "branch", "name": "main"}\n'
    '{"op": "commit", "branch": "main", "id": "c1", "msg": "a"}\n'
    '{"op": "commit", "branch": "main", "id": "c2", "msg": "b"}\n'
    '{"op": "commit", "branch": "main", "id": "c3", "msg": "c"}\n'
    '{"op": "commit", "branch": "main", "id": "c4", "msg": "d"}\n'
)

_BAND = "#0000ff80"


def _layout(text: str):
    parsed, report = parse_jsonl_text(text, file="x.jsonl")
    state, _theme = apply_ops(parsed, report)
    return compute_layout(state)


def _band_rects(svg: str, fill: str) -> list[ET.Element]:
    """Return every `<rect>` element painted with `fill`, in document order."""
    return [el for el in ET.fromstring(svg).iter() if el.tag.split("}")[-1] == "rect" and el.attrib.get("fill") == fill]


# ==================================================================================================
#  Geometry helper
# ==================================================================================================
def _canvas(orientation: Orientation) -> RenderCanvas:
    return RenderCanvas(
        width=200.0,
        height=300.0,
        n_commits=4,
        n_branches=1,
        branch_spacing=80.0,
        commit_spacing=40.0,
        margin_left=20.0,
        margin_right=20.0,
        margin_bottom=20.0,
        margin_top=20.0,
        orientation=orientation,
    )


def test_band_rect_is_full_width_in_vertical_orientation() -> None:
    """In `bt`/`tb` a row band is a full-width horizontal stripe, `commit_spacing` tall."""
    # --- arrange ----------------------
    canvas = _canvas(Orientation.BT)

    # --- act --------------------------
    x, _y, width, height = commit_row_band_rect(1, canvas)

    # --- assert -----------------------
    assert x == 0.0
    assert width == canvas.width
    assert height == canvas.commit_spacing


def test_band_rect_is_full_height_in_horizontal_orientation() -> None:
    """In `lr`/`rl` a row band is a full-height vertical stripe, `commit_spacing` wide."""
    # --- arrange ----------------------
    canvas = _canvas(Orientation.LR)

    # --- act --------------------------
    _x, y, width, height = commit_row_band_rect(1, canvas)

    # --- assert -----------------------
    assert y == 0.0
    assert height == canvas.height
    assert width == canvas.commit_spacing


# ==================================================================================================
#  Rendering
# ==================================================================================================
def test_default_theme_emits_no_band_rects() -> None:
    """With `commit_row_band_color` unset (default), no band rect is drawn — output unchanged."""
    # --- arrange ----------------------
    layout = _layout(_FOUR_ROWS)

    # --- act --------------------------
    svg = render(layout, DEFAULT_THEME).as_svg()

    # --- assert -----------------------
    assert '<rect x="0"' not in svg


def test_visible_band_color_stripes_odd_rows() -> None:
    """A visible band color paints one full-width band per odd commit row (row 0 bare)."""
    # --- arrange ----------------------
    layout = _layout(_FOUR_ROWS)
    theme = DefaultTheme.build({"commit_row_band_color": _BAND})

    # --- act --------------------------
    svg = render(layout, theme).as_svg()
    bands = _band_rects(svg, _BAND)

    # --- assert -----------------------
    # Rows 1 and 3 of {0, 1, 2, 3} → exactly two bands, each full-width (x == 0).
    assert len(bands) == 2
    assert all(b.attrib["x"] == "0" for b in bands)


def test_bands_sit_below_commit_dots() -> None:
    """Band rects are emitted before the commit dots (back of the z-order)."""
    # --- arrange ----------------------
    layout = _layout(_FOUR_ROWS)
    theme = DefaultTheme.build({"commit_row_band_color": _BAND})

    # --- act --------------------------
    svg = render(layout, theme).as_svg()
    els = list(ET.fromstring(svg).iter())
    tags = [el.tag.split("}")[-1] for el in els]
    fills = [el.attrib.get("fill") for el in els]

    # --- assert -----------------------
    last_band = max(i for i, f in enumerate(fills) if f == _BAND)
    first_circle = min(i for i, t in enumerate(tags) if t == "circle")
    assert last_band < first_circle


def test_fully_transparent_band_color_emits_nothing() -> None:
    """An explicit but fully-transparent band color paints no bands (treated as off)."""
    # --- arrange ----------------------
    layout = _layout(_FOUR_ROWS)
    theme = DefaultTheme.build({"commit_row_band_color": "#00000000"})

    # --- act --------------------------
    svg = render(layout, theme).as_svg()

    # --- assert -----------------------
    assert '<rect x="0"' not in svg
