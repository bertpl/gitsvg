"""`ThemeBuilder` — transient accumulator threaded through the apply pass.

A `Theme` is constructed from four independent inputs that the apply
pass collects op by op:

- `theme_cls`: the concrete `Theme` subclass selected by the most
  recent `theme: name=...` op. Starts as `DefaultTheme` and gets
  reassigned (last write wins) whenever a `theme:` op sets `name`.
- `user_set`: explicitly-set theme-field values, accumulated from
  every `theme:` op without a `name:` field, and from any explicit
  fields on a `theme:` op that also sets `name`. The dict only holds
  fields the user actually touched; absent keys fall through to the
  subclass's `_resolve_<field>` classmethod at build time.
- `branch_color_overrides`: state-derived per-branch hex colors,
  accumulated from `branch:` ops carrying `color`, removed when a
  `remove:` op drops the branch.
- `branch_label_side_overrides`: state-derived per-branch label
  sides, accumulated from `branch:` ops carrying `label_side`,
  removed when a `remove:` op drops the branch.

`ThemeBuilder` is the mutable container that holds these four
pieces while the apply pass iterates. `apply_theme_op`,
`apply_branch_op`, and `apply_remove_op` mutate it; every other op
handler receives it for signature uniformity but leaves it alone. The
state engine calls `builder.build()` once at end-of-apply to produce
the resolved `Theme` instance.

The two write primitives — `set_theme_cls` and `clear_overrides` —
are independent so the apply handler can compose them per-op based on
the `keep_prior_overrides` flag: a `name` switch always calls
`set_theme_cls`, and additionally calls `clear_overrides` unless the
flag is set.

`Theme.build(user_set)` factories live on the model itself (so each
subclass owns its default-resolution logic); the builder accumulates
across the apply pass and dispatches to the chosen `theme_cls`.
"""

from dataclasses import dataclass, field
from typing import Any

from gitsvg._shared.value_types import LabelSide

from ._default_theme import DefaultTheme
from ._theme import Theme


@dataclass(slots=True)
class ThemeBuilder:
    """Transient accumulator for theme construction during the apply pass.

    Attributes:
        theme_cls: The concrete `Theme` subclass to build with.
            Starts at `DefaultTheme`; reassigned by `set_theme_cls`
            whenever a `theme:` op carries a `name:` field.
        user_set: Mapping from theme-field name to the value the user
            explicitly supplied via a `theme:` op. Fields the user
            didn't touch are absent.
        user_set_lines: Mapping from theme-field name to the
            `(file, line)` of the `theme:` op that last set it. Kept in
            step with `user_set` (set together, cleared together) so a
            semantic check at end-of-apply can attribute an error to the
            originating op's line — e.g. E222 for a `merge_lane_clearance`
            that has no effect with `auto_lane_change` off.
        branch_color_overrides: Hex-color overrides keyed by
            `BranchState.id`, populated as `branch:` ops with `color`
            apply and pruned when their branch is removed.
        branch_label_side_overrides: `label_side` overrides keyed by
            `BranchState.id`, populated as `branch:` ops with
            `label_side` apply and pruned when their branch is removed.
    """

    theme_cls: type[Theme] = DefaultTheme
    user_set: dict[str, Any] = field(default_factory=dict)
    user_set_lines: dict[str, tuple[str | None, int]] = field(default_factory=dict)
    branch_color_overrides: dict[str, str] = field(default_factory=dict)
    branch_label_side_overrides: dict[str, LabelSide] = field(default_factory=dict)

    def set_theme_cls(self, theme_cls: type[Theme]) -> None:
        """Switch the concrete theme to build with — no other state changes.

        The companion `clear_overrides` runs separately (or not, per
        the op's `keep_prior_overrides` flag), so callers wanting the
        v0.1.4-documented "reset every field" behavior invoke both.

        Args:
            theme_cls: The concrete `Theme` subclass to dispatch
                `build()` to at end-of-apply.
        """
        self.theme_cls = theme_cls

    def clear_overrides(self) -> None:
        """Discard every accumulated override — user `theme:` fields and state-derived per-branch values.

        Called by `apply_theme_op` when a `name`-bearing op leaves
        `keep_prior_overrides` at its default `False`. Wiping all
        accumulators is what makes "switch theme cleanly" actually
        clean: leaving `branch_color_overrides` or
        `branch_label_side_overrides` in place would let earlier
        per-branch choices bleed through into the new theme with no
        syntactic way to clear them.
        """
        self.user_set = {}
        self.user_set_lines = {}
        self.branch_color_overrides = {}
        self.branch_label_side_overrides = {}

    def build(self) -> Theme:
        """Resolve a fully-populated `Theme` and attach state-derived overrides.

        Calls `self.theme_cls.build(self.user_set)` to produce the
        resolved theme; then writes the accumulated per-branch
        overrides onto the result. Called once by the state engine at
        end-of-apply.

        Returns:
            The fully-populated `Theme`.
        """
        theme = self.theme_cls.build(self.user_set)
        theme.branch_color_overrides = dict(self.branch_color_overrides)
        theme.branch_label_side_overrides = dict(self.branch_label_side_overrides)
        return theme
