"""Tests for the table label rendering (`commit_label_layout: table`)."""

import xml.etree.ElementTree as ET

from gitsvg._shared.value_types import CommitLabelLayout, Orientation
from gitsvg.layout import compute_layout
from gitsvg.parse import parse_jsonl_text
from gitsvg.render import render
from gitsvg.render._canvas import compute_canvas, is_table_active
from gitsvg.state import apply_ops
from gitsvg.theme import DefaultTheme
from tests._jsonl import build_jsonl


def _table_render(text: str, **overrides):
    """Build a table-mode `(layout, renderer_settings, canvas, svg)` for `text`."""
    parsed, report = parse_jsonl_text(text, file="x.jsonl")
    state, _theme = apply_ops(parsed, report)
    theme = DefaultTheme.build({"commit_label_layout": CommitLabelLayout.TABLE, **overrides})
    layout_settings, renderer = theme.split()
    layout = compute_layout(state, layout_settings)
    canvas = compute_canvas(layout, renderer)
    return layout, renderer, canvas, render(layout, renderer).as_svg()


def _texts(svg: str) -> list[ET.Element]:
    return [el for el in ET.fromstring(svg).iter() if el.tag.split("}")[-1] == "text"]


_LINEAR = build_jsonl(
    {"op": "branch", "name": "main"},
    {"op": "commit", "branch": "main", "id": "c1", "msg": "init", "hash": "abc1234"},
    {"op": "commit", "branch": "main", "id": "c2", "msg": "second", "hash": "def5678"},
)


def test_table_mode_allocates_a_region_right_of_the_graph() -> None:
    # --- arrange / act ----------------
    _layout, renderer, canvas, _svg = _table_render(_LINEAR)

    # --- assert -----------------------
    assert is_table_active(renderer)
    assert canvas.table_x_origin > 0


def test_inline_mode_allocates_no_table_region() -> None:
    """The default (`inline`) layout sets no table origin."""
    # --- arrange ----------------------
    parsed, report = parse_jsonl_text(_LINEAR, file="x.jsonl")
    state, _theme = apply_ops(parsed, report)
    _layout_settings, renderer = DefaultTheme.build({}).split()
    layout = compute_layout(state)

    # --- act --------------------------
    canvas = compute_canvas(layout, renderer)

    # --- assert -----------------------
    assert not is_table_active(renderer)
    assert canvas.table_x_origin == 0.0


def test_horizontal_orientation_makes_table_inactive() -> None:
    """`table` + a horizontal orientation (the E223 case) falls back to inline here."""
    # --- arrange / act ----------------
    _layout_settings, renderer = DefaultTheme.build(
        {"commit_label_layout": CommitLabelLayout.TABLE, "orientation": Orientation.LR}
    ).split()

    # --- assert -----------------------
    assert not is_table_active(renderer)


def test_table_draws_message_and_hash_in_the_table_region() -> None:
    # --- arrange / act ----------------
    _layout, _renderer, canvas, svg = _table_render(_LINEAR)
    texts = _texts(svg)

    # --- assert -----------------------
    contents = [t.text for t in texts]
    assert "init" in contents
    assert "second" in contents
    assert "abc1234" in contents
    assert "def5678" in contents
    # Every table cell sits at or past the table origin (right of the graph).
    cell_xs = [float(t.attrib["x"]) for t in texts if t.text in {"init", "second", "abc1234", "def5678"}]
    assert all(x >= canvas.table_x_origin for x in cell_xs)


def test_cell_text_is_inset_from_the_column_edge_by_the_padding() -> None:
    """Cell text starts a cell-padding inset past the table origin, not flush against it."""
    # --- arrange / act ----------------
    _layout, renderer, canvas, svg = _table_render(_LINEAR)
    msg_xs = [float(t.attrib["x"]) for t in _texts(svg) if t.text in {"init", "second"}]
    inset = canvas.table_x_origin + renderer.table_cell_padding_x

    # --- assert -----------------------
    # The bare row ("init") sits exactly at the inset; the tip row ("second",
    # carrying the "main" pill) is pushed further right by the pill run.
    assert msg_xs
    assert min(msg_xs) == inset
    assert all(x >= inset for x in msg_xs)


def test_table_mode_draws_no_free_floating_labels_left_of_the_table() -> None:
    """The graph-side commit labels are gone — all text is the table (≥ table origin)."""
    # --- arrange / act ----------------
    _layout, _renderer, canvas, svg = _table_render(_LINEAR)

    # --- assert -----------------------
    # No text element sits in the graph region (left of the table origin).
    assert all(float(t.attrib["x"]) >= canvas.table_x_origin for t in _texts(svg))


def test_branch_tip_pill_renders_at_the_tip_commit() -> None:
    # --- arrange / act ----------------
    _layout, _renderer, _canvas, svg = _table_render(_LINEAR)

    # --- assert -----------------------
    # The branch name appears only as its tip pill in table mode.
    assert "main" in [t.text for t in _texts(svg)]


def test_shared_tip_row_carries_multiple_pills() -> None:
    """An empty branch shares its parent's commit, so that row carries both names, same y."""
    # --- arrange / act ----------------
    _layout, _renderer, _canvas, svg = _table_render(
        build_jsonl(
            {"op": "branch", "name": "main"},
            {"op": "commit", "branch": "main", "id": "c1", "msg": "init"},
            {"op": "branch", "name": "feature", "from_branch": "main"},
        )
    )
    texts = _texts(svg)

    # --- assert -----------------------
    main_pill = next(t for t in texts if t.text == "main")
    feature_pill = next(t for t in texts if t.text == "feature")
    assert main_pill.attrib["y"] == feature_pill.attrib["y"]  # same row (c1's tip)
