"""Report the size of every shipped example at each minification level.

Walks `examples/`, renders each `.gitsvg.jsonl` four times (L0 / L1 /
L2 / L3) and prints a side-by-side size table. No files are written;
rendering is in-memory.

Run manually when curious — `python scripts/measure_minify.py` — to
inform level-vs-level trade-off discussions. No `make` target, no
test wiring, no CI gating; this is a local utility, not a regression
guard.
"""

import sys
from pathlib import Path

from gitsvg.cli._pipeline import apply_and_validate
from gitsvg.imports import resolve_imports
from gitsvg.layout import compute_layout
from gitsvg.parse import parse_jsonl_file
from gitsvg.render import compute_minify_config, minify, render

EXAMPLES_DIR = Path("examples")
LEVELS = (0, 1, 2, 3)


def _render_at_level(input_path: Path, level: int) -> str:
    """Render `input_path` at minification `level`; return SVG markup."""
    parsed_ops, report = parse_jsonl_file(input_path)
    expanded = resolve_imports(parsed_ops, file=input_path, report=report)
    state, theme = apply_and_validate(expanded, report)
    if not report.is_clean():
        for err in report.errors:
            print(f"  {err.format()}", file=sys.stderr)
        raise SystemExit(f"{input_path} did not validate cleanly")
    layout_settings, renderer_settings = theme.split()
    layout = compute_layout(state, layout_settings)
    drawing = render(layout, renderer_settings)
    config = compute_minify_config(level)
    if config.level == 0:
        return drawing.as_svg()
    svg = drawing.as_svg(header="", skip_css=True, skip_js=True)
    return minify(svg, config, renderer_settings)


def main() -> int:
    """Print a four-column sizing table for the shipped examples.

    Returns:
        Process exit code: 0 on success, 1 when `examples/` is absent
        or contains no `.gitsvg.jsonl` files.
    """
    if not EXAMPLES_DIR.exists():
        print(f"{EXAMPLES_DIR}/ not present", file=sys.stderr)
        return 1

    inputs = sorted(EXAMPLES_DIR.glob("*.gitsvg.jsonl"))
    if not inputs:
        print(f"no .gitsvg.jsonl files in {EXAMPLES_DIR}/", file=sys.stderr)
        return 1

    header = f"{'file':<32}" + "".join(f"{f'L{level}':>10}{'Δ':>8}" for level in LEVELS)
    print(header)
    print("-" * len(header))

    totals = {level: 0 for level in LEVELS}
    for input_path in inputs:
        sizes = {level: len(_render_at_level(input_path, level).encode("utf-8")) for level in LEVELS}
        baseline = sizes[0]
        row = f"{input_path.name:<32}"
        for level in LEVELS:
            delta_pct = (sizes[level] - baseline) / baseline * 100
            row += f"{sizes[level]:>10}{delta_pct:>7.1f}%"
            totals[level] += sizes[level]
        print(row)

    print("-" * len(header))
    total_row = f"{'total':<32}"
    baseline_total = totals[0]
    for level in LEVELS:
        delta_pct = (totals[level] - baseline_total) / baseline_total * 100
        total_row += f"{totals[level]:>10}{delta_pct:>7.1f}%"
    print(total_row)
    return 0


if __name__ == "__main__":
    sys.exit(main())
