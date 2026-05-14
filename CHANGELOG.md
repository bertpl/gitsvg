# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Added

- Five new `theme:` op fields expose previously-internal visual constants for user customisation: `guide_overshoot_in_rows`, `pill_padding_x_in_font_sizes`, `pill_padding_y_in_font_sizes`, `pill_corner_radius_in_font_sizes`, `label_line_padding_in_font_sizes`. Defaults reproduce today's pixel values; see the format spec for anchors.
- Two new validation error codes on the `theme:` op surface: `E218` (`branch_spacing` / `commit_spacing` must be `> 0`), `E219` (font sizes must be `> 0`).

### Changed

- **Breaking:** the `canvas:` op is renamed `grid:` and trimmed to its two slot-count fields (`n_commits`, `n_branches`); spacings and margins move exclusively to `theme:`. Migration: rename `"op": "canvas"` to `"op": "grid"`, and move any spacing/margin fields onto a `theme:` op (same field names).
- **Breaking:** six `theme:` op fields renamed and reparametrised as ratios of their grid anchor. The four margins (`margin_branch_axis_lower`, `margin_branch_axis_upper`, `margin_commit_axis_lower`, `margin_commit_axis_upper`) gain an `_in_lanes` (branch-axis) or `_in_rows` (commit-axis) suffix; `arc_corner_radius` → `arc_corner_radius_in_grid_units`; `label_offset` → `label_offset_branch_axis_in_lanes`. Migration: rename, then divide each value by its anchor — `branch_spacing` for `_in_lanes`, `commit_spacing` for `_in_rows`, or `min(branch_spacing, commit_spacing)` for `_in_grid_units`.
- **Breaking:** the two pill-offset fields each split into a signed two-axis ratio pair (positive = toward higher index on the named axis): `branch_name_pill_offset` → `branch_name_pill_offset_commit_axis_in_rows` (default `-0.5`) + `branch_name_pill_offset_branch_axis_in_lanes` (default `0.0`); same shape for `pull_request_pill_offset` (defaults `+0.5` and `0.0`).

### Deprecated

### Removed

### Fixed

### Security

## 0.1.4 (2026-05-12)

### Added

- New `theme` op for applying presentational overrides (spacings, margins, font sizes, stroke widths, colour palette, background) from JSONL. Each op patches the live theme; `"name": "default"` resets every field to the package defaults.
- `theme.colors` accepts a replacement branch-colour palette dict.
- Optional full-canvas background colour via `theme.background_color` (default unset = transparent).
- New shipped example (`examples/08_themed.gitsvg.jsonl`) demonstrating the theme op via a saturated palette over an imported diagram.
## 0.1.3 (2026-05-11)

### Added

- New `pull_request` op for declaring a pending merge; lifecycle is `pull_request` → `remove` → `merge`.
- New shipped example (`examples/07_pull_request.gitsvg.jsonl`) demonstrating an open pull-request with live-tracked endpoints.

### Changed

- Every op's `gitsvg schema` output now carries a per-field `description`.

### Fixed

- Default-mode SVG output is byte-equivalent to v0.1.1 again; the font-family trim from v0.1.2 now applies only under `--small`.
- Empty branches no longer emit a zero-length `<path>` element for their (invisible) branch line.
## 0.1.2 (2026-05-10)

### Added

- `gitsvg render --small` flag for compact SVG output (~30% smaller on shipped examples). Default output unchanged.

### Changed

- README CI badge now reads `CI: passing` instead of `Push to Main: passing`.
- `gitsvg schema commit` description no longer references a development version.
- Trimmed the SVG `font-family` fallback chain to `Inter, sans-serif`; viewers without Inter installed fall back to the host's generic `sans-serif`.

## 0.1.1 (2026-05-10)

### Changed

- Removed the inline alpha-status disclaimer from the README; the PyPI dev-status classifier already conveys this.

### Fixed

- Example images now display on PyPI (README references switched from repo-relative paths to absolute GitHub raw URLs).

## 0.1.0 (2026-05-10)

### Added

- `examples/` folder with six hand-written `.gitsvg.jsonl` files and their rendered SVGs, demonstrating the v0.0.x feature surface.
- README rewritten for first external use: quick-start, walkthrough of all six examples, and a CLI reference table.

### Changed

- PyPI development-status classifier bumped from `1 - Planning` to `3 - Alpha`.

## 0.0.4 (2026-05-09)

### Added

- `branch:` op gains an optional `branch_pos:` field pinning the branch's lane index; authors who set it take responsibility for the resulting layout.

### Changed

- Lane assignment now reuses freed lanes instead of monotonic declaration order, so the rebase-rebuild pattern and compact-left both render naturally. Pin `branch_pos:` to override.

## 0.0.3 (2026-05-09)

### Added

- `commit:` op gains an optional `gap:` field leaving N empty commit-axis slots between the branch's tip and the new commit, for hand-tuned breathing room.
- `merge:` op gains the same `gap:` field.
- `canvas:` op gains four optional pixel-margin fields (one per axis end); default is renderer auto-fit.
- `hash: "auto"` on `commit:` ops now resolves to a deterministic 7-character hex string derived from the commit's id and parent ids.
- `merge:` op gains a `hash:` field (same `"auto"` sentinel as `commit:`).
- Internal: layout engine (`gitsvg.layout`) — turns validated op stream into render-ready positions.
- `gitsvg render <input> -o <output>` command renders a validated `.gitsvg.jsonl` to SVG.
- `make render-local` target walks `local/test_examples/` and renders every `.gitsvg.jsonl`. Skipped silently when absent.
- Render output now includes branch-off arcs and merge arcs connecting parent commits to child-branch starts and merge commits.
- Render output now includes branch guides — faint dashed vertical lines at every occupied lane.
- Render output now includes commit labels (`msg` primary, optional `hash` as a smaller secondary line); multi-line `msg` strings stack vertically.
- Render output now includes branch-name pills — coloured rounded rectangles positioned below each branch's start point.
- Highlight visual: a commit with `highlight: true` now renders with an enlarged dot and a bold `msg` label.
- `canvas:` op honours all eight optional fields end-to-end; auto-fit kicks in for fields left unset.
- Auto-fit margins reserve room for the longest visible labels per side; pin via `canvas:` to opt out.
- Pinned-canvas overflow: when content exceeds pinned `n_commits`/`n_branches`, the excess is clipped by SVG default `overflow:hidden`.

### Changed

- Internal: rendering pipeline restructured into state → layout → renderer stages. No user-visible behaviour change.

### Removed

- `commit_pos:` and `branch_pos:` fields on `commit:` op; commit-axis case is replaced by relative `gap:`.
- `branch_pos:` field on `branch:` op; branch-axis position is now auto-assigned in declaration order.

## 0.0.2 (2026-05-08)

### Added

- `gitsvg schema` command lists input operations; `gitsvg schema <op>` prints that op's JSON Schema.
- `gitsvg errors` command lists registered validation error codes; `gitsvg errors <code>` prints that code's catalog entry.
- `gitsvg validate <file>` command parses and validates a `.gitsvg.jsonl` file; pass `--json` for a structured report.
- `gitsvg validate` now runs per-op semantic validation in addition to schema validation.
- Error catalog now spans 23 entries across parse, schema, and semantic phases.
- Import resolution: `gitsvg validate` expands a leading `import` op before schema and semantic checks; cycle detection, depth limit, and missing files surface as catalog codes.
- End-of-file cross-reference validation flags references to removed commits (E400, E401). The rebuild pattern (remove + re-add with the same id) still passes cleanly.
- Synthetic input corpus under `tests/fixtures/inputs/` — 13 hand-authored files covering happy and sad paths, run via `make test`.
- `make validate-local` target walks `local/test_examples/` recursively and runs the full validate pipeline. Skipped silently when absent.

### Removed

- The placeholder `gitsvg render` command (shipped only with v0.0.1) is removed.
- The `rich` dependency, which was unused in v0.0.1 scaffolding.

## 0.0.1 (2026-05-08)

### Added

- Initial placeholder release to reserve the PyPI name.
