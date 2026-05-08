# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Added

- `gitsvg schema` command: prints an index of all input operations with one-line descriptions; `gitsvg schema <op>` prints the JSON Schema for that op; `gitsvg schema --list-ops` prints a bare op-name list.
- `gitsvg errors` command: prints an index of all registered validation error codes; `gitsvg errors <code>` prints that code's long-form catalog entry; `gitsvg errors --list-codes` prints a bare code list. The catalog ships empty for now; entries are added as the validator gains error sites.
- `gitsvg validate <file>` command: parses a `.gitsvg.jsonl` input file line by line, runs per-op shape validation, and reports any errors with `file:line: [code] field: message` formatting. Pass `--json` for a structured `{ ok, errors }` report. Exits non-zero when validation fails. State-engine, import-resolution, and end-of-file checks land in subsequent versions of the validator.
- Initial error catalog: 13 entries spanning parse-phase failures (E001-E004) and per-op shape failures (E100-E108). Each entry is browseable via `gitsvg errors <code>`.

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
