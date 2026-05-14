"""Cross-cutting semantic checks fired during op application.

Each module exposes one or more validators that an op handler in the
sibling `_impl/` package invokes when its field set demands a
self-contained rule sweep beyond pydantic.
"""

from gitsvg.state._apply._checks._replaces import check_replaces_rules

__all__ = ["check_replaces_rules"]
