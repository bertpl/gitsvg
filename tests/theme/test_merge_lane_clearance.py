"""Resolution + split-routing tests for `theme.merge_lane_clearance`."""

from gitsvg.parse import parse_jsonl_text
from gitsvg.state import apply_ops
from gitsvg.theme import DefaultTheme
from tests._jsonl import build_jsonl


def test_default_merge_lane_clearance_is_one() -> None:
    # --- arrange / act ----------------
    theme = DefaultTheme.build({})

    # --- assert -----------------------
    assert theme.merge_lane_clearance == 1


def test_explicit_merge_lane_clearance_overrides_default() -> None:
    # --- arrange / act ----------------
    theme = DefaultTheme.build({"merge_lane_clearance": 3})

    # --- assert -----------------------
    assert theme.merge_lane_clearance == 3


def test_merge_lane_clearance_routes_into_layout_settings() -> None:
    """`Theme.split()` carries `merge_lane_clearance` onto the layout slice."""
    # --- arrange ----------------------
    theme = DefaultTheme.build({"merge_lane_clearance": 2})

    # --- act --------------------------
    layout_settings, _renderer_settings = theme.split()

    # --- assert -----------------------
    assert layout_settings.merge_lane_clearance == 2


def test_merge_lane_clearance_resolves_through_apply() -> None:
    """A `theme:` op with `merge_lane_clearance` ends up on the resolved theme."""
    # --- arrange / act ----------------
    parsed, report = parse_jsonl_text(
        build_jsonl({"op": "theme", "auto_lane_change": True, "merge_lane_clearance": 2}), file="x.jsonl"
    )
    _, theme = apply_ops(parsed, report)

    # --- assert -----------------------
    assert report.is_clean()
    assert theme.merge_lane_clearance == 2


def test_negative_merge_lane_clearance_rejected_at_schema() -> None:
    """A negative value is a schema-constraint violation (E103) with a line number."""
    # --- arrange / act ----------------
    _parsed, report = parse_jsonl_text(build_jsonl({"op": "theme", "merge_lane_clearance": -1}), file="x.jsonl")

    # --- assert -----------------------
    assert not report.is_clean()
    assert "E103" in [e.code for e in report.errors]
