"""Shared fixtures for `_errors` tests."""

from collections.abc import Iterator
from pathlib import Path

import pytest

from gitsvg._errors import _codes


@pytest.fixture
def empty_registry(monkeypatch: pytest.MonkeyPatch) -> Iterator[dict]:
    """Replace the global error-code registry with an empty dict for the test.

    The original registry is restored on teardown via `monkeypatch`,
    so individual tests can register codes without bleeding state into
    other tests.
    """
    fresh: dict = {}
    monkeypatch.setattr(_codes, "_REGISTERED_CODES", fresh)
    yield fresh


@pytest.fixture
def fixtures_catalog_dir() -> Path:
    """Return the path to `tests/fixtures/error_catalog/`."""
    return Path(__file__).parent.parent / "fixtures" / "error_catalog"
