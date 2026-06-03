"""The `gitsvg state` CLI command.

Emits a JSON snapshot of the diagram — branches, commits with their
parent chain, and open pull requests — as a structural description
of the resolved graph. The intended consumer is an LLM agent that
authored a `.gitsvg.jsonl` file and needs to read back the resolved
structure — auto-generated commit ids, resolved hashes (the
`"auto"` sentinel turned concrete), current branch heads, and the
parent chain — without re-parsing its own input or round-tripping
through the rendered SVG.

Three invocation forms, mirroring `gitsvg render`:

- *Single-file to stdout* — `gitsvg state INPUT.jsonl`. Writes the
  JSON to stdout.
- *Single-file to file* — `gitsvg state INPUT.jsonl -o OUTPUT.json`.
  Writes the JSON to the given file.
- *Bulk* — `gitsvg state INPUT_DIR -o OUTPUT_DIR`. Recursively
  walks `INPUT_DIR` for `*.gitsvg.jsonl` files, writes one
  `<stem>.state.json` per input under `OUTPUT_DIR`, mirroring
  subdirectory structure.

Validation errors print to stderr and exit non-zero; no JSON is
emitted for a failing input. Output format may change before
gitsvg 1.0 — pin a version when caching the schema.
"""

from pathlib import Path

from gitsvg.state import State, state_to_json
from gitsvg.theme import Theme

from ._introspect import introspection_command, run_introspection_command


def _state_payload(state: State, _theme: Theme) -> object:
    """Build the `gitsvg state` JSON payload — the resolved diagram snapshot."""
    return state_to_json(state)


@introspection_command("state")
def state_command(input_path: Path, output_path: Path | None) -> None:
    """Emit a JSON snapshot of the diagram (branches, commits, open pull requests, ids, parents).

    With a single file at INPUT and no `-o`, writes the JSON to
    stdout. With `-o OUTPUT.json`, writes to that file. With a
    directory at INPUT and a directory at `-o`, recursively walks
    INPUT for `*.gitsvg.jsonl` files and writes one
    `<stem>.state.json` per input under OUTPUT, preserving
    subdirectory structure.

    Runs the same validation pipeline as `gitsvg validate` per
    input. Exits non-zero (writing nothing for that input) on any
    validation error.

    Output format may change before gitsvg 1.0; pin a gitsvg
    version when caching the schema.
    """
    run_introspection_command(input_path, output_path, output_ext=".state.json", payload_fn=_state_payload)
