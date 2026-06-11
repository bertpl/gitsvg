"""mkdocs-gen-files script — expose the example SVGs to the docs build.

The docs pages embed the committed example renders, but MkDocs only
serves files under `docs/`. This script copies every `examples/*.svg`
into the generated site (under `assets/examples/`) at build time, so
the pages reference site-local paths and each docs build is
self-contained for its own ref — no floating raw-URL embeds.
"""

from pathlib import Path

import mkdocs_gen_files

EXAMPLES_DIR = Path(__file__).parent.parent / "examples"

for svg in sorted(EXAMPLES_DIR.glob("*.svg")):
    with mkdocs_gen_files.open(f"assets/examples/{svg.name}", "wb") as f:
        f.write(svg.read_bytes())
