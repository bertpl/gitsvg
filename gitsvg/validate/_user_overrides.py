"""`UserOverrides` — a record of what the input explicitly set.

The resolved-config consistency checks need to know not just the
*resolved* `Theme` but *what the user explicitly set, and where* — e.g.
E224 fires only when the user wrote `commit_row_mode: shared`, a fact
the resolved theme erases (table mode coerces it to `unique`).
`UserOverrides` carries exactly that, lifted off the transient
`ThemeBuilder` and the per-branch pins on `State`, so the checks
depend on neither.

It records *only what was set, and where* — never a resolved theme
value; resolved config stays on `Theme`.
"""

from dataclasses import dataclass
from typing import Any

from gitsvg.state import State
from gitsvg.theme import ThemeBuilder


@dataclass(frozen=True, slots=True)
class ThemeOverride:
    """One explicitly-set theme field: the value supplied and where it was set."""

    value: Any
    file: str | None
    line: int


@dataclass(frozen=True, slots=True)
class BranchPin:
    """One `branch_pos`-pinned branch: its name and the line that declared it."""

    name: str
    file: str | None
    line: int


@dataclass(frozen=True, slots=True)
class UserOverrides:
    """What the input explicitly set — theme-field overrides and branch pins.

    Attributes:
        theme_fields: Explicitly-set theme fields keyed by field name; each
            carries the set value and the `(file, line)` it was set on.
        branch_pins: The `branch_pos`-pinned branches, each carrying its name
            and the `(file, line)` of the `branch:` op that pinned it.
    """

    theme_fields: dict[str, ThemeOverride]
    branch_pins: tuple[BranchPin, ...]

    @classmethod
    def collect(cls, state: State, builder: ThemeBuilder) -> "UserOverrides":
        """Gather what was explicitly set off the applied state and the theme builder.

        Args:
            state: The fully-applied state, carrying per-branch pins.
            builder: The theme builder threaded through the apply pass,
                carrying the explicit `user_set` overrides and their lines.

        Returns:
            A frozen snapshot of what the input explicitly set.
        """
        theme_fields = {
            name: ThemeOverride(value, *builder.user_set_lines.get(name, (None, 0)))
            for name, value in builder.user_set.items()
        }
        branch_pins = tuple(
            BranchPin(branch.name, branch.declaration_file, branch.declaration_line)
            for branch in state.branches.values()
            if branch.branch_pos is not None
        )
        return cls(theme_fields=theme_fields, branch_pins=branch_pins)
