"""Bulk walker + input/output kind dispatch for `.gitsvg.jsonl` inputs.

Two flavors of CLI subcommand consume `.gitsvg.jsonl` input files:

- *Single-file mode* — `INPUT` is one file, `-o` is one output path.
- *Bulk mode* — `INPUT` is a directory, `-o` is a directory; the
  walker descends `INPUT` for `*.gitsvg.jsonl` files and writes one
  output per input under the mirrored subdirectory structure.

This module exposes the shared machinery so subcommands keep their
own bodies focused on the per-file action (write SVG, emit JSON,
etc.). The single entry point is `process_input`; the helpers
`walk_inputs`, `mirror_output_path`, and `run_bulk` are exposed for
tests and for direct reuse when a subcommand needs finer control.

Bulk-mode behavior: continue on per-file failures (a failing file
does not stop the walk), aggregate validation errors, print a
summary line at the end, and exit non-zero when at least one file
failed. Matches the shape of the local-only render / validate
walker scripts that preceded this module.
"""

from collections.abc import Callable
from pathlib import Path

import click

from gitsvg.errors import ValidationReport

_INPUT_GLOB = "*.gitsvg.jsonl"
_INPUT_SUFFIX = ".gitsvg.jsonl"

ProcessOne = Callable[[Path, Path], ValidationReport]
"""Per-file callback: validate + act on one input, return its report."""


# ==================================================================================================
#  Top-level dispatch
# ==================================================================================================
def process_input(
    input_path: Path,
    output_path: Path,
    output_ext: str,
    process_one: ProcessOne,
) -> int:
    """Dispatch a CLI subcommand to single-file or bulk mode.

    Inspects `input_path` to decide the mode, validates that
    `output_path`'s type matches, then either invokes `process_one`
    once (single-file mode) or recursively walks the input tree
    and invokes it per file (bulk mode). Writes any validation
    errors to stderr,
    prints a summary line in bulk mode, and returns the exit code
    the CLI subcommand should propagate.

    Args:
        input_path: Path passed to the subcommand's `INPUT`
            argument. Must exist.
        output_path: Path passed to the subcommand's `-o` option.
            May or may not exist; its type (file vs directory) must
            match `input_path`'s.
        output_ext: Stem suffix used for mirrored outputs in bulk
            mode (e.g. `".svg"`, `".state.json"`). Replaces the
            `.gitsvg.jsonl` suffix on the input filename.
        process_one: Per-file callback. Receives the input path
            and the output path. Returns a `ValidationReport`;
            clean = success. Must not print to stderr — for inputs
            routed through this function, validation errors are written
            to stderr here so bulk mode can aggregate.

    Returns:
        Exit code suitable for `sys.exit()`: 0 on full success, 1
        when any file failed validation, 2 on an input/output kind
        mismatch (file vs directory).
    """
    if input_path.is_dir():
        if output_path.exists() and not output_path.is_dir():
            click.echo(
                f"INPUT is a directory but OUTPUT exists as a file: {output_path}",
                err=True,
            )
            return 2
        return run_bulk(input_path, output_path, output_ext, process_one)

    if output_path.exists() and output_path.is_dir():
        click.echo(
            f"INPUT is a file but OUTPUT exists as a directory: {output_path}",
            err=True,
        )
        return 2

    report = process_one(input_path, output_path)
    if not report.is_clean():
        for err in report.errors:
            click.echo(err.format(), err=True)
        return 1
    return 0


# ==================================================================================================
#  Bulk walking
# ==================================================================================================
def run_bulk(
    input_root: Path,
    output_root: Path,
    output_ext: str,
    process_one: ProcessOne,
) -> int:
    """Recursively walk `input_root` for `*.gitsvg.jsonl` and process each file.

    Each input maps to a mirrored output path under `output_root`
    with the `.gitsvg.jsonl` suffix replaced by `output_ext`. The
    walker creates output parent directories on demand, dispatches
    to `process_one`, aggregates per-file failures, and prints a
    summary line. Continue-on-error: a failing file does not stop
    the walk.

    Args:
        input_root: Directory to walk. May be missing or empty —
            both cases print a friendly notice and return 0.
        output_root: Directory to mirror outputs into. Created if
            absent.
        output_ext: Suffix appended to each input's stem
            (e.g. `".svg"`).
        process_one: Per-file callback returning a
            `ValidationReport`.

    Returns:
        Exit code: 0 when every file processed cleanly (or the
        input tree is empty), 1 when at least one file failed.
    """
    inputs = walk_inputs(input_root)
    if not inputs:
        click.echo(f"no {_INPUT_GLOB} files found under {input_root}", err=True)
        return 0

    failures: list[tuple[Path, ValidationReport]] = []
    for input_path in inputs:
        output_path = mirror_output_path(input_path, input_root, output_root, output_ext)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        report = process_one(input_path, output_path)
        if not report.is_clean():
            failures.append((input_path, report))

    click.echo(f"{len(inputs) - len(failures)}/{len(inputs)} files processed cleanly", err=True)
    if failures:
        click.echo(f"\n{len(failures)} failure(s):", err=True)
        for input_path, report in failures:
            click.echo(f"\n--- {input_path} ---", err=True)
            for err in report.errors:
                click.echo(f"  {err.format()}", err=True)
        return 1
    return 0


def walk_inputs(input_root: Path) -> list[Path]:
    """Return a sorted list of `*.gitsvg.jsonl` paths recursively under `input_root`.

    Args:
        input_root: Directory to recursively walk. Missing directories
            produce an empty list (no error).

    Returns:
        Sorted list of matching paths. Empty if the directory is
        absent or contains no matching files.
    """
    if not input_root.is_dir():
        return []
    return sorted(input_root.rglob(_INPUT_GLOB))


def mirror_output_path(
    input_path: Path,
    input_root: Path,
    output_root: Path,
    output_ext: str,
) -> Path:
    """Compute the mirrored output path for one input file.

    Strips the `.gitsvg.jsonl` suffix from the input's filename,
    appends `output_ext`, and reattaches the input's subdirectory
    structure relative to `input_root` under `output_root`.

    Args:
        input_path: A `.gitsvg.jsonl` file somewhere under
            `input_root`.
        input_root: The bulk walk's input root directory.
        output_root: The bulk walk's output root directory.
        output_ext: Suffix to append to the input's stem (e.g.
            `".svg"`, `".state.json"`).

    Returns:
        The output path the per-file callback should write to.

    Raises:
        ValueError: If `input_path` is not under `input_root` or
            does not have the `.gitsvg.jsonl` suffix.
    """
    relative = input_path.relative_to(input_root)
    if not input_path.name.endswith(_INPUT_SUFFIX):
        raise ValueError(f"expected a {_INPUT_SUFFIX} input, got {input_path.name!r}")
    stem = input_path.name[: -len(_INPUT_SUFFIX)]
    return output_root / relative.parent / (stem + output_ext)
