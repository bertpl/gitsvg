"""Meta-test enforcing per-field axis classification on architectural dataclasses.

Walks `Theme`, every `Layout*` dataclass, and `RenderCanvas`, asserting
every field carries a per-field docstring with a valid `Classification:`
line. Adding a new field without a classification fails this test —
the author is then forced to declare whether the new field is
`axis-symmetric`, `axis-bound: <axis>`, `direction-bound: <axis>,
<direction>`, or genuinely `not-applicable`.

Backs invariant #2 in `docs/architecture.md` (position/size field axis
classification, locked in v0.1.5).
"""

import ast
import dataclasses
import inspect
import re
from typing import Any

import pytest

from gitsvg._theme import Theme
from gitsvg.layout import Layout, LayoutArc, LayoutBranch, LayoutCommit, LayoutGrid, LayoutGuide, LayoutPullRequest
from gitsvg.render._canvas import RenderCanvas

# ==================================================================================================
#  Classification grammar
# ==================================================================================================
# The line must look like one of:
#   Classification: axis-symmetric.
#   Classification: axis-bound: branch-axis.
#   Classification: axis-bound: commit-axis (slot index).
#   Classification: direction-bound: branch-axis, set by `label_side`.
#   Classification: direction-bound: commit-axis, toward lower index.
#   Classification: not-applicable.
# Trailing free-text after the class name is ignored — it carries
# human-readable context.
_CLASSIFICATION_RE = re.compile(
    r"Classification:\s+("
    r"axis-symmetric"
    r"|axis-bound:\s+(branch-axis|commit-axis)"
    r"|direction-bound:\s+(branch-axis|commit-axis),\s+.+"
    r"|not-applicable"
    r")"
)


# ==================================================================================================
#  Classes the meta-test covers
# ==================================================================================================
_CLASSES_UNDER_TEST: list[type] = [
    Theme,
    LayoutGrid,
    LayoutBranch,
    LayoutCommit,
    LayoutArc,
    LayoutGuide,
    LayoutPullRequest,
    Layout,
    RenderCanvas,
]


# ==================================================================================================
#  Per-field docstring extraction
# ==================================================================================================
def _field_docstrings(cls: type) -> dict[str, str | None]:
    """Return a `{field_name: docstring or None}` mapping for a dataclass.

    Parses the class source via `ast`, walking the body for
    `AnnAssign` nodes (annotated field declarations) and pairing each
    with the immediately following `Expr(Constant(str))` if present —
    the standard Python convention for per-field docstrings.

    Args:
        cls: A dataclass to introspect.

    Returns:
        A mapping from each declared field name to its trailing
        per-field docstring, or `None` when no docstring follows.
    """
    source = inspect.getsource(cls)
    # `inspect.getsource` may include leading indentation for nested
    # classes. `textwrap.dedent` is unnecessary here because all our
    # classes are module-level, but `ast.parse` handles either case.
    tree = ast.parse(source)
    class_def = tree.body[0]
    assert isinstance(class_def, ast.ClassDef), f"Expected ClassDef, got {type(class_def).__name__}"

    docstrings: dict[str, str | None] = {}
    body = class_def.body
    for index, node in enumerate(body):
        if not isinstance(node, ast.AnnAssign):
            continue
        if not isinstance(node.target, ast.Name):
            continue
        field_name = node.target.id
        docstring: str | None = None
        if index + 1 < len(body):
            next_node = body[index + 1]
            if (
                isinstance(next_node, ast.Expr)
                and isinstance(next_node.value, ast.Constant)
                and isinstance(next_node.value.value, str)
            ):
                docstring = next_node.value.value
        docstrings[field_name] = docstring
    return docstrings


# ==================================================================================================
#  Coverage check
# ==================================================================================================
@pytest.mark.parametrize("cls", _CLASSES_UNDER_TEST, ids=lambda c: c.__name__)
def test_every_field_has_a_classified_docstring(cls: type[Any]) -> None:
    """Every declared field on `cls` must have a per-field docstring containing a valid `Classification:` line."""
    # --- arrange ----------------------
    expected_field_names = {f.name for f in dataclasses.fields(cls)}
    docstrings = _field_docstrings(cls)

    # --- act / assert -----------------
    missing_fields = expected_field_names - set(docstrings.keys())
    assert not missing_fields, (
        f"{cls.__name__}: AST walk did not find these declared fields: {sorted(missing_fields)}. "
        "Likely cause: a field was added without a per-field docstring (the trailing string literal)."
    )

    failures: list[str] = []
    for field_name in sorted(expected_field_names):
        docstring = docstrings[field_name]
        if docstring is None:
            failures.append(f"  {cls.__name__}.{field_name}: no per-field docstring")
            continue
        if not _CLASSIFICATION_RE.search(docstring):
            failures.append(
                f"  {cls.__name__}.{field_name}: docstring lacks a valid `Classification:` line.\n"
                f"    docstring: {docstring!r}"
            )

    if failures:
        pytest.fail(
            "Missing or malformed `Classification:` lines:\n"
            + "\n".join(failures)
            + "\n\nSee `docs/architecture.md` invariant #2 for the taxonomy."
        )


# ==================================================================================================
#  Self-tests on the regex
# ==================================================================================================
@pytest.mark.parametrize(
    "docstring",
    [
        "x. Classification: axis-symmetric.",
        "x. Classification: axis-bound: branch-axis.",
        "x. Classification: axis-bound: commit-axis (slot index).",
        "x. Classification: direction-bound: branch-axis, set by `label_side`.",
        "x. Classification: direction-bound: commit-axis, toward lower index.",
        "x. Classification: not-applicable.",
        "Multi-line.\n\nClassification: axis-symmetric.\n",
    ],
)
def test_classification_regex_accepts_valid_examples(docstring: str) -> None:
    """The classification regex matches every documented valid form."""
    # --- act / assert -----------------
    assert _CLASSIFICATION_RE.search(docstring), f"regex rejected: {docstring!r}"


@pytest.mark.parametrize(
    "docstring",
    [
        "no classification at all",
        "Classification: something-else.",
        "Classification: axis-bound: invalid-axis.",
        "Classification: direction-bound: branch-axis.",  # missing direction phrase
        "Classification: direction-bound.",  # missing axis
    ],
)
def test_classification_regex_rejects_invalid_examples(docstring: str) -> None:
    """The classification regex rejects malformed or missing classifications."""
    # --- act / assert -----------------
    assert not _CLASSIFICATION_RE.search(docstring), f"regex incorrectly accepted: {docstring!r}"
