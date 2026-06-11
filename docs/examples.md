# Examples

Every diagram below is one of the self-contained input files shipped in the
[`examples/`](https://github.com/bertpl/gitsvg/tree/main/examples) folder. Each
shows the rendered SVG and the `.gitsvg.jsonl` source it came from — copy any
of them as a starting point.

The first seven cover the diagram operations; the rest demonstrate theming,
orientation, and layout modes.

## 1. Linear history

A single branch with a few commits — the minimum viable diagram.

![Linear history](assets/examples/01_linear.svg)

```jsonl
{"op": "branch", "name": "main", "label_side": "before"}
{"op": "commit", "branch": "main", "id": "c1", "msg": "initial commit", "hash": "auto"}
{"op": "commit", "branch": "main", "id": "c2", "msg": "add README", "hash": "auto"}
{"op": "commit", "branch": "main", "id": "c3", "msg": "add tests", "hash": "auto"}
{"op": "commit", "branch": "main", "id": "c4", "msg": "fix typo", "hash": "auto"}
```

## 2. Branch and merge

A `feature` branch forks off `main`, accumulates a couple of commits, then
merges back.

![Branch and merge](assets/examples/02_branch_merge.svg)

```jsonl
{"op": "branch", "name": "main", "label_side": "before"}
{"op": "commit", "branch": "main", "id": "c1", "msg": "initial commit", "hash": "auto"}
{"op": "commit", "branch": "main", "id": "c2", "msg": "setup config", "hash": "auto"}
{"op": "branch", "name": "feature", "from_branch": "main"}
{"op": "commit", "branch": "feature", "id": "f1", "msg": "add login form", "hash": "auto"}
{"op": "commit", "branch": "feature", "id": "f2", "msg": "wire up auth", "hash": "auto"}
{"op": "merge", "from": "feature", "into": "main", "as": "m1", "msg": "merge feature", "hash": "auto"}
```

## 3. Multiple branches with lane reuse

Two concurrent branches share lanes 1 and 2; after both merge, a later
`feature-b` reclaims the now-free lane 1 instead of starting a new one. Lane
assignment is automatic and geometry-driven.

![Multiple branches with lane reuse](assets/examples/03_multi_branch.svg)

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

## 4. Highlighting a commit

The `highlight` op marks an existing commit with an enlarged dot and a bold
label — useful for drawing attention to a release or a key milestone.

![Highlighted release commit](assets/examples/04_highlight.svg)

```jsonl
{"op": "branch", "name": "main", "label_side": "before"}
{"op": "commit", "branch": "main", "id": "c1", "msg": "initial commit", "hash": "auto"}
{"op": "commit", "branch": "main", "id": "c2", "msg": "feature work", "hash": "auto"}
{"op": "commit", "branch": "main", "id": "c3", "msg": "more feature work", "hash": "auto"}
{"op": "commit", "branch": "main", "id": "v1", "msg": "release v1.0", "hash": "auto"}
{"op": "commit", "branch": "main", "id": "c4", "msg": "post-release fix", "hash": "auto"}
{"op": "highlight", "commit": "v1"}
```

## 5. Remove and rebuild (rebase pattern)

A `feature` branch is removed and re-declared on top of a more recent `main`
commit, with the same commit IDs as before. This is the rebase-style "move my
work onto the new tip" pattern, expressed as primitives.

![Remove and rebuild](assets/examples/05_remove_rebuild.svg)

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

## 6. Import and squash

The `import` op replays another file as a prelude — here it picks up the
rebased state from Example 5. A single new commit then squashes `f1` and `f2`
into one via `replaces`.

![Import and squash](assets/examples/06_import_squash.svg)

```jsonl
{"op": "import", "path": "05_remove_rebuild.gitsvg.jsonl"}
{"op": "commit", "branch": "feature", "replaces": ["f1", "f2"], "id": "f_squash", "msg": "complete feature", "hash": "auto"}
```

## 7. Open pull request

The `pull_request` op declares a pending merge between two branches. Both
endpoints live-track the current branch tips: as commits accumulate on either
side, the dashed arc advances. The optional `title` renders as a pill anchored
at the source-tip commit. The typical lifecycle closes the PR with `remove`
and then runs a real `merge`; this example stops before either, so the open PR
remains visible in the final state.

![Open pull request](assets/examples/07_pull_request.svg)

```jsonl
{"op": "branch", "name": "main", "label_side": "before"}
{"op": "commit", "branch": "main", "id": "m1", "msg": "release"}
{"op": "branch", "name": "feature", "from_branch": "main"}
{"op": "commit", "branch": "feature", "id": "f1", "msg": "wip"}
{"op": "pull_request", "id": "pr1", "from": "feature", "into": "main", "title": "PR 1: add thing"}
{"op": "commit", "branch": "feature", "id": "f2", "msg": "polish"}
{"op": "commit", "branch": "main", "id": "m2", "msg": "hotfix"}
```

## 8. Recolored palette

The `theme` op customizes the presentational surface — spacings, sizes, fonts,
the branch-color palette, the background, and more. Here we import Example 3
unchanged and apply a saturated palette with thicker strokes, larger labels,
and a warm background.

![Recolored palette](assets/examples/08_themed.svg)

```jsonl
{"op": "import", "path": "03_multi_branch.gitsvg.jsonl"}
{"op": "theme", "background_color": "#fff8e7", "branch_spacing": 110, "branch_line_width": 4, "label_font_size": 14, "branch_label_font_size": 14, "hash_font_size": 11, "commit_radius": 7, "highlight_radius": 9, "branch_name_pill_offset_commit_axis_in_rows": -0.56, "colors": {"main": "#d62728", "branch1": "#1f77b4", "branch2": "#2ca02c", "branch3": "#ff7f0e", "branch4": "#9467bd"}}
```

## 9. Horizontal orientation

A `theme.orientation` of `lr` flips the diagram left-to-right: the commit axis
grows rightward and branches stack downward. The same input renders in `bt`
(default, bottom-to-top), `tb` (top-to-bottom), and `rl` (right-to-left);
pill placement, margin defaults, and label-side mapping all adjust per
orientation. Accepted values include the canonical short codes (`bt`, `tb`,
`lr`, `rl`) and common aliases (Mermaid's `TD`, CSS's `ltr` / `rtl`, long forms
like `bottom_to_top`, and `top_down` / `bottom_up`).

![Horizontal orientation](assets/examples/09_horizontal.svg)

```jsonl
{"op": "branch", "name": "main", "label_side": "before"}
{"op": "commit", "branch": "main", "id": "m1", "msg": "init", "hash": "auto"}
{"op": "commit", "branch": "main", "id": "m2", "msg": "release v1", "hash": "auto", "highlight": true}
{"op": "branch", "name": "feature", "from_branch": "main"}
{"op": "commit", "branch": "feature", "id": "f1", "msg": "wip", "hash": "auto"}
{"op": "commit", "branch": "feature", "id": "f2", "msg": "polish", "hash": "auto"}
{"op": "branch", "name": "docs", "from_branch": "main"}
{"op": "commit", "branch": "docs", "id": "d1", "msg": "readme", "hash": "auto"}
{"op": "merge", "into": "main", "from": "feature", "msg": "merge feature", "hash": "auto"}
{"op": "commit", "branch": "main", "id": "m3", "msg": "hotfix", "hash": "auto"}
{"op": "pull_request", "id": "pr1", "from": "docs", "into": "main", "title": "PR 1: docs update"}
{"op": "theme", "orientation": "lr"}
```

## 10. Built-in named themes

Beyond `default`, gitsvg ships four built-in themes:

- **`muted`** — the pre-refresh default look: a softer, grayer branch palette
  with plain circle merge dots.
- **`dark`** — One Dark-inspired palette on a `#282c34` canvas.
- **`compact`** — ~30 % denser spacing with smaller fonts.
- **`gui`** — a desktop-git-GUI look: table layout, auto lane change, tight
  spacing, and a system-color branch palette.

Selecting one is a single field on a `theme` op (`{"op": "theme", "name": "dark"}`).
The preview below tiles `default`, `muted`, `dark`, and `compact` on a shared
input, with the table-layout `gui` theme shown beneath on its own diagram.

![Built-in named themes](assets/examples/10_named_themes.svg)

Selecting a named theme also wipes any `theme` field overrides and
`branch.color` overrides accumulated earlier. To layer a chosen theme on top of
those overrides instead, pass `keep_prior_overrides: true` on the same op.

## 11. Unique commit rows

By default (`commit_row_mode: shared`) commits on different branches may share a
row, which keeps diagrams compact. Setting `theme.commit_row_mode` to `unique`
gives every commit its own row, assigned in authoring order — so reading along
the commit axis recovers the exact order events were declared, even when work
on several branches interleaves.

![Unique commit rows](assets/examples/11_unique_rows.svg)

```jsonl
{"op": "branch", "name": "main", "label_side": "before"}
{"op": "commit", "branch": "main", "id": "m1", "msg": "project start", "hash": "auto"}
{"op": "branch", "name": "auth", "from_branch": "main"}
{"op": "commit", "branch": "auth", "id": "a1", "msg": "login form", "hash": "auto"}
{"op": "branch", "name": "ui", "from_branch": "main"}
{"op": "commit", "branch": "ui", "id": "u1", "msg": "navbar", "hash": "auto"}
{"op": "commit", "branch": "auth", "id": "a2", "msg": "oauth", "hash": "auto"}
{"op": "commit", "branch": "ui", "id": "u2", "msg": "dark mode", "hash": "auto"}
{"op": "merge", "from": "auth", "into": "main", "as": "m2", "msg": "merge auth", "hash": "auto"}
{"op": "commit", "branch": "ui", "id": "u3", "msg": "polish", "hash": "auto"}
{"op": "merge", "from": "ui", "into": "main", "as": "m3", "msg": "merge ui", "hash": "auto"}
{"op": "theme", "commit_row_mode": "unique"}
```

## 12. Auto lane change

By default a branch keeps its lane for its whole life, so once an inner branch
merges its lane sits empty while outer branches stay stranded. Setting
`theme.auto_lane_change` to `true` compacts the graph the way real git tools
do: as each lower lane frees up, the surviving branches migrate inward. The
shift is drawn as a short connector in the branch line's own style.

![Auto lane change](assets/examples/12_auto_lane_change.svg)

```jsonl
{"op": "branch", "name": "main", "label_side": "before"}
{"op": "commit", "branch": "main", "id": "m1", "msg": "project start", "hash": "auto"}
{"op": "branch", "name": "feat-a", "from_branch": "main"}
{"op": "commit", "branch": "feat-a", "id": "a1", "msg": "feature a", "hash": "auto"}
{"op": "branch", "name": "feat-b", "from_branch": "main"}
{"op": "commit", "branch": "feat-b", "id": "b1", "msg": "feature b", "hash": "auto"}
{"op": "branch", "name": "feat-c", "from_branch": "main"}
{"op": "commit", "branch": "feat-c", "id": "c1", "msg": "feature c", "hash": "auto"}
{"op": "merge", "from": "feat-a", "into": "main", "as": "ma", "msg": "merge a", "hash": "auto"}
{"op": "commit", "branch": "feat-b", "id": "b2", "msg": "more b", "hash": "auto", "gap": 1}
{"op": "commit", "branch": "feat-c", "id": "c2", "msg": "more c", "hash": "auto"}
{"op": "merge", "from": "feat-b", "into": "main", "as": "mb", "msg": "merge b", "hash": "auto"}
{"op": "commit", "branch": "feat-c", "id": "c3", "msg": "polish c", "hash": "auto", "gap": 1}
{"op": "merge", "from": "feat-c", "into": "main", "as": "mc", "msg": "merge c", "hash": "auto"}
{"op": "commit", "branch": "main", "id": "m2", "msg": "release", "hash": "auto"}
{"op": "theme", "auto_lane_change": true}
```

## 13. Desktop-GUI table theme

The `gui` theme renders a multi-branch history the way a desktop git client
would — the graph on the left, a per-commit table on the right (message and
hash columns), and each branch's name as a colored pill at the commit its ref
points to. It is best seen at full size.

![Desktop-GUI table theme](assets/examples/13_gui_table.svg)
