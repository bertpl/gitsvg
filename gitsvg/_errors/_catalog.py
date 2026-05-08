"""Catalog loader — reads the long-form markdown explanation for an error code.

Each registered code may have an accompanying `<code>.md` file under
`gitsvg/_errors/catalog/` with sections like *Cause*, *Example*,
*How to fix*, *Related codes*, *Spec reference*. The CLI's
`gitsvg errors <code>` command surfaces this file's contents.

Codes without a markdown entry yet are still queryable — the loader
returns `None` and the CLI falls back to the registry's one-line
summary.
"""

from importlib.resources import files
from importlib.resources.abc import Traversable


def default_catalog_dir() -> Traversable:
    """Return the production catalog directory inside the installed package."""
    return files("gitsvg._errors.catalog")


def load_catalog_entry(code: str, *, catalog_dir: Traversable | None = None) -> str | None:
    """Load the markdown body of the catalog entry for `code`.

    Args:
        code: The error code (e.g. `"E210"`).
        catalog_dir: Override the catalog directory. When None, reads
            from the production catalog under `gitsvg._errors.catalog`.
            Tests pass a fixture directory.

    Returns:
        The full markdown contents of the entry file, or `None` if the
        catalog has no entry for that code yet.
    """
    if catalog_dir is None:
        catalog_dir = default_catalog_dir()
    entry = catalog_dir / f"{code}.md"
    return entry.read_text(encoding="utf-8") if entry.is_file() else None
