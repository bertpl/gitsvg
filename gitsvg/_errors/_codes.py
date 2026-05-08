"""Catalog-driven error code registry for the gitsvg validator.

The filesystem is the source of truth. Every `<code>.md` file under
`gitsvg/_errors/catalog/` declares one error code. The registry is
populated by scanning that directory at import time:

- Filename `E001.md` → code `"E001"`.
- The first H1 heading inside the file, when of the form
  `# E001 - <summary>` (also accepts `:` or `—` as the separator),
  contributes the one-line summary shown in the `gitsvg errors` index.
  When the heading doesn't follow the convention, the entire heading
  text becomes the summary.

The numeric range encodes the validation phase the code belongs to:

- E001-E099: parse / JSONL syntax
- E100-E199: per-op shape (pydantic-level)
- E200-E299: per-op semantic (state-aware)
- E300-E399: imports (cycle, depth, path, ordering)
- E400-E499: end-of-file cross-reference checks
- E500+:     reserved for future categories

Codes may still be renumbered through 0.0.x. Strive for stability
from 0.1.0 onward.

Adding a new code is a single edit: drop a new `<code>.md` into the
catalog directory. `ValidationError.__post_init__` enforces the inverse
direction at runtime — emitting a code that has no catalog entry
raises immediately, so the catalog and the emit sites cannot drift
out of sync.
"""

import re
from dataclasses import dataclass
from importlib.resources.abc import Traversable

from gitsvg._errors._catalog import default_catalog_dir


# ==================================================================================================
#  ErrorCode dataclass
# ==================================================================================================
@dataclass(frozen=True, slots=True)
class ErrorCode:
    """A single declared error code with its short summary.

    Attributes:
        code: The textual code (e.g. `"E210"`).
        summary: One-line description shown in the `gitsvg errors` index.
    """

    code: str
    summary: str


# ==================================================================================================
#  Catalog scan
# ==================================================================================================
_CODE_FILENAME_PATTERN = re.compile(r"^(E\d{3,})\.md$")


def _extract_summary(body: str, code: str) -> str:
    """Extract the one-line summary from the first H1 heading of a catalog entry.

    The convention is `# <code> <separator> <summary>` where `<separator>` is one
    of `-`, `:`, or `—`. When the heading doesn't match that pattern, the entire
    heading text is returned. When no H1 heading appears as the first non-blank
    line, returns an empty string.

    Args:
        body: Markdown body of the catalog entry.
        code: The code expected to appear in the heading.

    Returns:
        The extracted summary, or an empty string when the convention is not
        followed.
    """
    for line in body.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("# "):
            heading = line[2:].strip()
            match = re.match(rf"^{re.escape(code)}\s*[-:—]\s*(.+)$", heading)
            return match.group(1).strip() if match else heading
        return ""
    return ""


def _scan_catalog(catalog_dir: Traversable) -> dict[str, ErrorCode]:
    """Build a registry dict by reading every `E###.md` file in `catalog_dir`.

    Files whose names don't match the `E###.md` convention are silently
    skipped (e.g. README files, `__init__.py`).

    Args:
        catalog_dir: The directory holding catalog markdown files.
            Production callers pass `default_catalog_dir()`; tests pass
            a fixture directory.

    Returns:
        A dict of `code -> ErrorCode`, sorted by code in ascending
        order.
    """
    out: dict[str, ErrorCode] = {}
    for entry in catalog_dir.iterdir():
        match = _CODE_FILENAME_PATTERN.match(entry.name)
        if not match:
            continue
        code = match.group(1)
        body = entry.read_text(encoding="utf-8")
        out[code] = ErrorCode(code=code, summary=_extract_summary(body, code))
    return dict(sorted(out.items()))


# ==================================================================================================
#  Module-level registry
# ==================================================================================================
_REGISTERED_CODES: dict[str, ErrorCode] = _scan_catalog(default_catalog_dir())


def get(code: str) -> ErrorCode | None:
    """Return the registered `ErrorCode` for `code`, or None if unknown."""
    return _REGISTERED_CODES.get(code)


def all_codes() -> list[ErrorCode]:
    """Return all registered codes in ascending code order."""
    return list(_REGISTERED_CODES.values())
