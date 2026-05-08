# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Added

- `gitsvg schema` command: prints an index of all input operations with one-line descriptions; `gitsvg schema <op>` prints the JSON Schema for that op; `gitsvg schema --list-ops` prints a bare op-name list.
- `gitsvg errors` command: prints an index of all registered validation error codes; `gitsvg errors <code>` prints that code's long-form catalog entry; `gitsvg errors --list-codes` prints a bare code list. The catalog ships empty for now; entries are added as the validator gains error sites.
- `gitsvg validate <file>` command: parses a `.gitsvg.jsonl` input file line by line, runs per-op shape validation, and reports any errors with `file:line: [code] field: message` formatting. Pass `--json` for a structured `{ ok, errors }` report. Exits non-zero when validation fails. Import-resolution and end-of-file checks land in subsequent versions of the validator.
- `gitsvg validate` now runs per-op semantic validation in addition to shape validation. Branch existence, commit-id uniqueness, commit-id references, the `replaces:` 7-rule check, branch-root constraints, and remove-cascade behaviour all surface as structured errors with their own catalog codes.
- Error catalog now spans 23 entries: parse-phase (E001-E004), shape-phase (E100-E108), and semantic-phase (E200-E209). Each entry is browseable via `gitsvg errors <code>`.
- Import resolution: `gitsvg validate` now expands a leading `import` op into the imported file's ops before running shape and semantic checks. Cycle detection (on resolved absolute paths), depth-limit cap (1000), missing-file errors, and structural rules (at most one import, must be first) all surface as catalog codes E300-E304. Each parsed op carries `(file, line)` provenance, so errors against imported ops still point at the original file.
- End-of-file cross-reference validation: after applying every op, `gitsvg validate` walks the final state and flags branch roots and commit parents that point at commits that have since been removed (E400, E401). The rebuild pattern (remove + re-add with the same id) passes cleanly because the missing reference is restored before EOF. Final validator pipeline: parse → import-expand → state-apply → end-of-file check.

### Changed

### Deprecated

### Removed

- The placeholder `gitsvg render` command (shipped only with v0.0.1) is removed; rendering will return as part of v0.0.3.
- The `rich` dependency, which was unused in v0.0.1 scaffolding.

### Fixed

### Security

## 0.0.1 (2026-05-08)

### Added

- Initial placeholder release to reserve the PyPI name.
