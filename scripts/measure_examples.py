"""Report the size of every shipped example, with and without `--small`.

Walks `examples/`, renders each `.gitsvg.jsonl` twice — once with the
default pipeline, once with `--small` — and prints a side-by-side size
table. No files are written; rendering is in-memory.

Used to baseline the round-1 reductions and (later) compare against
round-2 numbers when those land. The committed `examples/*.svg` files
are unchanged.
"""

import sys
from pathlib import Path

from gitsvg.imports import resolve_imports
from gitsvg.layout import compute_layout
from gitsvg.parse import parse_jsonl_file
from gitsvg.render import render
from gitsvg.render._minify import minify
from gitsvg.state import apply_ops, check_end_of_file

EXAMPLES_DIR = Path("examples")


def render_default(input_path: Path) -> str:
    """Render `input_path` with the default pipeline; return SVG markup."""
    drawing = _build_drawing(input_path)
    return drawing.as_svg()


def render_small(input_path: Path) -> str:
    """Render `input_path` under `--small`; return SVG markup."""
    drawing = _build_drawing(input_path)
    svg = drawing.as_svg(header="", skip_css=True, skip_js=True)
    return minify(svg, small=True)


def _build_drawing(input_path: Path):
    """Run the validate + layout + render pipeline; return the drawsvg.Drawing."""
    parsed_ops, report = parse_jsonl_file(input_path)
    expanded = resolve_imports(parsed_ops, file=input_path, report=report)
    state = apply_ops(expanded, report)
    check_end_of_file(state, report)
    if not report.is_clean():
        for err in report.errors:
            print(f"  {err.format()}", file=sys.stderr)
        raise SystemExit(f"{input_path} did not validate cleanly")
    layout = compute_layout(state)
    return render(layout)


def main() -> int:
    """Print a sizing table for the shipped examples.

    Returns:
        Process exit code: 0 on success, 1 when `examples/` is absent.
    """
    if not EXAMPLES_DIR.exists():
        print(f"{EXAMPLES_DIR}/ not present", file=sys.stderr)
        return 1

    inputs = sorted(EXAMPLES_DIR.glob("*.gitsvg.jsonl"))
    if not inputs:
        print(f"no .gitsvg.jsonl files in {EXAMPLES_DIR}/", file=sys.stderr)
        return 1

    print(f"{'file':<32} {'default':>10} {'--small':>10} {'reduction':>12}")
    print("-" * 68)
    total_default = 0
    total_small = 0
    for input_path in inputs:
        default_bytes = len(render_default(input_path).encode("utf-8"))
        small_bytes = len(render_small(input_path).encode("utf-8"))
        reduction = (default_bytes - small_bytes) / default_bytes * 100
        total_default += default_bytes
        total_small += small_bytes
        print(f"{input_path.name:<32} {default_bytes:>10} {small_bytes:>10} {reduction:>11.1f}%")
    print("-" * 68)
    total_reduction = (total_default - total_small) / total_default * 100
    print(f"{'total':<32} {total_default:>10} {total_small:>10} {total_reduction:>11.1f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
