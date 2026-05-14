# Architecture invariants

This file is the canonical record of architectural invariants that
bind the codebase. Each invariant carries a one-line rule, the
rationale, the enforcement mechanism (meta-test, code-review
discipline, or both), and the version it locked in. Reading this
file at any commit shows what is actually binding in the codebase
at that point.

| # | Invariant | Locked in |
|---|---|---|
| 1 | Layout↔render boundary | v0.1.4 |
| 2 | Position/size field axis classification | v0.1.5 |

When the list grows past ~10 invariants (or any single section
becomes substantial), this file splits into `docs/architecture/`
with one file per invariant. Until then, a single file keeps the
overview cheap to read.

## 1. Layout↔render boundary

**Rule.** The layout engine produces an integer-grid intermediate
representation; the renderer reads the resolved `Theme` and
converts grid positions to pixel coordinates. No field crosses
the boundary in the other direction.

**Concretely:**

- Layout output (`Layout`, `LayoutGrid`, `LayoutBranch`,
  `LayoutCommit`, `LayoutArc`, `LayoutGuide`,
  `LayoutPullRequest` in `gitsvg/layout/_layout.py`) carries only
  integer slot indices, semantic identifiers, resolved label-side
  hints, and resolved hash strings. No pixel coordinates, colour
  values, font sizes, stroke widths, or opacities.
- Pixel-space concerns (canvas dimensions, spacings, margins,
  font sizes, colours, dashes, opacities) live exclusively on
  `Theme` (`gitsvg/_theme.py`) and are read only by the
  renderer (`gitsvg/render/`).
- The bridging adapter `build_theme(state)` in
  `gitsvg/render/_theme.py` is the single place state-mutated
  presentational data flows into the resolved theme. The layout
  engine never sees `Theme`.

**Rationale.** Different layout strategies (declaration-order
assignment, lane-reuse, future orientations) all produce the same
`Layout` schema, so the renderer stays oblivious. Different theme
variants (light/dark, custom palettes, future orientation) all read
the same layout output, so the layout engine stays oblivious.

**Enforcement.** Code-review discipline. The `Layout` dataclasses'
docstrings and `_theme.py`'s module docstring point readers at this
invariant; pixel/colour/font fields appearing on a `Layout*` type
are the trigger for review pushback.

**Locked in:** v0.1.4 (the refactor that introduced the boundary).
This invariant was backfilled into `docs/architecture.md` in
v0.1.5 PR1 — see git history for the original boundary work.

## 2. Position/size field axis classification

**Rule.** Every field on `Theme`, on any Layout dataclass, and
on `RenderCanvas` carries a documented classification in its
per-field docstring. Module-level position/size constants in
`gitsvg/render/` carry the same classification as a trailing
`# Classification: ...` comment on their declaration line. Four
classes — three for position/size, one catch-all:

- **`axis-symmetric`** — position/size magnitude with no axis
  preference (radii, stroke widths, font sizes, char-width
  factors, pill paddings).
- **`axis-bound: <axis>`** — position/size magnitude bound to a
  specific grid axis. `<axis>` is `branch-axis` or `commit-axis`.
  Slot indices, slot counts, spacings, and margins are axis-bound.
  Margins are unsigned distances; signed axis-bound fields use
  the convention in invariant #3 (added in v0.1.5 PR5).
- **`direction-bound: <axis>, <direction>`** — position/size
  magnitude with a baked-in direction along an axis (e.g. today's
  `branch_name_pill_offset` is direction-bound: commit-axis,
  toward lower index; today's `pull_request_pill_offset` is
  direction-bound: commit-axis, toward upper index). Direction-bound
  fields are the orientation-leaky ones — they survive the
  bottom-to-top default but break under any rotation.
- **`not-applicable`** — field has no axis semantic at all
  (colours, fonts, dashes, opacities, IDs, names, hash strings,
  message text, label-side hint strings, boolean flags). The
  meta-test enforces classification coverage uniformly across
  every field on each in-scope class; `not-applicable` is what
  every non-position/size field carries.

**Format inside docstrings.** A single line beginning with
`Classification:`. Examples:

```
Classification: axis-symmetric.
Classification: axis-bound: branch-axis.
Classification: axis-bound: commit-axis (slot index).
Classification: direction-bound: commit-axis, toward lower index.
Classification: not-applicable.
```

The `Classification:` prefix is what the meta-test greps for. The
trailing free-text after the class name (e.g. `(slot index)`,
`toward lower index`) carries human-readable context the test
ignores.

**Rationale.** The pre-classification surface mixed three
different things behind similar-looking names. Naming a field's
axis (or its direction along an axis) makes the orientation-leaky
ones visible at the docstring level rather than only at
rotation-bug time. The classification is the foundation every
later v0.1.5 PR builds on — it tells PR4 which fields ratio
(structural, axis-bound) vs stay pixels (perceptual,
axis-symmetric), and tells PR5 which fields split into the
two-axis signed form (the direction-bound ones).

**Enforcement.** Meta-test in `tests/architecture/`. The test
walks `Theme`, every Layout dataclass, and `RenderCanvas`, and
asserts every field's per-field docstring carries a
`Classification:` line matching one of the four classes. Adding
a new field without a classification fails the test, forcing the
author to think about whether the new field has an axis semantic
or is genuinely `not-applicable`.

Module-level position/size constants in `gitsvg/render/_metrics.py`
and `gitsvg/render/_primitives/` carry trailing
`# Classification: ...` comments for human consistency; the
meta-test does not enforce them (Python module-level constants
have no docstring slot to walk programmatically).

**Locked in:** v0.1.5 PR1.
