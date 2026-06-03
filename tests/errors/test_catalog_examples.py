"""Guard test: every catalog `## Example` must still trigger its own error code.

Each `gitsvg/errors/catalog/<code>.md` carries an `## Example` block — an input
crafted to raise `<code>`. This test feeds that block through the full in-memory
validate pipeline and asserts `<code>` shows up in the report, so an example
can't silently rot when the input format changes (e.g. a renamed op or a removed
field would make the example raise a *different* code, or none).

It guards example-block drift, not prose drift in the Cause / How-to-fix text.

Exempted: the import-resolution family (E300–E304), whose examples need on-disk
file structure (a cycle is two files, a missing import needs an absent path);
those are covered by the fixture-based tests under `tests/imports/`.
"""

from pathlib import Path

import pytest

from gitsvg._pipeline import apply_and_validate
from gitsvg.errors import all_codes, load_catalog_entry
from gitsvg.imports import resolve_imports
from gitsvg.parse import parse_jsonl_text

_IMPORT_FAMILY = frozenset({"E300", "E301", "E302", "E303", "E304"})
_RUNNABLE_CODES = sorted(c.code for c in all_codes() if c.code not in _IMPORT_FAMILY)


def _first_example_block(markdown: str) -> str:
    """Return the text inside the first fenced block under `## Example`."""
    lines = markdown.splitlines()
    start = next(i for i, line in enumerate(lines) if line.strip() == "## Example")
    fence = next(i for i in range(start + 1, len(lines)) if lines[i].lstrip().startswith("```"))
    body: list[str] = []
    for line in lines[fence + 1 :]:
        if line.lstrip().startswith("```"):
            break
        body.append(line)
    return "\n".join(body)


@pytest.mark.parametrize("code", _RUNNABLE_CODES)
def test_catalog_example_triggers_its_code(code: str) -> None:
    """The `## Example` for `code` must produce `code` when run through the pipeline."""
    # --- arrange ----------------------
    entry = load_catalog_entry(code)
    assert entry is not None, f"no catalog entry for {code}"
    example = _first_example_block(entry)

    # --- act --------------------------
    parsed, report = parse_jsonl_text(example, file="<example>")
    expanded = resolve_imports(parsed, file=Path("<example>"), report=report)
    apply_and_validate(expanded, report)

    # --- assert -----------------------
    raised = {error.code for error in report.errors}
    assert code in raised, f"{code}.md example raised {sorted(raised) or 'nothing'}, not {code}"
