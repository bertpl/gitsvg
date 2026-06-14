"""Tests for the import resolver — happy paths, cycles, depth, missing files,
malformed import position, path sandboxing, and in-memory-input rejection."""

import json
import os
from pathlib import Path

import pytest

from gitsvg.errors import ValidationReport
from gitsvg.file_format.ops import BranchOp, CommitOp
from gitsvg.imports import resolve_imports
from gitsvg.parse import parse_jsonl_file


def _resolve(file: Path, *, depth_limit: int = 1000) -> tuple[list, ValidationReport]:
    """Parse `file` and resolve its imports, returning the expanded ops + report."""
    parsed, report = parse_jsonl_file(file)
    expanded = resolve_imports(parsed, file=file, report=report, depth_limit=depth_limit)
    return expanded, report


# ==================================================================================================
#  Happy path
# ==================================================================================================
def test_no_import_returns_input_unchanged(tmp_path: Path) -> None:
    # --- arrange ----------------------
    file = tmp_path / "a.jsonl"
    file.write_text('{"op": "branch", "name": "main"}\n')

    # --- act --------------------------
    expanded, report = _resolve(file)

    # --- assert -----------------------
    assert report.is_clean()
    assert len(expanded) == 1
    assert isinstance(expanded[0].op, BranchOp)


def test_simple_import_inlines_predecessor(tmp_path: Path) -> None:
    # --- arrange ----------------------
    base = tmp_path / "base.jsonl"
    base.write_text('{"op": "branch", "name": "main"}\n{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n')
    derived = tmp_path / "derived.jsonl"
    derived.write_text('{"op": "import", "path": "./base.jsonl"}\n{"op": "commit", "branch": "main", "msg": "y"}\n')

    # --- act --------------------------
    expanded, report = _resolve(derived)

    # --- assert -----------------------
    assert report.is_clean()
    assert [type(p.op).__name__ for p in expanded] == ["BranchOp", "CommitOp", "CommitOp"]
    # Source locations should point at the original files
    assert expanded[0].file == str(base.resolve())
    assert expanded[2].file == str(derived)


def test_import_chain_three_levels_deep(tmp_path: Path) -> None:
    # --- arrange ----------------------
    a = tmp_path / "a.jsonl"
    a.write_text('{"op": "branch", "name": "main"}\n')
    b = tmp_path / "b.jsonl"
    b.write_text('{"op": "import", "path": "./a.jsonl"}\n{"op": "commit", "branch": "main", "id": "c1", "msg": "b"}\n')
    c = tmp_path / "c.jsonl"
    c.write_text('{"op": "import", "path": "./b.jsonl"}\n{"op": "commit", "branch": "main", "id": "c2", "msg": "c"}\n')

    # --- act --------------------------
    expanded, report = _resolve(c)

    # --- assert -----------------------
    assert report.is_clean()
    assert [type(p.op).__name__ for p in expanded] == ["BranchOp", "CommitOp", "CommitOp"]


def test_file_with_only_import_op_is_valid(tmp_path: Path) -> None:
    """A 'hold' frame: file is just an import, expansion equals the imported file."""
    # --- arrange ----------------------
    base = tmp_path / "base.jsonl"
    base.write_text('{"op": "branch", "name": "main"}\n')
    hold = tmp_path / "hold.jsonl"
    hold.write_text('{"op": "import", "path": "./base.jsonl"}\n')

    # --- act --------------------------
    expanded, report = _resolve(hold)

    # --- assert -----------------------
    assert report.is_clean()
    assert len(expanded) == 1
    assert isinstance(expanded[0].op, BranchOp)


# ==================================================================================================
#  Cycles (E300)
# ==================================================================================================
def test_self_cycle_emits_e300(tmp_path: Path) -> None:
    # --- arrange ----------------------
    file = tmp_path / "self.jsonl"
    file.write_text('{"op": "import", "path": "./self.jsonl"}\n')

    # --- act --------------------------
    _, report = _resolve(file)

    # --- assert -----------------------
    assert [e.code for e in report.errors] == ["E300"]


def test_mutual_cycle_emits_e300(tmp_path: Path) -> None:
    # --- arrange ----------------------
    a = tmp_path / "a.jsonl"
    b = tmp_path / "b.jsonl"
    a.write_text('{"op": "import", "path": "./b.jsonl"}\n')
    b.write_text('{"op": "import", "path": "./a.jsonl"}\n')

    # --- act --------------------------
    _, report = _resolve(a)

    # --- assert -----------------------
    assert [e.code for e in report.errors] == ["E300"]


def test_cycle_via_relative_paths_resolves_to_same_file(tmp_path: Path) -> None:
    """Relative paths that point at the same absolute file are still a cycle."""
    # --- arrange ----------------------
    sub = tmp_path / "sub"
    sub.mkdir()
    a = tmp_path / "a.jsonl"
    b = sub / "b.jsonl"
    a.write_text('{"op": "import", "path": "./sub/b.jsonl"}\n')
    b.write_text('{"op": "import", "path": "../a.jsonl"}\n')

    # --- act --------------------------
    _, report = _resolve(a)

    # --- assert -----------------------
    assert [e.code for e in report.errors] == ["E300"]


# ==================================================================================================
#  Depth limit (E301)
# ==================================================================================================
def test_depth_limit_exceeded_emits_e301(tmp_path: Path) -> None:
    # --- arrange ----------------------
    # Build a chain a -> b -> c -> d
    files = ["a.jsonl", "b.jsonl", "c.jsonl", "d.jsonl"]
    for i, name in enumerate(files):
        target = tmp_path / name
        if i + 1 < len(files):
            target.write_text(f'{{"op": "import", "path": "./{files[i + 1]}"}}\n')
        else:
            target.write_text('{"op": "branch", "name": "main"}\n')

    # --- act --------------------------
    _, report = _resolve(tmp_path / "a.jsonl", depth_limit=2)

    # --- assert -----------------------
    assert any(e.code == "E301" for e in report.errors)


# ==================================================================================================
#  Missing file (E302)
# ==================================================================================================
def test_missing_imported_file_emits_e302(tmp_path: Path) -> None:
    # --- arrange ----------------------
    file = tmp_path / "main.jsonl"
    file.write_text('{"op": "import", "path": "./does-not-exist.jsonl"}\n')

    # --- act --------------------------
    _, report = _resolve(file)

    # --- assert -----------------------
    assert [e.code for e in report.errors] == ["E302"]


# ==================================================================================================
#  Multiple imports (E303)
# ==================================================================================================
def test_multiple_imports_emits_e303_for_each_extra(tmp_path: Path) -> None:
    # --- arrange ----------------------
    base = tmp_path / "base.jsonl"
    base.write_text('{"op": "branch", "name": "main"}\n')
    extra = tmp_path / "extra.jsonl"
    extra.write_text('{"op": "branch", "name": "feat", "from_branch": "main"}\n')
    main = tmp_path / "main.jsonl"
    main.write_text('{"op": "import", "path": "./base.jsonl"}\n{"op": "import", "path": "./extra.jsonl"}\n')

    # --- act --------------------------
    _, report = _resolve(main)

    # --- assert -----------------------
    codes = [e.code for e in report.errors]
    assert codes.count("E303") == 1


# ==================================================================================================
#  Import not first (E304)
# ==================================================================================================
def test_import_not_first_emits_e304_and_drops_import(tmp_path: Path) -> None:
    # --- arrange ----------------------
    base = tmp_path / "base.jsonl"
    base.write_text('{"op": "branch", "name": "main"}\n')
    main = tmp_path / "main.jsonl"
    main.write_text('{"op": "branch", "name": "main"}\n{"op": "import", "path": "./base.jsonl"}\n')

    # --- act --------------------------
    expanded, report = _resolve(main)

    # --- assert -----------------------
    assert [e.code for e in report.errors] == ["E304"]
    # Import was dropped; only the branch op remains.
    assert len(expanded) == 1
    assert isinstance(expanded[0].op, BranchOp)


# ==================================================================================================
#  Imported file's own errors flow through
# ==================================================================================================
def test_imported_file_parse_errors_surface_in_report(tmp_path: Path) -> None:
    # --- arrange ----------------------
    bad = tmp_path / "bad.jsonl"
    bad.write_text("{not json}\n")
    main = tmp_path / "main.jsonl"
    main.write_text('{"op": "import", "path": "./bad.jsonl"}\n')

    # --- act --------------------------
    _, report = _resolve(main)

    # --- assert -----------------------
    # The imported file's E001 makes it through.
    assert any(e.code == "E001" for e in report.errors)


# ==================================================================================================
#  Path sandbox (E305)
# ==================================================================================================
def test_parent_escape_emits_e305_without_reading_the_file(tmp_path: Path) -> None:
    """A `../` path out of the top-level file's directory is rejected before any read."""
    # --- arrange ----------------------
    outside = tmp_path / "outside.jsonl"
    outside.write_text('{"op": "branch", "name": "secret-branch"}\n')
    sub = tmp_path / "sub"
    sub.mkdir()
    main = sub / "main.jsonl"
    main.write_text('{"op": "import", "path": "../outside.jsonl"}\n{"op": "branch", "name": "main"}\n')

    # --- act --------------------------
    expanded, report = _resolve(main)

    # --- assert -----------------------
    # E305 only — no E302/E001 from the out-of-tree file, i.e. no read happened.
    assert [e.code for e in report.errors] == ["E305"]
    assert all(not isinstance(p.op, BranchOp) or p.op.name != "secret-branch" for p in expanded)
    # The message names the requested path, never the resolved target.
    assert "../outside.jsonl" in report.errors[0].message
    assert str(outside.resolve()) not in report.errors[0].message


def test_absolute_path_emits_e305_even_inside_the_root(tmp_path: Path) -> None:
    """Absolute paths are rejected outright, even when they point inside the root."""
    # --- arrange ----------------------
    base = tmp_path / "base.jsonl"
    base.write_text('{"op": "branch", "name": "main"}\n')
    main = tmp_path / "main.jsonl"
    # Build via json.dumps so the absolute path is JSON-escaped — on Windows
    # it contains backslashes that would otherwise be invalid JSON escapes.
    main.write_text(json.dumps({"op": "import", "path": str(base.resolve())}) + "\n")

    # --- act --------------------------
    expanded, report = _resolve(main)

    # --- assert -----------------------
    assert [e.code for e in report.errors] == ["E305"]
    assert expanded == []


def test_nested_import_escape_emits_e305(tmp_path: Path) -> None:
    """Containment is checked against the *top-level* file's directory for the whole chain."""
    # --- arrange ----------------------
    outside = tmp_path / "outside.jsonl"
    outside.write_text('{"op": "branch", "name": "main"}\n')
    sub = tmp_path / "sub"
    sub.mkdir()
    inner = sub / "inner.jsonl"
    inner.write_text('{"op": "import", "path": "../outside.jsonl"}\n')
    main = sub / "main.jsonl"
    main.write_text('{"op": "import", "path": "./inner.jsonl"}\n')

    # --- act --------------------------
    _, report = _resolve(main)

    # --- assert -----------------------
    assert [e.code for e in report.errors] == ["E305"]


def test_descent_below_the_root_is_allowed(tmp_path: Path) -> None:
    """A subdirectory import stays inside the root and resolves normally."""
    # --- arrange ----------------------
    shared = tmp_path / "shared"
    shared.mkdir()
    base = shared / "base.jsonl"
    base.write_text('{"op": "branch", "name": "main"}\n')
    main = tmp_path / "main.jsonl"
    main.write_text('{"op": "import", "path": "./shared/base.jsonl"}\n')

    # --- act --------------------------
    expanded, report = _resolve(main)

    # --- assert -----------------------
    assert report.is_clean()
    assert len(expanded) == 1


@pytest.mark.skipif(os.name == "nt", reason="symlink creation needs privileges on Windows")
def test_symlink_escape_emits_e305(tmp_path: Path) -> None:
    """A within-root symlink resolving outside the root is an escape."""
    # --- arrange ----------------------
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()
    outside = outside_dir / "real.jsonl"
    outside.write_text('{"op": "branch", "name": "main"}\n')
    root = tmp_path / "root"
    root.mkdir()
    (root / "link.jsonl").symlink_to(outside)
    main = root / "main.jsonl"
    main.write_text('{"op": "import", "path": "./link.jsonl"}\n')

    # --- act --------------------------
    _, report = _resolve(main)

    # --- assert -----------------------
    assert [e.code for e in report.errors] == ["E305"]


# ==================================================================================================
#  In-memory input (E306)
# ==================================================================================================
def test_allow_imports_false_emits_e306_and_keeps_rest(tmp_path: Path) -> None:
    # --- arrange ----------------------
    base = tmp_path / "base.jsonl"
    base.write_text('{"op": "branch", "name": "main"}\n')
    main = tmp_path / "main.jsonl"
    main.write_text('{"op": "import", "path": "./base.jsonl"}\n{"op": "branch", "name": "feat"}\n')
    parsed, report = parse_jsonl_file(main)

    # --- act --------------------------
    expanded = resolve_imports(parsed, file=main, report=report, allow_imports=False)

    # --- assert -----------------------
    # The import is rejected without resolving (the target exists and is valid);
    # the ops after it survive.
    assert [e.code for e in report.errors] == ["E306"]
    assert len(expanded) == 1
    assert isinstance(expanded[0].op, BranchOp)
    assert expanded[0].op.name == "feat"


def test_imported_ops_point_at_their_source_file(tmp_path: Path) -> None:
    """Errors raised against an imported op should name the imported file."""
    # --- arrange ----------------------
    base = tmp_path / "base.jsonl"
    base.write_text('{"op": "branch", "name": "main"}\n{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n')
    derived = tmp_path / "derived.jsonl"
    derived.write_text('{"op": "import", "path": "./base.jsonl"}\n')

    # --- act --------------------------
    expanded, report = _resolve(derived)

    # --- assert -----------------------
    assert report.is_clean()
    base_resolved = str(base.resolve())
    assert all(p.file == base_resolved for p in expanded)
    assert isinstance(expanded[0].op, BranchOp)
    assert isinstance(expanded[1].op, CommitOp)
