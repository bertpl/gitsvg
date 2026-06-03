# CLI reference

gitsvg installs a single `gitsvg` command with several sub-commands. The render
and validate commands cover the everyday loop; the `schema`, `errors`, and
`theme` introspection commands are designed for agents and tooling.

## Rendering and validation

### `gitsvg render <input> -o <output>`

Render a `.gitsvg.jsonl` file to SVG. Pass a **directory** at both ends to
recursively walk the input tree and write mirrored `.svg` outputs under the
output directory, preserving subdirectory structure.

`--small=N` selects a minification level (0–3); bare `--small` is level 2
(lossless structural compression):

| Level | Effect |
|-------|--------|
| 0 | Pristine (default) |
| 1 | Lossless basics |
| 2 | + structural compression (the default when `--small` is given with no value) |
| 3 | + font-fallback trim and tighter rounding |

```bash
gitsvg render diagram.gitsvg.jsonl -o diagram.svg
gitsvg render diagram.gitsvg.jsonl -o diagram.svg --small
gitsvg render inputs/ -o outputs/        # walk a tree
```

### `gitsvg validate <input>`

Run the full validation pipeline; report errors as `file:line: [code] field:
message`. Add `--json` for a structured report.

```bash
gitsvg validate diagram.gitsvg.jsonl
gitsvg validate diagram.gitsvg.jsonl --json
```

## Introspection

### `gitsvg state <input>`

Emit a JSON snapshot of the diagram — branches, commits with their parent
chain, and open pull requests — a structural description of the resolved graph.
Stdout by default; `-o <file>` writes to a file, or pass a directory pair to
walk recursively (one `<stem>.state.json` per input).

### `gitsvg layout <input>`

Emit a JSON view of the resolved layout — grid extent, lane assignments, commit
positions, arcs, and pull-request geometry — i.e. what the renderer consumes.
Useful for debugging visual placement. Same invocation matrix as `state`.

!!! note
    The `state` and `layout` JSON formats may change before 1.0. Pin a gitsvg
    version if you cache or depend on their schema.

### `gitsvg schema`

Index of all input operations. `gitsvg schema <op>` prints the JSON Schema for
one operation (e.g. `gitsvg schema theme` for the theme op's field schema);
`--list-ops` prints a bare op list.

### `gitsvg theme`

Index of the built-in named themes with one-line descriptions. `gitsvg theme
<name>` prints a named theme's resolved field values; `--list-names` prints a
bare name list.

### `gitsvg errors`

Index of all validation error codes. `gitsvg errors <code>` prints the
long-form catalog entry; `--list-codes` prints a bare code list.

## Designed for agents

`gitsvg schema` and `gitsvg errors` exist so an LLM-based agent producing input
can fetch the schema for a single op and the catalog entry for any error it
hits, without reading the rest of the documentation. The
[Python API](api.md) exposes the same pipeline programmatically.
