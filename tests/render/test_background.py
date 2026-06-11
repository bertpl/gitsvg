"""Tests for the canvas-background rendering (introduced with the `Theme`)."""

from gitsvg.layout import compute_layout
from gitsvg.parse import parse_jsonl_text
from gitsvg.render import render
from gitsvg.state import apply_ops
from gitsvg.theme import DEFAULT_THEME, DefaultTheme


def _layout(text: str):
    parsed, report = parse_jsonl_text(text, file="x.jsonl")
    state, _theme = apply_ops(parsed, report)
    return compute_layout(state)


def test_default_theme_emits_no_background_rect() -> None:
    """With `background_color=None` (the default), the SVG carries no
    full-canvas background rectangle — output remains transparent."""
    # --- arrange ----------------------
    layout = _layout('{"op": "branch", "name": "main"}\n{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n')

    # --- act --------------------------
    svg = render(layout, DEFAULT_THEME.split()[1]).as_svg()

    # --- assert -----------------------
    # No `<rect>` covering the whole canvas. The pill rects are present, but
    # they don't start at x="0" y="0".
    assert '<rect x="0" y="0"' not in svg


def test_background_color_accepts_alpha_hex() -> None:
    """Color fields take an optional alpha channel — a translucent background validates and resolves."""
    # --- arrange ----------------------
    parsed, report = parse_jsonl_text(
        '{"op": "theme", "background_color": "#11223344"}\n'
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n',
        file="x.jsonl",
    )

    # --- act --------------------------
    _state, theme = apply_ops(parsed, report)

    # --- assert -----------------------
    assert report.is_clean()
    assert theme.background_color == "#11223344"


def test_theme_with_background_emits_full_canvas_rect_first() -> None:
    """A non-None `theme.background_color` emits a full-canvas `<rect>` as
    the first painted element (Z-order layer 0, behind all other content)."""
    # --- arrange ----------------------
    layout = _layout('{"op": "branch", "name": "main"}\n{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n')
    theme = DefaultTheme.build({"background_color": "#ff00ff"})

    # --- act --------------------------
    svg = render(layout, theme.split()[1]).as_svg()

    # --- assert -----------------------
    # The background rect carries the chosen color and starts at the origin.
    assert 'x="0" y="0"' in svg
    assert 'fill="#ff00ff"' in svg
    # It precedes the branch-guide path that's normally the back-most layer.
    bg_pos = svg.index('fill="#ff00ff"')
    first_path_pos = svg.index("<path")
    assert bg_pos < first_path_pos
