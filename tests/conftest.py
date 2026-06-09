"""Project-wide pytest fixtures.

Shared fixtures — accessible from any test file under `tests/`.
"""

import os
from collections.abc import Iterator
from pathlib import Path

import pytest

from gitsvg.errors import _codes


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Dump collected node-ids to ``$GITSVG_NODEID_DUMP`` when set.

    CI sets this per matrix combo so the coverage job can union the node-ids
    across combos into the cumulative test count. A no-op on normal runs.
    """
    dump_path = os.environ.get("GITSVG_NODEID_DUMP")
    if dump_path:
        Path(dump_path).write_text("\n".join(item.nodeid for item in items) + "\n")


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
    return registry


@pytest.fixture
def empty_registry(monkeypatch: pytest.MonkeyPatch) -> Iterator[dict[str, _codes.ErrorCode]]:
    """Replace the global registry with an empty dict.

    Use when a test explicitly needs to verify behavior under an empty
    catalog (e.g. CLI placeholder text).
    """
    fresh: dict[str, _codes.ErrorCode] = {}
    monkeypatch.setattr(_codes, "_REGISTERED_CODES", fresh)
    return fresh
