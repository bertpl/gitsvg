# Architecture invariants

The canonical record of architectural invariants that bind the
codebase. Each entry states the rule, the rationale, the enforcement
mechanism, and the version it locked in.

| # | Invariant | Locked in |
|---|---|---|
| 1 | Layout↔render boundary | v0.1.4 |
| 2 | Position/size field axis classification | v0.1.5 |

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

**Rule.** Every field on the architectural dataclasses (`Theme`,
every `Layout*` dataclass, `RenderCanvas`) carries a
`Classification:` line in its per-field docstring. Four classes:

- **`axis-symmetric`** — magnitude with no axis preference
  (radii, stroke widths, font sizes, char-width factors, paddings).
- **`axis-bound: <axis>`** — magnitude bound to a specific grid
  axis (`branch-axis` or `commit-axis`). Slot indices, slot
  counts, spacings, margins.
- **`direction-bound: <axis>, <direction>`** — magnitude with a
  baked-in direction along an axis. These are the orientation-leaky
  fields: they survive the bottom-to-top default but break under
  any rotation.
- **`not-applicable`** — field has no axis semantic (colours,
  fonts, IDs, names, message text, boolean flags).

**Rationale.** Classification surfaces orientation-leaky fields
at the docstring level rather than at rotation-bug time, and gives
downstream changes a checkable surface to reason against.

**Enforcement.** Meta-test in `tests/architecture/`. The test
walks the in-scope dataclasses and asserts every field has a
valid classification — adding a new field without one fails the
test. The test docstring is the canonical source for the
docstring grammar.

**Locked in:** v0.1.5.
