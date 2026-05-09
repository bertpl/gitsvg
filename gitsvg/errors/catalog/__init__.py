"""Long-form error catalog — one markdown file per error code.

This sub-package is the canonical declaration of which error codes exist.
Each `<code>.md` file (e.g. `E001.md`) contributes one entry to the
registry built by `gitsvg.errors._codes._scan_catalog()` at import time.
The first H1 heading is parsed as `# <code> - <summary>`; the body is
returned by `gitsvg.errors._catalog.load_catalog_entry()` for the CLI's
`gitsvg errors <code>` command.

The registry is fully populated whenever this package loads — no
import-order dependency on which feature modules are touched first. This
also means an emit site cannot use a code that has no catalog entry:
`ValidationError.__post_init__` rejects it.

Entries are organised by validation phase:

- E0xx — parse / JSONL syntax
- E1xx — per-op schema (pydantic-level)
- E2xx — per-op semantic (state-aware)
- E3xx — imports (cycle, depth, path, ordering)
- E4xx — end-of-file cross-reference checks
"""
