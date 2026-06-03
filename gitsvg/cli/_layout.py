"""The `gitsvg layout` CLI command.

Emits the resolved layout (slot positions, lane assignments, arcs,
guides, open pull-request geometry) as a JSON document. The intended
consumer is a human or agent debugging visual placement — "why is
this branch in lane 3", "where does the merge arc land" — without
round-tripping through the rendered SVG.

Three invocation forms, mirroring `gitsvg state` and `gitsvg render`:

- *Single-file to stdout* — `gitsvg layout INPUT.jsonl`. Writes the
  JSON to stdout.
- *Single-file to file* — `gitsvg layout INPUT.jsonl -o OUTPUT.json`.
  Writes the JSON to the given file.
- *Bulk* — `gitsvg layout INPUT_DIR -o OUTPUT_DIR`. Recursively
  walks `INPUT_DIR` for `*.gitsvg.jsonl` files, writes one
  `<stem>.layout.json` per input under `OUTPUT_DIR`, mirroring
  subdirectory structure.

Validation errors print to stderr and exit non-zero; no JSON is
emitted for a failing input. Output format may change before
gitsvg 1.0 — pin a version when caching the schema.
"""

from pathlib import Path

from gitsvg.layout import compute_layout, layout_to_json
from gitsvg.state import State
from gitsvg.theme import Theme

from ._introspect import introspection_command, run_introspection_command


def _layout_payload(state: State, theme: Theme) -> object:
    """Build the `gitsvg layout` JSON payload — the resolved layout geometry."""
    layout_settings, _ = theme.split()
    return layout_to_json(compute_layout(state, layout_settings))


@introspection_command("layout")
def layout_command(input_path: Path, output_path: Path | None) -> None:
    """Emit a JSON view of the resolved layout (grid, lanes, arcs, guides, pull-request geometry).

    With a single file at INPUT and no `-o`, writes the JSON to
    stdout. With `-o OUTPUT.json`, writes to that file. With a
    directory at INPUT and a directory at `-o`, recursively walks
    INPUT for `*.gitsvg.jsonl` files and writes one
    `<stem>.layout.json` per input under OUTPUT, preserving
    subdirectory structure.

    Runs the same validation pipeline as `gitsvg validate` per
    input, then computes the layout. Exits non-zero (writing
    nothing for that input) on any validation error.

    Output format may change before gitsvg 1.0; pin a gitsvg
    version when caching the schema.
    """
    run_introspection_command(input_path, output_path, output_ext=".layout.json", payload_fn=_layout_payload)
