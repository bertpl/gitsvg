"""`ThemeBuilder` — transient accumulator threaded through the apply pass.

A `Theme` is constructed from three independent inputs that the apply
pass collects op by op:

- `theme_cls`: the concrete `Theme` subclass selected by the most
  recent `theme: name=...` op. Starts as `DefaultTheme` and gets
  swapped when a named-theme reset arrives.
- `user_set`: explicitly-set theme-field values, accumulated from
  every `theme:` op without a `name:` field. The dict only holds
  fields the user actually touched; absent keys fall through to the
  subclass's `_resolve_<field>` classmethod at build time.
- `branch_color_overrides`: state-derived per-branch hex colours,
  accumulated from `branch:` ops carrying `color`, removed when a
  `remove:` op drops the branch.

`ThemeBuilder` is the mutable container that holds these three
pieces while the apply pass iterates. `apply_theme_op`,
`apply_branch_op`, and `apply_remove_op` mutate it; every other op
handler receives it for signature uniformity but leaves it alone. The
state engine calls `builder.build()` once at end-of-apply to produce
the resolved `Theme` instance.

`Theme.build(user_set)` factories live on the model itself (so each
subclass owns its default-resolution logic); the builder accumulates
across the apply pass and dispatches to the chosen `theme_cls`.
"""

from dataclasses import dataclass, field
from typing import Any

from gitsvg.theme._default_theme import DefaultTheme
from gitsvg.theme._theme import Theme


@dataclass(slots=True)
class ThemeBuilder:
    """Transient accumulator for theme construction during the apply pass.

    Attributes:
        theme_cls: The concrete `Theme` subclass to build with.
            Starts at `DefaultTheme`; reassigned by a `theme:` op that
            carries a `name:` field (which also clears `user_set`).
        user_set: Mapping from theme-field name to the value the user
            explicitly supplied via a `theme:` op (without `name:`).
            Fields the user didn't touch are absent.
        branch_color_overrides: Hex-colour overrides keyed by
            `BranchState.id`, populated as `branch:` ops with `color`
            apply and pruned when their branch is removed.
    """

    theme_cls: type[Theme] = DefaultTheme
    user_set: dict[str, Any] = field(default_factory=dict)
    branch_color_overrides: dict[str, str] = field(default_factory=dict)

    def reset_to(self, theme_cls: type[Theme]) -> None:
        """Swap to a different concrete theme and discard accumulated user overrides.

        Invoked by the `theme:` op handler when the op carries a
        `name:` field. The named-theme replacement is total — any
        explicit fields from earlier ops on the same `theme:` cascade
        are dropped. `branch_color_overrides` is unaffected (state-
        derived, not user input on the `theme:` op).

        Args:
            theme_cls: The new concrete `Theme` subclass to build with.
        """
        self.theme_cls = theme_cls
        self.user_set = {}

    def build(self) -> Theme:
        """Resolve a fully-populated `Theme` and attach state-derived overrides.

        Calls `self.theme_cls.build(self.user_set)` to produce the
        resolved theme; then writes the accumulated
        `branch_color_overrides` onto the result. Called once by the
        state engine at end-of-apply.

        Returns:
            The fully-populated `Theme`.
        """
        theme = self.theme_cls.build(self.user_set)
        theme.branch_color_overrides = dict(self.branch_color_overrides)
        return theme
