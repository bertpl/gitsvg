# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 0.3.1 (2026-06-10)

### Added

- The package now ships a PEP 561 `py.typed` marker, so type checkers see the public API as typed.

### Changed

- PyPI development-status classifier bumped from `3 - Alpha` to `4 - Beta`.

### Fixed

- Validation errors without a source location no longer print a `None:0:` prefix.
- Raise the `pydantic` minimum to 2.12.0 on Python 3.14, where the declared 2.10.0 floor has no installable wheel.
## 0.3.0 (2026-06-03)

### Added

- Hosted documentation site at [gitsvg.readthedocs.io](https://gitsvg.readthedocs.io/).
## 0.2.7 (2026-06-03)

### Added

- New `gitsvg theme` command to inspect the built-in named themes — index, per-theme resolved values, and a bare-name list.
- New public `gitsvg.render_text()` API — renders a JSONL op-stream string to an inline-embeddable SVG string; raises `GitsvgValidationError` on invalid input.

### Changed

- **Breaking:** named-theme inspection moved from `gitsvg schema` to the new `gitsvg theme` command: `schema theme <name>` → `theme <name>`, `schema themes` → `theme --list-names`.
- US English spelling normalized across user-facing text — CLI `gitsvg schema` field descriptions and error-catalog entries — and the documentation. No behavioral change.

### Removed

- **Breaking:** removed the `commit` op's `parents` field; a commit's parents are now structural (its branch's prior commit), and `merge` is the only op that adds a second parent. Migration: replace `commit … "parents": [...]` with a `merge` op.

### Fixed

- `theme.merge_commit_radius` now defaults to the effective `commit_radius` (including a `theme:`-overridden value) instead of the package default, so merge dots track a customized `commit_radius` as documented (regressed in 0.2.6).
- Fractional values for the numeric `theme:` size fields (spacings, radii, line width) no longer crash with a traceback; sub-pixel values are now honored, and whole numbers render exactly as before.
- Branching off — or merging from — a branch with no commits of its own now resolves to the commit that branch points at (its branch-off commit), instead of detaching the new branch or dropping the merge's second parent.
- A `merge` op with `from` and `into` set to the same branch is now rejected (new error `E209`), matching the existing `pull_request` guard (E210); it previously produced a degenerate single-parent commit.
- Exclude click 8.3.0/8.3.1, which broke the optional-value `--small` flag (fixed in click 8.3.2).
## 0.2.6 (2026-06-01)

### Added

- New `theme.commit_row_band_color` — paints a zebra stripe on alternate commit-axis rows (full canvas, any orientation) for easier row-tracking; unset by default. Accepts an alpha channel (`#RRGGBBAA`) so the stripe composes over the background.
- New `theme.commit_label_layout: table` lays commit labels out as a table beside the graph — message and hash columns, with branch names as pills at their tip commits (vertical orientations only).
- New `theme.table_cell_padding_x_in_font_sizes` (default `0.5`) sets the table's horizontal cell padding and the gaps between tip pills and the message.
- New `theme.merge_commit_radius` (defaults to `commit_radius`) sizes merge-commit dots independently — e.g. to keep merges prominent while shrinking ordinary dots.
- New built-in `gui` named theme mimicking a desktop git GUI — table layout, auto lane change, tight spacing, and a system-color branch palette.
- New shipped example `examples/13_gui_table.svg` demonstrating the `gui` theme; also shown as a fifth tile on the named-themes preview.

### Changed

- All hex color fields (`theme.*_color`, `branch.color`) now accept an optional alpha channel (`#RGBA` / `#RRGGBBAA`), e.g. for a translucent `background_color`; opaque `#RGB` / `#RRGGBB` are unchanged.
## 0.2.5 (2026-05-31)

### Added

- New `theme.auto_lane_change` (default off) — branches migrate toward lower lane indices as lower lanes free up, so live branches always occupy the lowest lanes, with each lane shift drawn in the active `branch_line_style`; conflicts with a `branch.branch_pos` pin (new error `E221`).
- New `theme.merge_lane_clearance` (default `1`) — under `auto_lane_change`, the row margin kept between a merged or pull-requested branch and a neighboring branch migrating into the lane it vacates; setting it with `auto_lane_change` off is rejected (new error `E222`).

### Changed

- Merge and pull-request connectors are now single-row hops: a branch line runs up to one row below the merge, then a short connector crosses in. The `rounded` style's output is visually unchanged; `straight` / `double_rounded` / `double_bezier` render merges and PRs more tightly.
- `gitsvg layout` JSON now carries a per-branch `segments` array (the lane / start / end breakdown of each branch's life) — one entry for a static branch, several when it migrates under `auto_lane_change`.
- **Breaking:** `theme.branch_line_style: "bezier"` is redefined as a single flowing curve that runs along a branch's own lane and sweeps diagonally across to the connecting commit; the prior cubic-Bézier S is now the separate value `"double_bezier"`. Migration: rename `"bezier"` → `"double_bezier"` to keep the S.
- Refreshed the `default`, `dark`, and `compact` named themes.
## 0.2.4 (2026-05-31)

### Added

- New `theme.commit_row_mode` — `shared` (default) or `unique` — `unique` gives every commit its own commit-axis row, assigned in authoring order, so vertical position encodes the order events were declared; default output unchanged.
## 0.2.3 (2026-05-30)

### Added

- New `theme.branch_line_style` — `rounded` (default), `straight`, `bezier`, or `double_rounded` — sets the shape of branch-off, merge, and pull-request connectors.
- New `theme.merge_commit_style` — `checkmark` (default) or `circle` — marks merge commits with a checkmark inside the dot.
- New built-in `muted` named theme — the pre-refresh default look (softer palette, rounded connectors, circle merge dots).

### Changed

- Default theme refreshed: more-saturated branch palette and checkmark merge dots; select `theme: {"name": "muted"}` for the prior look.
## 0.2.2 (2026-05-19)

### Changed

- `gitsvg layout` JSON output schema slimmed — `vertical_first`, `color_branch_id`, `guides`, and `label_side` no longer emitted.
## 0.2.1 (2026-05-18)

### Added

- `gitsvg render` accepts a directory pair: recursively walks `INPUT_DIR` for `*.gitsvg.jsonl` files and writes mirrored `.svg` outputs under `OUTPUT_DIR`, preserving subdirectory structure.
- New `gitsvg state INPUT` command emits a JSON snapshot of the diagram (branches, commits, open pull requests, ids, parents).
- New `gitsvg layout INPUT` command emits a JSON view of the resolved layout (grid, lanes, commit positions, arcs, guides, pull-request geometry).
## 0.2.0 (2026-05-17)

### Changed

- README example fixes — Example 8 JSONL synced with the shipped file; Example 10 narrative distinguishes the "how to use" snippet from the multi-theme preview image.
- README CLI reference — explicit pointer to `gitsvg schema theme` (no name) for the theme op's field schema, disambiguating from the named-theme inspection forms.
- `gitsvg schema theme` — `branch_label_angle` field description no longer references a deferred "later version" for visually optimal angle/anchor pairings; named themes already shipped in v0.1.10.
## 0.1.11 (2026-05-17)

### Changed

- `--small` is now a minification level dial (`--small=N`, `N` in 0-3) instead of a binary flag; bare `--small` selects level 2 (lossless structural compression). The font-fallback trim from v0.1.2 moves to level 3 — pass `--small=3` to restore the v0.1.10 `--small` output exactly.
- `--small=2` and `--small=3` now extract repeated presentation attributes into a CSS class block, further increasing compression.
## 0.1.10 (2026-05-17)

### Added

- New `theme.keep_prior_overrides: bool` flag (default `false`); set `true` to preserve prior overrides across a named-theme switch.
- New built-in `dark` named theme (One Dark-inspired palette).
- New built-in `compact` named theme (denser spacings and smaller fonts).
- New `theme.commit_stroke_color` field for the commit-dot outline (default `"white"`).
- New `gitsvg schema themes` and `gitsvg schema theme <name>` commands for theme introspection.
- New shipped example `examples/10_named_themes.svg` previewing the built-in themes side-by-side.

### Changed

- **Breaking:** a `theme:` op with `name` now wipes prior `branch.color` overrides alongside `theme:` field overrides; pass `keep_prior_overrides: true` to preserve them.
- `theme:` font-size fields now accept floats.
## 0.1.9 (2026-05-16)

### Added

- Four new `theme:` op fields exposing previously-internal box-anchor values: `branch_pill_anchor`, `pull_request_pill_anchor`, `commit_label_anchor_before`, `commit_label_anchor_after`. Each is a two-element JSON array `[u, v]` in `[0, 1]²` saying where inside the un-rotated bounding box the world anchor point sits (and equivalently where rotation pivots); defaults reproduce the v0.1.8 per-orientation values, so default output is unchanged. Together with the label-angle fields from v0.1.8, non-zero label angles become practically usable for the first time.
## 0.1.8 (2026-05-16)

### Added

- New `theme.branch_label_angle` / `commit_label_angle` / `pull_request_label_angle` fields rotate the corresponding labels around their world anchor point (signed degrees, default `0°`); current anchor positions are tuned for un-rotated text, so visually-tuned angle/anchor pairings arrive with later named themes.
## 0.1.7 (2026-05-16)

### Changed

- Pill and commit-label widths now use measured glyph metrics from `theme.label_font_family`'s fallback chain instead of a uniform per-character factor; existing diagrams may show small pixel shifts.
- Canvas auto-fit now covers long branch names in `lr` / `rl` (start-side margin grows to fit instead of overflowing) and correctly routes the `tb` branch-pill allowance to `margin_top` instead of `margin_bottom`.
- Default first non-main branch color swapped from blue-gray to green for a clearer contrast against the `main` palette entry.
- Horizontal-orientation default spacings (`lr` / `rl`) changed from `(50, 100)` to `(75, 75)` — symmetric reads better when commit labels sit above/below the branch line.
## 0.1.6 (2026-05-15)

### Added

- New `theme.orientation` field for diagram orientation: `bt` (bottom-to-top, default), `tb` (top-to-bottom), `lr` (left-to-right), or `rl` (right-to-left). Accepts case-insensitive short codes (including Mermaid's `TD` and CSS `ltr` / `rtl`), `_`- or `-`-separated long forms (e.g. `bottom_to_top`, `top-to-bottom`), and vernacular `top_down` / `bottom_up`. Per-orientation defaults resolve at theme-build time for spacings, margins, pill offsets, label offset, and guide overshoot.

### Changed

- **Breaking:** `branch.label_side` values rename from `"left"` / `"right"` to `"before"` / `"after"` — axis-index-relative, orientation-invariant on the layout side; the renderer maps to a pixel side per orientation. Migration: rename `"left"` → `"before"`, `"right"` → `"after"`.
- **Breaking:** the four `theme:` margin fields rename from axis-relative ratios to visual-side pixels: `margin_branch_axis_lower_in_lanes` → `margin_left`, `margin_branch_axis_upper_in_lanes` → `margin_right`, `margin_commit_axis_upper_in_rows` → `margin_top`, `margin_commit_axis_lower_in_rows` → `margin_bottom`. Migration: rename and convert each value to absolute pixels (multiply by the original anchor — `branch_spacing` for the lane fields, `commit_spacing` for the row fields). When left unset, defaults resolve per `theme.orientation`.
- Default `pull_request_dash` changed from `"6,4"` to `"2,6"` — airier distinction from solid arcs. Affects every diagram with an open pull request.
- Default `guide_overshoot_in_rows` (vertical orientations) changed from `0.2` to `0.25` — slightly longer guide tails. Affects every existing diagram. Horizontal orientations resolve to `0.5` to cover the asymmetric start-side margin.
## 0.1.5 (2026-05-14)

### Added

- Five new `theme:` op fields expose previously-internal visual constants for user customization: `guide_overshoot_in_rows`, `pill_padding_x_in_font_sizes`, `pill_padding_y_in_font_sizes`, `pill_corner_radius_in_font_sizes`, `label_line_padding_in_font_sizes`. Defaults reproduce today's pixel values; see the format spec for anchors.
- Two new validation error codes on the `theme:` op surface: `E218` (`branch_spacing` / `commit_spacing` must be `> 0`), `E219` (font sizes must be `> 0`).

### Changed

- **Breaking:** the `canvas:` op is renamed `grid:` and trimmed to its two slot-count fields (`n_commits`, `n_branches`); spacings and margins move exclusively to `theme:`. Migration: rename `"op": "canvas"` to `"op": "grid"`, and move any spacing/margin fields onto a `theme:` op (same field names).
- **Breaking:** six `theme:` op fields renamed and reparametrised as ratios of their grid anchor. The four margins (`margin_branch_axis_lower`, `margin_branch_axis_upper`, `margin_commit_axis_lower`, `margin_commit_axis_upper`) gain an `_in_lanes` (branch-axis) or `_in_rows` (commit-axis) suffix; `arc_corner_radius` → `arc_corner_radius_in_grid_units`; `label_offset` → `label_offset_branch_axis_in_lanes`. Migration: rename, then divide each value by its anchor — `branch_spacing` for `_in_lanes`, `commit_spacing` for `_in_rows`, or `min(branch_spacing, commit_spacing)` for `_in_grid_units`.
- **Breaking:** the two pill-offset fields each split into a signed two-axis ratio pair (positive = toward higher index on the named axis): `branch_name_pill_offset` → `branch_name_pill_offset_commit_axis_in_rows` (default `-0.5`) + `branch_name_pill_offset_branch_axis_in_lanes` (default `0.0`); same shape for `pull_request_pill_offset` (defaults `+0.5` and `0.0`).
- Cleanup of DTO shapes between pipeline stages `parse`, `layout`, and `render`, making `State` leaner and more single-purposed.
## 0.1.4 (2026-05-12)

### Added

- New `theme` op for applying presentational overrides (spacings, margins, font sizes, stroke widths, color palette, background) from JSONL. Each op patches the live theme; `"name": "default"` resets every field to the package defaults.
- `theme.colors` accepts a replacement branch-color palette dict.
- Optional full-canvas background color via `theme.background_color` (default unset = transparent).
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
- Render output now includes branch-name pills — colored rounded rectangles positioned below each branch's start point.
- Highlight visual: a commit with `highlight: true` now renders with an enlarged dot and a bold `msg` label.
- `canvas:` op honors all eight optional fields end-to-end; auto-fit kicks in for fields left unset.
- Auto-fit margins reserve room for the longest visible labels per side; pin via `canvas:` to opt out.
- Pinned-canvas overflow: when content exceeds pinned `n_commits`/`n_branches`, the excess is clipped by SVG default `overflow:hidden`.

### Changed

- Internal: rendering pipeline restructured into state → layout → renderer stages. No user-visible behavior change.

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
