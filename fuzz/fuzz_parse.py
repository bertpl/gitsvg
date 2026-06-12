#!/usr/bin/env python3
"""atheris fuzz target for gitsvg's untrusted-input boundary.

Drives the public `render_text` entry point, which composes the entire
validate-and-render pipeline (parse -> imports -> state -> layout ->
render) on an in-memory string. That string is the only untrusted
input gitsvg accepts, so it is the right surface to fuzz.

Contract under test:

* `render_text` either returns an SVG string, or raises
  `GitsvgValidationError` for input it rejects. Any other exception
  (a traceback escaping the validator) is a finding.
* On the success path the returned SVG must be well-formed XML. This
  strengthens "did not crash" into "did not crash *and* emitted valid
  output", catching a malformed-output class the bare contract misses
  (SVGs embed into READMEs and docs, so output well-formedness matters).

In-memory input has no directory to resolve imports against, so
`render_text` runs import resolution with `allow_imports=False`: any
`import` op is rejected with `E306` and no filesystem access happens.
The fuzzer therefore never touches disk through this path.

Run a bounded session locally (requires Linux + the `fuzz` group;
atheris ships Linux-only wheels):

    uv run --group fuzz python fuzz/fuzz_parse.py -atheris_runs=100000

CI runs the same bounded command on every PR to main and weekly; see
`.github/workflows/fuzz.yml`.
"""

import sys
from xml.etree import ElementTree

import atheris

# Instrument gitsvg's modules as they import so libFuzzer gets coverage
# feedback over the real pipeline, not just this thin harness.
with atheris.instrument_imports():
    from gitsvg import GitsvgValidationError, render_text


def test_one_input(data: bytes) -> None:
    """Feed one fuzzer-chosen byte string through `render_text`."""
    fdp = atheris.FuzzedDataProvider(data)
    source = fdp.ConsumeUnicodeNoSurrogates(fdp.remaining_bytes())
    try:
        svg = render_text(source)
    except GitsvgValidationError:
        # Expected: malformed input is rejected cleanly, not with a traceback.
        return
    # Success path: the emitted SVG must parse as well-formed XML. A
    # ParseError here propagates and is reported as a crash — a real finding.
    ElementTree.fromstring(svg)


def main() -> None:
    """Set up atheris and start fuzzing."""
    atheris.Setup(sys.argv, test_one_input)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
