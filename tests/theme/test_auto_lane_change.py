"""Resolution + split-routing tests for `theme.auto_lane_change`."""

from gitsvg.parse import parse_jsonl_text
from gitsvg.state import apply_ops
from gitsvg.theme import DefaultTheme
from tests._jsonl import build_jsonl


def test_default_auto_lane_change_is_false() -> None:
    # --- arrange / act ----------------
    theme = DefaultTheme.build({})

    # --- assert -----------------------
    assert theme.auto_lane_change is False


def test_explicit_auto_lane_change_overrides_default() -> None:
    # --- arrange / act ----------------
    theme = DefaultTheme.build({"auto_lane_change": True})

    # --- assert -----------------------
    assert theme.auto_lane_change is True


def test_auto_lane_change_routes_into_layout_settings() -> None:
    """`Theme.split()` carries `auto_lane_change` onto the layout slice."""
    # --- arrange ----------------------
    theme = DefaultTheme.build({"auto_lane_change": True})

    # --- act --------------------------
    layout_settings, _renderer_settings = theme.split()

    # --- assert -----------------------
    assert layout_settings.auto_lane_change is True


def test_auto_lane_change_resolves_through_apply() -> None:
    """A `theme:` op with `auto_lane_change` ends up on the resolved theme."""
    # --- arrange / act ----------------
    parsed, report = parse_jsonl_text(build_jsonl({"op": "theme", "auto_lane_change": True}), file="x.jsonl")
    _, theme = apply_ops(parsed, report)

    # --- assert -----------------------
    assert report.is_clean()
    assert theme.auto_lane_change is True
