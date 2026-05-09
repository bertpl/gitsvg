# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 0.0.3 (2026-05-09)

### Added

- `commit:` op gains a `gap:` field (non-negative integer, default `0`): leaves N empty commit-axis slots between the branch's tip and the new commit's landing position, for hand-tuned breathing room. Allowed on squash (`replaces:`) commits too; when unset there, the state engine inherits the earliest replaced commit's `gap` by default — preserving any breathing room the original chain had.
- `merge:` op gains the same `gap:` field, applied above the natural anchor at `max(into.tip, from.tip) + 1`.
- `canvas:` op gains four pixel-margin fields — `margin_commit_axis_lower`, `margin_commit_axis_upper`, `margin_branch_axis_lower`, `margin_branch_axis_upper` — one per axis end. Default is renderer auto-fit; pin them only when stable per-frame margins matter (animation series).
- `hash: "auto"` on `commit:` ops now resolves to a deterministic 7-character hex string. The hash is the lower-cased hex of `sha256(id + "\n" + sorted(immediate_parent_ids))[:7]`. Sorting parents makes the hash insensitive to declaration order on merge parents; including parent ids makes it sensitive to rebase-style chain changes (so a downstream commit gets a new hash when an upstream commit's id is renamed).
- `merge:` op gains a `hash:` field (with the same `"auto"` sentinel as `commit:`), so merge commits can carry a stable, auto-generated identifier across animation frames.
- Internal: layout engine (`gitsvg.layout`) — pure-computation module that turns a validated op stream into per-branch and per-commit axis positions. Not exposed through the CLI yet; consumed by rendering work to follow.
- `gitsvg render <input> -o <output>` command — renders a validated `.gitsvg.jsonl` file to SVG (single file in, single file out). Runs the validate pipeline first; emits no output and exits non-zero on errors.
- `make render-local` target — walks `local/test_examples/` and renders every `.gitsvg.jsonl` to a sibling `_render_outputs/` directory. Skipped silently when the directory is absent.
- Render output now includes branch-off arcs (quarter-circle curves from a parent commit on one lane to the start of a child branch on another, in the new branch's colour) and merge arcs (vertical-first quarter-circle curves from a merging-from branch's tip to the merge commit on the merging-into branch's lane, in the source branch's colour).
- Render output now includes branch guides — faint dashed vertical lines at every occupied lane, sitting behind branch lines and arcs as a subtle visual anchor.
- Render output now includes commit labels — the commit's `msg` is drawn as the primary line in `LABEL_FONT_SIZE` next to the dot (on the side indicated by `label_side`); when `hash` is set, it appears as a smaller secondary line in `HASH_FONT_SIZE`/`HASH_COLOR` directly below. Multi-line `msg` strings (split on `\n`) stack vertically with consistent line spacing, centred on the dot's y.
- Render output now includes branch-name pills — coloured rounded rectangles with the branch name in white, positioned `BRANCH_NAME_PILL_OFFSET` pixels below each branch's start point. Canvas height auto-reserves room for the bottom-most pill.
- Highlight visual: a commit with `highlight: true` now renders with an enlarged dot (`HIGHLIGHT_RADIUS`) and a bold (weight 700) `msg` label. The hash secondary line stays at regular weight.
- `canvas:` op honours all eight optional fields end-to-end: `n_commits`, `n_branches`, `commit_spacing`, `branch_spacing`, and the four `margin_*_axis_*` margins. Pinned values flow through to the rendered SVG dimensions and the renderer's coordinate transform; auto-fit kicks in for any field left unset.
- Auto-fit margins reserve room for the longest visible labels per side: the lower / upper branch-axis margins extend to fit pills on the leftmost / rightmost lane and any commit msg/hash whose `label_side` points outward; the lower commit-axis margin reserves room for the bottom-most pill (the root branch's). Authors who pin a margin via `canvas:` opt out of auto-fit for that side.
- Pinned-canvas overflow: when content exceeds pinned `n_commits`/`n_branches`, the rendered SVG keeps the pinned dimensions; content past the canvas edge is clipped by SVG default `overflow:hidden`. Authors who pin canvas size are expected to ensure content fits.

### Changed

- Internal: rendering pipeline restructured into a three-stage architecture — state engine (op stream → entities) → layout engine (entities → render-ready model with positions, resolved colours, arcs, guides, canvas dimensions) → renderer (model → SVG primitives). The renderer no longer depends on state internals; alternative layout strategies and renderers can be plugged in without touching each other. No user-visible behaviour change for the existing corpus.

### Removed

- `commit_pos:` and `branch_pos:` fields on `commit:` op. The commit-axis case is replaced by relative `gap:`; commit-level branch-axis overrides aren't needed in v0.0.x (commits always live on their branch's lane).
- `branch_pos:` field on `branch:` op. Branch-axis position is now auto-assigned in declaration order; an override mechanism may return when lane-reuse heuristics land.
## 0.0.2 (2026-05-08)

### Added

- `gitsvg schema` command: prints an index of all input operations with one-line descriptions; `gitsvg schema <op>` prints the JSON Schema for that op; `gitsvg schema --list-ops` prints a bare op-name list.
- `gitsvg errors` command: prints an index of all registered validation error codes; `gitsvg errors <code>` prints that code's long-form catalog entry; `gitsvg errors --list-codes` prints a bare code list. The catalog ships empty for now; entries are added as the validator gains error sites.
- `gitsvg validate <file>` command: parses a `.gitsvg.jsonl` input file line by line, runs per-op schema validation, and reports any errors with `file:line: [code] field: message` formatting. Pass `--json` for a structured `{ ok, errors }` report. Exits non-zero when validation fails. Import-resolution and end-of-file checks land in subsequent versions of the validator.
- `gitsvg validate` now runs per-op semantic validation in addition to schema validation. Branch existence, commit-id uniqueness, commit-id references, the `replaces:` 7-rule check, branch-root constraints, and remove-cascade behaviour all surface as structured errors with their own catalog codes.
- Error catalog now spans 23 entries: parse-phase (E001-E004), schema-phase (E100-E108), and semantic-phase (E200-E209). Each entry is browseable via `gitsvg errors <code>`.
- Import resolution: `gitsvg validate` now expands a leading `import` op into the imported file's ops before running schema and semantic checks. Cycle detection (on resolved absolute paths), depth-limit cap (1000), missing-file errors, and structural rules (at most one import, must be first) all surface as catalog codes E300-E304. Each parsed op carries `(file, line)` provenance, so errors against imported ops still point at the original file.
- End-of-file cross-reference validation: after applying every op, `gitsvg validate` walks the final state and flags branch roots and commit parents that point at commits that have since been removed (E400, E401). The rebuild pattern (remove + re-add with the same id) passes cleanly because the missing reference is restored before EOF. Final validator pipeline: parse → import-expand → state-apply → end-of-file check.
- Synthetic input corpus under `tests/fixtures/inputs/` — 13 hand-authored files spanning happy paths (basics, squash + rebuild, import chain) and sad paths (parse / schema / semantic / replaces / EOF / import errors). Run via the integration test suite alongside `make test`.
- `make validate-local` target — walks `local/test_examples/` recursively and runs the full validate pipeline on every `*.gitsvg.jsonl`. Skipped silently when the directory is absent. Useful as a developer-side regression guard against breaking real diagrams.

### Removed

- The placeholder `gitsvg render` command (shipped only with v0.0.1) is removed; rendering will return as part of v0.0.3.
- The `rich` dependency, which was unused in v0.0.1 scaffolding.
## 0.0.1 (2026-05-08)

### Added

- Initial placeholder release to reserve the PyPI name.
