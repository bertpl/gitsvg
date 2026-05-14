# Architecture invariants

The canonical record of architectural invariants that bind the
codebase. Each entry states the rule, the rationale, the enforcement
mechanism, and the version it locked in.

| # | Invariant | Locked in |
|---|---|---|
| 1 | Layout↔render boundary | v0.1.4 |
| 2 | Position/size field axis classification | v0.1.5 |
| 4 | Structural-vs-perceptual cleavage | v0.1.5 |
| 5 | Geometry-module routing for coordinate math | v0.1.5 |
| 6 | Op-to-consumer boundary | v0.1.5 |

## 1. Layout↔render boundary

**Rule.** The layout engine produces an integer-grid intermediate
representation; the renderer reads the resolved `Theme` and converts
grid positions to pixel coordinates. No field crosses the boundary
in the other direction. Layout output carries no pixel coordinates,
colours, fonts, strokes, or opacities; presentational state never
flows back into layout.

**Rationale.** Layout strategies (declaration-order assignment,
lane-reuse, future orientations) and theme variants (light/dark,
custom palettes, future orientation) vary independently. Keeping
each side oblivious to the other lets either evolve without
coupling.

**Enforcement.** Code-review discipline. Pixel/colour/font fields
appearing on a `Layout*` type are the trigger for review pushback.

**Locked in:** v0.1.4.

## 2. Position/size field axis classification

**Rule.** Every position/size field on `Theme`, on any `Layout*`
dataclass, and on `RenderCanvas` carries a trailing comment
naming its axis classification. Three classes:

- **`axis-symmetric`** — magnitude with no axis preference
  (radii, stroke widths, font sizes, paddings).
- **`axis-bound: <axis>`** — magnitude bound to a specific grid
  axis (`branch-axis` or `commit-axis`). Slot indices, slot
  counts, spacings, margins.
- **`direction-bound: <axis>, <direction>`** — magnitude with a
  baked-in direction along an axis. These are the orientation-leaky
  fields: they survive the bottom-to-top default but break under
  any rotation.

Non-position/size fields (colours, fonts, IDs, names, booleans)
carry no comment.

**Rationale.** Surfaces orientation-leaky fields at the field
declaration so a reader spots them without rendering at rotation
or running the code.

**Enforcement.** Best-effort convention, code-review discipline.
No test enforces presence — a missing classification on a new
position/size field is a review nit, not a build break.

**Locked in:** v0.1.5.

## 4. Structural-vs-perceptual cleavage

**Rule.** Fields with a natural anchor are stored as ratios of that
anchor. The field name carries a suffix naming the anchor:

- `_in_lanes` → `branch_spacing`
- `_in_rows` → `commit_spacing`
- `_in_grid_units` → `min(branch_spacing, commit_spacing)`
- `_in_font_sizes` → the relevant font_size field

**Rationale.** Tweaking a spacing or font size then rescales
everything anchored to it proportionally.

**Locked in:** v0.1.5.

## 5. Geometry-module routing for coordinate math

**Rule.** Every coordinate computation in render-side code routes
through the geometry module (`gitsvg/render/_geometry.py`).
Primitives never assemble coordinates inline — they call
`branch_axis_to_x`, `commit_axis_to_y`, `offset_position`,
`branch_guide_endpoints`, etc. The arithmetic that turns slot
indices and theme offsets into SVG pixel coordinates lives in
exactly one place.

**Rationale.** Inline `y + theme.<offset>` and `canvas.height -
canvas.margin_… ± const` arithmetic at the call site couples
every primitive to the BT screen-direction convention. Routing
through helpers means a future orientation rotation lives entirely
inside the geometry module — primitives only know about slot
indices and axis-relative offsets.

**Enforcement.** Code-review discipline. Pixel arithmetic on
`canvas.*` or theme spacing/margin fields appearing inside a
`_primitives/*.py` module is the trigger for review pushback.
Local primitive geometry (pill width/height + centring on the
anchor; label-stack vertical centring; arc segment + sweep math)
stays in the primitives — those are not coordinate transforms.

**Locked in:** v0.1.5.

## 6. Op-to-consumer boundary

**Rule.** Layout-engine inputs and renderer inputs live on distinct
ops. The `grid:` op carries the layout extent (`n_commits`,
`n_branches`); the `theme:` op carries every pixel-side concern
(spacings, margins, fonts, colours, strokes, opacities). No field
appears on both ops, and no field on `state.grid` flows into the
resolved theme.

**Rationale.** Spacing and margin had previously lived on both
the `canvas:` op and the `theme:` op, with the canvas op winning
(specific over general). The duplication leaked the layout↔render
boundary back into the JSONL surface and forced renderers and
authors alike to know the precedence rule. Splitting the
`canvas:` op into a slot-counts-only `grid:` op + a theme-only
spacing/margin surface restores invariant #1 at the user-visible
op level: each op feeds exactly one consumer.

**Enforcement.** Code-review discipline. The `GridOp` model
(`gitsvg/file_format/ops/impl/_grid.py`) carries only the two
slot-count fields; adding a spacing/margin field there is the
trigger for review pushback. The `build_theme` adapter
(`gitsvg/render/_theme.py`) does not import `state.grid` at all.

**Locked in:** v0.1.5.
