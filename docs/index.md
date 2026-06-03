# gitsvg

**A CLI that renders git tree visualizations as SVG from JSONL input.**

gitsvg turns a plain-text description of a git history — branches, commits,
merges, pull requests — into a clean SVG diagram. The input is a
`.gitsvg.jsonl` file: a list of operations, one JSON object per line, applied
top-to-bottom to build the diagram. Because the format is line-oriented and
declarative, it is easy for both people and LLM-based agents to author.

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

Write a `.gitsvg.jsonl` file:

```jsonl
{"op": "branch", "name": "main", "label_side": "before"}
{"op": "commit", "branch": "main", "id": "c1", "msg": "initial commit", "hash": "auto"}
{"op": "commit", "branch": "main", "id": "c2", "msg": "add README", "hash": "auto"}
{"op": "branch", "name": "feature", "from_branch": "main"}
{"op": "commit", "branch": "feature", "id": "f1", "msg": "add login form", "hash": "auto"}
{"op": "merge", "from": "feature", "into": "main", "as": "m1", "msg": "merge feature", "hash": "auto"}
```

Render it to SVG:

```bash
gitsvg render diagram.gitsvg.jsonl -o diagram.svg
```

Validate without rendering:

```bash
gitsvg validate diagram.gitsvg.jsonl
```

That's the whole loop. See the [Examples](examples.md) gallery for the full
feature surface — branching, merges, pull requests, theming, orientations, and
layout modes — and the [Input format](format.md) page for the operation set.

## Where to go next

- **[Examples](examples.md)** — a gallery of rendered diagrams with their source.
- **[CLI reference](cli.md)** — every command, including the agent-facing
  `schema` / `errors` / `theme` introspection commands.
- **[Input format](format.md)** — the nine operations and how a diagram is built.
- **[Python API](api.md)** — `gitsvg.render_text()` for embedding gitsvg in
  other tools.
