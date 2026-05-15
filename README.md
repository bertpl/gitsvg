# gitsvg

CLI that renders git tree visualizations as SVG from JSONL input.

[![CI](https://img.shields.io/github/actions/workflow/status/bertpl/gitsvg/push_to_main.yml?branch=main&label=CI)](https://github.com/bertpl/gitsvg/actions/workflows/push_to_main.yml)
[![PyPI](https://img.shields.io/pypi/v/gitsvg.svg)](https://pypi.org/project/gitsvg/)
[![Python](https://img.shields.io/pypi/pyversions/gitsvg.svg)](https://pypi.org/project/gitsvg/)
[![License](https://img.shields.io/badge/license-MIT-blue)](https://github.com/bertpl/gitsvg/blob/main/LICENSE)

## Installation

```bash
pip install gitsvg
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv tool install gitsvg
```

## Quick start

A `.gitsvg.jsonl` file is a list of operations, one JSON object per line, applied top-to-bottom to build a diagram. Render it with:

```bash
gitsvg render diagram.gitsvg.jsonl -o diagram.svg
```

Validate without rendering:

```bash
gitsvg validate diagram.gitsvg.jsonl
```

## Examples

The [`examples/`](examples/) folder ships eight self-contained input files demonstrating the format. Each subsection below shows the rendered output and the source it came from.

### Example 1: Linear history

A single branch with a few commits. The minimum viable diagram.

![Linear history](https://raw.githubusercontent.com/bertpl/gitsvg/main/examples/01_linear.svg)

```jsonl
{"op": "branch", "name": "main", "label_side": "before"}
{"op": "commit", "branch": "main", "id": "c1", "msg": "initial commit", "hash": "auto"}
{"op": "commit", "branch": "main", "id": "c2", "msg": "add README", "hash": "auto"}
{"op": "commit", "branch": "main", "id": "c3", "msg": "add tests", "hash": "auto"}
{"op": "commit", "branch": "main", "id": "c4", "msg": "fix typo", "hash": "auto"}
```

### Example 2: Branch and merge

A `feature` branch forks off `main`, accumulates a couple of commits, then merges back.

![Branch and merge](https://raw.githubusercontent.com/bertpl/gitsvg/main/examples/02_branch_merge.svg)

```jsonl
{"op": "branch", "name": "main", "label_side": "before"}
{"op": "commit", "branch": "main", "id": "c1", "msg": "initial commit", "hash": "auto"}
{"op": "commit", "branch": "main", "id": "c2", "msg": "setup config", "hash": "auto"}
{"op": "branch", "name": "feature", "from_branch": "main"}
{"op": "commit", "branch": "feature", "id": "f1", "msg": "add login form", "hash": "auto"}
{"op": "commit", "branch": "feature", "id": "f2", "msg": "wire up auth", "hash": "auto"}
{"op": "merge", "from": "feature", "into": "main", "as": "m1", "msg": "merge feature", "hash": "auto"}
```

### Example 3: Multiple branches with lane reuse

Two concurrent branches share lanes 1 and 2; after both merge, a later `feature-b` reclaims the now-free lane 1 instead of starting a new one. Lane assignment is automatic and geometry-driven.

![Multiple branches with lane reuse](https://raw.githubusercontent.com/bertpl/gitsvg/main/examples/03_multi_branch.svg)

```jsonl
{"op": "branch", "name": "main", "label_side": "before"}
{"op": "commit", "branch": "main", "id": "c1", "msg": "initial commit", "hash": "auto"}
{"op": "branch", "name": "feature-a", "from_branch": "main"}
{"op": "commit", "branch": "feature-a", "id": "a1", "msg": "start feature A", "hash": "auto"}
{"op": "branch", "name": "bugfix", "from_branch": "main"}
{"op": "commit", "branch": "bugfix", "id": "x1", "msg": "fix #42", "hash": "auto"}
{"op": "merge", "from": "feature-a", "into": "main", "as": "m1", "msg": "merge feature A", "hash": "auto"}
{"op": "merge", "from": "bugfix", "into": "main", "as": "m2", "msg": "merge bugfix", "hash": "auto"}
{"op": "commit", "branch": "main", "id": "c2", "msg": "release prep", "hash": "auto"}
{"op": "branch", "name": "feature-b", "from_branch": "main"}
{"op": "commit", "branch": "feature-b", "id": "b1", "msg": "feature B", "hash": "auto"}
{"op": "merge", "from": "feature-b", "into": "main", "as": "m3", "msg": "merge feature B", "hash": "auto"}
```

### Example 4: Highlighting a commit

The `highlight` op marks an existing commit with an enlarged dot and a bold label — useful for drawing attention to a release or a key milestone.

![Highlighted release commit](https://raw.githubusercontent.com/bertpl/gitsvg/main/examples/04_highlight.svg)

```jsonl
{"op": "branch", "name": "main", "label_side": "before"}
{"op": "commit", "branch": "main", "id": "c1", "msg": "initial commit", "hash": "auto"}
{"op": "commit", "branch": "main", "id": "c2", "msg": "feature work", "hash": "auto"}
{"op": "commit", "branch": "main", "id": "c3", "msg": "more feature work", "hash": "auto"}
{"op": "commit", "branch": "main", "id": "v1", "msg": "release v1.0", "hash": "auto"}
{"op": "commit", "branch": "main", "id": "c4", "msg": "post-release fix", "hash": "auto"}
{"op": "highlight", "commit": "v1"}
```

### Example 5: Remove and rebuild (rebase pattern)

A `feature` branch is removed and re-declared on top of a more recent `main` commit, with the same commit IDs as before. This is the rebase-style "move my work onto the new tip" pattern, expressed as primitives.

![Remove and rebuild](https://raw.githubusercontent.com/bertpl/gitsvg/main/examples/05_remove_rebuild.svg)

```jsonl
{"op": "branch", "name": "main", "label_side": "before"}
{"op": "commit", "branch": "main", "id": "c1", "msg": "initial commit", "hash": "auto"}
{"op": "branch", "name": "feature", "from_branch": "main"}
{"op": "commit", "branch": "feature", "id": "f1", "msg": "WIP feature", "hash": "auto"}
{"op": "commit", "branch": "feature", "id": "f2", "msg": "more WIP", "hash": "auto"}
{"op": "commit", "branch": "main", "id": "c2", "msg": "main moves on", "hash": "auto"}
{"op": "commit", "branch": "main", "id": "c3", "msg": "more main work", "hash": "auto"}
{"op": "remove", "branches": ["feature"]}
{"op": "branch", "name": "feature", "from_branch": "main"}
{"op": "commit", "branch": "feature", "id": "f1", "msg": "WIP feature", "hash": "auto"}
{"op": "commit", "branch": "feature", "id": "f2", "msg": "more WIP", "hash": "auto"}
```

### Example 6: Import and squash

The `import` op replays another file as a prelude — here it picks up the rebased state from Example 5. A single new commit then squashes `f1` and `f2` into one via `replaces:`.

![Import and squash](https://raw.githubusercontent.com/bertpl/gitsvg/main/examples/06_import_squash.svg)

```jsonl
{"op": "import", "path": "05_remove_rebuild.gitsvg.jsonl"}
{"op": "commit", "branch": "feature", "replaces": ["f1", "f2"], "id": "f_squash", "msg": "complete feature", "hash": "auto"}
```

### Example 7: Open pull request

The `pull_request` op declares a pending merge between two branches. Both endpoints live-track the current branch tips: as commits accumulate on either side, the dashed arc advances. The optional `title` renders as a pill anchored at the source-tip commit. The typical lifecycle closes the PR with `remove` and then runs a real `merge`; this example stops before either, so the open PR remains visible in the final state.

![Open pull request](https://raw.githubusercontent.com/bertpl/gitsvg/main/examples/07_pull_request.svg)

```jsonl
{"op": "branch", "name": "main", "label_side": "before"}
{"op": "commit", "branch": "main", "id": "m1", "msg": "release"}
{"op": "branch", "name": "feature", "from_branch": "main"}
{"op": "commit", "branch": "feature", "id": "f1", "msg": "wip"}
{"op": "pull_request", "id": "pr1", "from": "feature", "into": "main", "title": "PR 1: add thing"}
{"op": "commit", "branch": "feature", "id": "f2", "msg": "polish"}
{"op": "commit", "branch": "main", "id": "m2", "msg": "hotfix"}
```

### Example 8: Themed rendering

The `theme` op patches the diagram's live theme — spacings, sizes, fonts, the branch-colour palette, the SVG background, and more. Each op only overrides the fields it lists; a `name` selects a built-in theme (today: `default`) that replaces every field first. Here we import Example 3 unchanged and apply a saturated palette with thicker strokes, larger labels, and a warm background.

![Themed rendering](https://raw.githubusercontent.com/bertpl/gitsvg/main/examples/08_themed.svg)

```jsonl
{"op": "import", "path": "03_multi_branch.gitsvg.jsonl"}
{"op": "theme", "background_color": "#fff8e7", "branch_line_width": 4, "label_font_size": 14, "branch_label_font_size": 14, "hash_font_size": 11, "commit_radius": 7, "highlight_radius": 9, "colors": {"main": "#d62728", "branch1": "#1f77b4", "branch2": "#2ca02c", "branch3": "#ff7f0e", "branch4": "#9467bd"}}
```

## CLI reference

| Command | Purpose |
|---------|---------|
| `gitsvg render <input> -o <output>` | Render a `.gitsvg.jsonl` file to SVG. Add `--small` for a more compact SVG (some loss of numeric precision). |
| `gitsvg validate <input>` | Run the full validation pipeline; report errors with `file:line: [code] field: message`. Add `--json` for a structured report. |
| `gitsvg schema` | Index of all input operations. `gitsvg schema <op>` prints the JSON Schema for a specific operation; `--list-ops` prints a bare op list. |
| `gitsvg errors` | Index of all validation error codes. `gitsvg errors <code>` prints the long-form catalog entry; `--list-codes` prints a bare code list. |

`gitsvg schema` and `gitsvg errors` are designed for agents and tooling: an LLM-based agent producing input can fetch the schema for a single op and the catalog entry for any error it hits, without reading the rest of the documentation.

## License

[MIT](https://github.com/bertpl/gitsvg/blob/main/LICENSE).
