# Contributing to gitsvg

Thanks for your interest in contributing.

## Security

Found a vulnerability? Please report it privately — see
[`SECURITY.md`](SECURITY.md). Do not open a public issue for it.

## Architecture

[`docs/architecture.md`](docs/architecture.md) is the canonical reference for the
package's pipeline shape and the architectural invariants that bind the codebase.
Read it before making structural changes — it covers the validate-and-render
flow (`parse → imports → state → layout → render`) and the conventions each
stage upholds.

## Dev setup

One-time setup on a fresh clone:

```bash
make dev-setup
```

This syncs dev dependencies via `uv` and installs pre-commit hooks.

## Common commands

```bash
make test            # Run the test suite (pytest)
make format          # Format and auto-fix with ruff
make lint            # Lint with ruff
make validate-local  # Validate every .gitsvg.jsonl under local/test_examples/
```

## Local example smoke test

`make validate-local` walks `local/test_examples/` recursively and
runs the full validate pipeline on every `*.gitsvg.jsonl` it finds.
The directory is gitignored — drop your own input files there if you
want to keep them out of the public repo while still being able to
smoke-test them with one command. The make target skips silently
when the directory is absent, so fresh clones work without any
local fixtures.

The synthetic corpus that ships with the repo (under
`tests/fixtures/inputs/`) covers the canonical happy and sad paths
via the `pytest` suite. `make validate-local` is the additional
developer-side regression guard for any private inputs you keep
locally.

## Branching

Branch names follow the pattern:

```
<prefix>/<NN>-<short-slug>
```

- **Prefix** -- one of `feat/`, `fix/`, `chore/`, `docs/`, `refactor/`,
  `test/`. CI rejects anything else.
- **NN** -- two-digit zero-padded sequence number, continuous across all
  branches in the project (substitutes for an issue number where one
  doesn't exist). Use the next free number; check `git branch -a` if
  unsure.
- **Slug** -- short kebab-case description, lowercase letters, digits,
  and hyphens only.

Examples: `chore/01-oss-scaffolding`, `feat/07-new-input-format`,
`fix/12-svg-render-crash`.

When a GitHub issue exists, its number replaces the sequence
(`feat/42-...`).

## Pull requests

PRs are merged into `main` via **squash merge only** (repo settings
disable merge commits and rebase merges). Each PR therefore produces
exactly one commit on `main`. The squash commit subject is the PR
title and the body is the PR body, so write both with care -- they
become the permanent history. The feature branch is deleted
automatically on merge.

## Commit messages

Subject line uses the same short-form prefixes as branches:

```
<prefix>: <imperative summary>
```

- **Prefix** -- `feat`, `fix`, `chore`, `docs`, `refactor`, `test`
  (matching the branch prefix is the common case but not required).
- **Summary** -- imperative mood, lowercase, no trailing period,
  ideally under 72 characters.

Examples:

```
feat: add yaml input parser
fix: handle empty branch list
chore: bump click to 8.3
docs: clarify input schema
```

The body (optional) explains *why*, not *what*. Wrap at ~72 characters.

## Changelog

Add an entry under the appropriate category in the `## Unreleased` section
of [`CHANGELOG.md`](CHANGELOG.md) as part of your PR.

Changelog entries are **user-facing** — write them for someone deciding
whether to upgrade, not for someone reviewing the implementation. Focus on
what changed from the user's perspective.

**Keep each entry to a single line.** Avoid verbosity; omit internal details
(class names, wiring, refactors that don't affect behavior). Expand to a
second line only when a single line genuinely can't convey what the change
is about.
