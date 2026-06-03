# Python API

gitsvg exposes a small, stable public API for embedding diagram rendering in
other tools — documentation plugins, generators, web apps — without shelling
out to the CLI or composing pipeline internals.

```python
import gitsvg
```

The public surface is intentionally minimal: `render_text`, the
`GitsvgValidationError` it raises, and the `ValidationReport` that error
carries.

## `render_text`

```python
gitsvg.render_text(source: str, *, id_prefix: str = "") -> str
```

Render a JSONL op-stream string to an **inline-embeddable** SVG string. Runs
the same validate-and-render pipeline as `gitsvg render`, but on an in-memory
string, returning the SVG rather than writing a file. The output omits the XML
prolog and any injected `<style>` / `<script>`, and the root `<svg>` carries
its `xmlns`, so the result inlines directly into an HTML document.

**Parameters**

- **`source`** — the op-stream as `.gitsvg.jsonl` text (one JSON op per line).
  An `import` op has no base path to resolve against and will fail validation;
  inline the imported ops instead.
- **`id_prefix`** — optional prefix for element ids in the emitted SVG, so
  multiple inline diagrams on one page can't collide. Empty (the default) keeps
  drawsvg's default prefix.

**Returns** the SVG document as a string, ready to inline into HTML.

**Raises** `GitsvgValidationError` if `source` fails to parse or validate. No
partial SVG is produced.

### Example

```python
import gitsvg

source = """\
{"op": "branch", "name": "main", "label_side": "before"}
{"op": "commit", "branch": "main", "id": "c1", "msg": "initial commit", "hash": "auto"}
{"op": "commit", "branch": "main", "id": "c2", "msg": "add README", "hash": "auto"}
"""

svg = gitsvg.render_text(source)
# -> "<svg ...>...</svg>", ready to embed in a page
```

## Error handling

```python
import gitsvg

try:
    svg = gitsvg.render_text(bad_source)
except gitsvg.GitsvgValidationError as exc:
    # exc.report is a ValidationReport carrying the individual errors,
    # each with a file/line, error code, field, and message.
    report = exc.report
    ...
```

`GitsvgValidationError` carries the full `ValidationReport` so callers can
format or surface the individual problems however they like — the same error
codes the [`gitsvg errors`](cli.md#gitsvg-errors) command documents.
