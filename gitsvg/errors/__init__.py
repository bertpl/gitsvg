"""Error catalog and validation-error machinery for gitsvg.

Modules:

- `_codes` — `ErrorCode` declarations and the catalog-driven registry.
  The directory `catalog/` (one markdown file per code) is the
  canonical declaration of which codes exist.
- `_validation_error` — the `ValidationError` record dataclass. Rejects
  construction with codes that are not in the catalog.
- `_report` — `ValidationReport` accumulator.
- `_catalog` — markdown loader for long-form catalog entries.

External callers should import from this package directly.
"""

from gitsvg.errors._catalog import default_catalog_dir, load_catalog_entry
from gitsvg.errors._codes import ErrorCode, all_codes, find_error_code
from gitsvg.errors._report import ValidationReport
from gitsvg.errors._validation_error import ValidationError

__all__ = [
    "ErrorCode",
    "ValidationError",
    "ValidationReport",
    "all_codes",
    "default_catalog_dir",
    "load_catalog_entry",
    "find_error_code",
]
