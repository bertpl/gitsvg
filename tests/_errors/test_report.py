"""Tests for `ValidationReport`."""

from gitsvg._errors import ValidationError, ValidationReport


def _make_error(line: int = 1, code: str = "E999") -> ValidationError:
    """Construct a minimal `ValidationError` for use in tests."""
    return ValidationError(file="x.jsonl", line=line, code=code, message="msg")


def test_new_report_is_clean_and_empty() -> None:
    # --- act --------------------------
    report = ValidationReport()

    # --- assert -----------------------
    assert report.is_clean()
    assert len(report) == 0
    assert report.errors == []


def test_add_appends_in_insertion_order(populated_registry: dict) -> None:
    # --- arrange ----------------------
    report = ValidationReport()
    e1 = _make_error(line=1, code="E999")
    e2 = _make_error(line=5, code="E998")

    # --- act --------------------------
    report.add(e1)
    report.add(e2)

    # --- assert -----------------------
    assert report.is_clean() is False
    assert len(report) == 2
    assert report.errors == [e1, e2]


def test_errors_returns_defensive_copy(populated_registry: dict) -> None:
    # --- arrange ----------------------
    report = ValidationReport()
    report.add(_make_error())

    # --- act --------------------------
    errors_view = report.errors
    errors_view.clear()

    # --- assert -----------------------
    assert len(report) == 1
