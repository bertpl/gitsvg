"""Unit tests for the `drop_empty_defs_and_unused_xlink` step."""

from gitsvg.render._minify import drop_empty_defs_and_unused_xlink


def test_drop_empty_defs_removes_empty_defs_block() -> None:
    # --- arrange ----------------------
    svg = "<svg><defs>\n</defs><path/></svg>"

    # --- act --------------------------
    result = drop_empty_defs_and_unused_xlink(svg)

    # --- assert -----------------------
    assert "<defs>" not in result
    assert "</defs>" not in result


def test_drop_empty_defs_keeps_non_empty_defs_block() -> None:
    # --- arrange ----------------------
    svg = "<svg><defs><symbol id='a'/></defs><path/></svg>"

    # --- act --------------------------
    result = drop_empty_defs_and_unused_xlink(svg)

    # --- assert -----------------------
    assert "<defs>" in result
    assert "<symbol id='a'/>" in result


def test_drop_unused_xlink_when_no_xlink_references() -> None:
    # --- arrange ----------------------
    svg = '<svg xmlns="ns" xmlns:xlink="xl"><path/></svg>'

    # --- act --------------------------
    result = drop_empty_defs_and_unused_xlink(svg)

    # --- assert -----------------------
    assert 'xmlns:xlink="xl"' not in result
    assert 'xmlns="ns"' in result  # the other namespace is untouched


def test_keep_xlink_when_xlink_attributes_present() -> None:
    # --- arrange ----------------------
    svg = '<svg xmlns:xlink="xl"><use xlink:href="#a"/></svg>'

    # --- act --------------------------
    result = drop_empty_defs_and_unused_xlink(svg)

    # --- assert -----------------------
    assert 'xmlns:xlink="xl"' in result
