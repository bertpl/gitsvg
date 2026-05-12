"""Walk `local/test_examples/` and render every input file to a sibling SVG.

Local-only smoke output for development. The directory is gitignored,
so CI never sees this — it exists for the developer's machine, where
the real example inputs and reference SVGs live.

For each `<story>/inputs/<frame>.gitsvg.jsonl`, writes the SVG to
`<story>/_render_outputs/<frame>.svg`. Skipped silently when
`local/test_examples/` is absent. Exits non-zero when any file fails
to validate or render; a summary line names the pass/fail counts.
"""

import sys
from pathlib import Path

from gitsvg.errors import ValidationReport
from gitsvg.imports import resolve_imports
from gitsvg.layout import compute_layout
from gitsvg.parse import parse_jsonl_file
from gitsvg.render import render
from gitsvg.render._theme import build_theme
from gitsvg.state import apply_ops, check_end_of_file

LOCAL_DIR = Path("local/test_examples")
OUTPUT_DIR_NAME = "_render_outputs"


def render_one(input_path: Path, output_path: Path) -> ValidationReport:
    """Run validate + layout + render for `input_path`, writing to `output_path`.

    Args:
        input_path: A `.gitsvg.jsonl` file under `local/test_examples/`.
        output_path: Where to write the resulting SVG.

    Returns:
        The validation report. Cleans means the file rendered.
    """
    parsed_ops, report = parse_jsonl_file(input_path)
    expanded = resolve_imports(parsed_ops, file=input_path, report=report)
    state = apply_ops(expanded, report)
    check_end_of_file(state, report)
    if not report.is_clean():
        return report
    theme = build_theme(state)
    layout = compute_layout(state)
    drawing = render(layout, theme)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    drawing.save_svg(str(output_path))
    return report


def main() -> int:
    """Walk the local example tree and render every `.gitsvg.jsonl` file.

    Returns:
        Process exit code: 0 when every file renders cleanly (or the
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
        # File path: local/test_examples/<story>/inputs/<frame>.gitsvg.jsonl
        # Output path: local/test_examples/<story>/_render_outputs/<frame>.svg
        story_dir = file.parent.parent
        frame_name = file.name.removesuffix(".gitsvg.jsonl") + ".svg"
        output_path = story_dir / OUTPUT_DIR_NAME / frame_name
        report = render_one(file, output_path)
        if not report.is_clean():
            failures.append((file, report))

    print(f"\n{len(files) - len(failures)}/{len(files)} files rendered cleanly")
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
