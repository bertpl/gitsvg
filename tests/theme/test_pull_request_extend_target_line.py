"""Resolution + split-routing tests for `theme.pull_request_extend_target_line`."""

from gitsvg.parse import parse_jsonl_text
from gitsvg.state import apply_ops
from gitsvg.theme import DefaultTheme
from tests._jsonl import build_jsonl


def test_default_pull_request_extend_target_line_is_false() -> None:
    # --- arrange / act ----------------
    theme = DefaultTheme.build({})

    # --- assert -----------------------
    assert theme.pull_request_extend_target_line is False


def test_explicit_pull_request_extend_target_line_overrides_default() -> None:
    # --- arrange / act ----------------
    theme = DefaultTheme.build({"pull_request_extend_target_line": True})

    # --- assert -----------------------
    assert theme.pull_request_extend_target_line is True


def test_pull_request_extend_target_line_routes_into_layout_settings() -> None:
    """`Theme.split()` carries `pull_request_extend_target_line` onto the layout slice."""
    # --- arrange ----------------------
    theme = DefaultTheme.build({"pull_request_extend_target_line": True})

    # --- act --------------------------
    layout_settings, _renderer_settings = theme.split()

    # --- assert -----------------------
    assert layout_settings.pull_request_extend_target_line is True


def test_pull_request_extend_target_line_resolves_through_apply() -> None:
    """A `theme:` op with `pull_request_extend_target_line` ends up on the resolved theme."""
    # --- arrange / act ----------------
    parsed, report = parse_jsonl_text(
        build_jsonl({"op": "theme", "pull_request_extend_target_line": True}), file="x.jsonl"
    )
    _, theme = apply_ops(parsed, report)

    # --- assert -----------------------
    assert report.is_clean()
    assert theme.pull_request_extend_target_line is True
