"""gitsvg/_shared/ — dependency-free primitives shared across pipeline stages.

The cross-cutting building blocks every stage imports one-way: the
presentational value-types (`value_types/`) and small stage-agnostic
helpers. This package depends on nothing else in `gitsvg` (enforced by
`tests/architecture/test_shared_is_leaf.py`), so it sits below
`file_format`, `theme`, `layout`, and `render` in the import graph and
carries no cycle risk. Private (`_`-prefixed): internal plumbing, not a
public API.
"""
