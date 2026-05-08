"""Project-wide pytest fixtures.

Shared fixtures — accessible from any test file under `tests/`.
"""

from collections.abc import Iterator
from pathlib import Path

import pytest

from gitsvg.errors import _codes


@pytest.fixture
def fixtures_catalog_dir() -> Path:
    """Return the path to `tests/fixtures/error_catalog/`."""
    return Path(__file__).parent / "fixtures" / "error_catalog"


@pytest.fixture
def populated_registry(
    monkeypatch: pytest.MonkeyPatch,
    fixtures_catalog_dir: Path,
) -> Iterator[dict[str, _codes.ErrorCode]]:
    """Replace the global registry with one built from the fixture catalog.

    The fixture catalog at `tests/fixtures/error_catalog/` ships with
    `E999.md` and `E998.md`. Tests that need to construct
    `ValidationError` records or test the CLI's populated path use this
    fixture.
    """
    registry = _codes._scan_catalog(fixtures_catalog_dir)
    monkeypatch.setattr(_codes, "_REGISTERED_CODES", registry)
    yield registry


@pytest.fixture
def empty_registry(monkeypatch: pytest.MonkeyPatch) -> Iterator[dict[str, _codes.ErrorCode]]:
    """Replace the global registry with an empty dict.

    Use when a test explicitly needs to verify behaviour under an empty
    catalog (e.g. CLI placeholder text).
    """
    fresh: dict[str, _codes.ErrorCode] = {}
    monkeypatch.setattr(_codes, "_REGISTERED_CODES", fresh)
    yield fresh
