"""Walk `local/test_examples/` and run the full validate pipeline on every input file.

Local-only smoke test for development. The directory is gitignored, so CI
never sees this — it exists for the developer's machine, where the real
example inputs and reference SVGs live.

Skipped silently when `local/test_examples/` is absent. Exits non-zero
when any file fails to validate; a summary line names the pass/fail
counts.
"""

import sys
from pathlib import Path

from gitsvg.cli._pipeline import apply_and_validate
from gitsvg.errors import ValidationReport
from gitsvg.imports import resolve_imports
from gitsvg.parse import parse_jsonl_file

LOCAL_DIR = Path("local/test_examples")


def validate_one(path: Path) -> ValidationReport:
    """Run the full validate pipeline on `path` and return the report."""
    parsed_ops, report = parse_jsonl_file(path)
    expanded = resolve_imports(parsed_ops, file=path, report=report)
    apply_and_validate(expanded, report)
    return report


def main() -> int:
    """Walk the local example tree and validate every `.gitsvg.jsonl` file.

    Returns:
        Process exit code: 0 when every file validates cleanly (or the
        directory is absent), 1 when at least one file fails.
    """
    if not LOCAL_DIR.exists():
        print(f"{LOCAL_DIR}/ not present — skipping")
        return 0

    files = sorted(LOCAL_DIR.rglob("*.gitsvg.jsonl"))
    if not files:
        print(f"no .gitsvg.jsonl files found under {LOCAL_DIR}")
        return 0

    failures: list[tuple[Path, ValidationReport]] = []
    for file in files:
        report = validate_one(file)
        if not report.is_clean():
            failures.append((file, report))

    print(f"\n{len(files) - len(failures)}/{len(files)} files validated cleanly")
    if failures:
        print(f"\n{len(failures)} failure(s):")
        for file, report in failures:
            print(f"\n--- {file} ---")
            for err in report.errors:
                print(f"  {err.format()}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
