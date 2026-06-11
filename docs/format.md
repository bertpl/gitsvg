# Input format

A gitsvg diagram is described by a `.gitsvg.jsonl` file: one JSON object per
line, each an **operation**, applied top-to-bottom to build up the diagram
state. A line's `op` field names the operation; the remaining fields are its
arguments.

```jsonl
{"op": "branch", "name": "main", "label_side": "before"}
{"op": "commit", "branch": "main", "id": "c1", "msg": "initial commit", "hash": "auto"}
```

This page is an overview of the nine operations. For the exact, authoritative
field schema of any operation — including which fields are required, their
types, and defaults — run:

```bash
gitsvg schema <op>      # e.g. gitsvg schema commit
```

## The nine operations

| Op | Purpose |
|----|---------|
| `branch` | Declare a branch. The first branch is the trunk; later branches fork off an existing one via `from_branch`. |
| `commit` | Add a commit to a branch. Its parent is structural — the branch's prior tip. `replaces` squashes named commits into this one. |
| `merge` | Merge one branch into another, producing a merge commit with two parents (`from`-tip and `into`-tip). The only op that creates a multi-parent commit. |
| `pull_request` | Declare a pending merge between two branches. Both endpoints live-track the current branch tips; renders as a dashed arc with an optional title pill. |
| `remove` | Remove branches from the diagram — used for the rebase-style remove-and-rebuild pattern and to close a pull request before merging. |
| `highlight` | Mark an existing commit with an enlarged dot and a bold label. |
| `import` | Replay another `.gitsvg.jsonl` file inline as a prelude, then continue with the current file's ops. The path must be relative and stay inside the top-level input file's directory. |
| `theme` | Override the presentational surface (spacings, sizes, fonts, palette, background, orientation, layout modes). A `name` selects a built-in theme to resolve from. |
| `grid` | Pin the diagram's slot counts (`n_commits`, `n_branches`) instead of letting the renderer auto-fit. |

## How a diagram is built

- **Commits chain structurally.** A commit's parent is its branch's current
  tip; there is no parent list to author. Multi-parent commits come only from
  `merge`.
- **Lanes are automatic.** Branches are assigned lanes geometrically, reusing
  freed lanes; `theme.auto_lane_change` lets a branch migrate inward as lower
  lanes free up.
- **`theme` ops accumulate.** Each `theme` op overrides only the fields it
  lists, layering on the resolved theme so far. Selecting a `name` resets field
  and color overrides unless `keep_prior_overrides: true` is set.
- **Hashes can be automatic.** `hash: "auto"` derives a deterministic
  seven-character hex string from the commit's id and parents.

## Validation

Every input passes through a validation pipeline before rendering. Errors are
reported as `file:line: [code] field: message`, where `code` is a stable error
code (e.g. `E200`). Look up any code's long-form explanation with:

```bash
gitsvg errors <code>    # e.g. gitsvg errors E200
```

See the [CLI reference](cli.md) for `validate`, `schema`, and `errors` in full.
