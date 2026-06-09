"""Compute release metrics from the CI coverage + node-id artifacts.

Run by the coverage-combine job after ``coverage combine``, with every matrix
combo's data present in the working directory. Reads the combined coverage
total and the per-combo collected-node-id dumps (``test-ids-*.txt``), logs the
per-combo counts, and writes a metrics JSON (path from ``argv[1]``) with the
cumulative numbers the release stamps into the README badges: ``coverage_pct``,
``test_union`` (distinct node-ids across all combos), and ``test_max`` (the
largest single-combo count).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _coverage_total() -> float:
    """Return the combined coverage percentage from the current ``.coverage``."""
    out = subprocess.run(
        ["coverage", "report", "--format=total"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return float(out.strip())


def _distinct_nodeids(path: Path) -> set[str]:
    """Return the distinct test node-ids recorded in a per-combo dump file."""
    return {line.strip() for line in path.read_text().splitlines() if "::" in line}


def main() -> None:
    """Compute cumulative metrics and write them to the JSON path in ``argv[1]``."""
    out_path = Path(sys.argv[1])
    id_files = sorted(Path().glob("test-ids-*.txt"))
    if not id_files:
        sys.exit("no test-ids-*.txt files found to union")

    per_combo = {f.name: _distinct_nodeids(f) for f in id_files}
    union: set[str] = set().union(*per_combo.values())
    for name, ids in per_combo.items():
        print(f"  {name}: {len(ids)}")
    test_max = max(len(ids) for ids in per_combo.values())
    print(f"  union: {len(union)}  (max single combo: {test_max})")

    metrics = {
        "coverage_pct": _coverage_total(),
        "test_union": len(union),
        "test_max": test_max,
    }
    out_path.write_text(json.dumps(metrics, indent=2) + "\n")


if __name__ == "__main__":
    main()
