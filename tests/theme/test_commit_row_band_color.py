"""Resolution / split / schema / apply tests for `theme.commit_row_band_color`."""

from gitsvg.parse import parse_jsonl_text
from gitsvg.state import apply_ops
from gitsvg.theme import DefaultTheme
from tests._jsonl import build_jsonl


def test_default_commit_row_band_color_is_none() -> None:
    # --- arrange / act ----------------
    theme = DefaultTheme.build({})

    # --- assert -----------------------
    assert theme.commit_row_band_color is None


def test_explicit_commit_row_band_color_overrides_default() -> None:
    # --- arrange / act ----------------
    theme = DefaultTheme.build({"commit_row_band_color": "#00000022"})

    # --- assert -----------------------
    assert theme.commit_row_band_color == "#00000022"


def test_commit_row_band_color_rides_the_renderer_slice() -> None:
    """`commit_row_band_color` is a render-side field — it lands on the renderer slice."""
    # --- arrange ----------------------
    theme = DefaultTheme.build({"commit_row_band_color": "#0000ff80"})

    # --- act --------------------------
    _layout_settings, renderer_settings = theme.split()

    # --- assert -----------------------
    assert renderer_settings.commit_row_band_color == "#0000ff80"


def test_commit_row_band_color_resolves_through_apply() -> None:
    """A `theme:` op with `commit_row_band_color` ends up on the resolved theme."""
    # --- arrange / act ----------------
    parsed, report = parse_jsonl_text(
        build_jsonl({"op": "theme", "commit_row_band_color": "#11223344"}), file="x.jsonl"
    )
    _, theme = apply_ops(parsed, report)

    # --- assert -----------------------
    assert report.is_clean()
    assert theme.commit_row_band_color == "#11223344"


def test_commit_row_band_color_accepts_alpha_hex_forms() -> None:
    """4- and 8-digit (alpha) hex forms validate cleanly on the `theme:` op."""
    # --- arrange / act ----------------
    parsed, report = parse_jsonl_text(
        build_jsonl(
            {"op": "theme", "commit_row_band_color": "#1234"}, {"op": "theme", "commit_row_band_color": "#11223344"}
        ),
        file="x.jsonl",
    )
    apply_ops(parsed, report)

    # --- assert -----------------------
    assert report.is_clean()


def test_commit_row_band_color_rejects_malformed_hex() -> None:
    """A 5-digit hex (neither alpha nor plain form) is rejected at schema level."""
    # --- arrange / act ----------------
    parsed, report = parse_jsonl_text(build_jsonl({"op": "theme", "commit_row_band_color": "#12345"}), file="x.jsonl")
    apply_ops(parsed, report)

    # --- assert -----------------------
    assert not report.is_clean()
