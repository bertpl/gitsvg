"""Long-form error catalog — one markdown file per error code.

This sub-package is treated as a data directory rather than a code
module. Markdown files (`E001.md`, `E210.md`, ...) are loaded by
`gitsvg._errors._catalog.load_catalog_entry()` via `importlib.resources`.

PR2 ships an empty catalog; entries land alongside the code that emits
them, starting in PR3.
"""
