"""Cross-cutting, end-of-stream validation.

Checks that can only run once the whole op stream is applied — they need
the fully-resolved `Theme` and/or the complete `State` graph, so they
live downstream of the apply pass rather than inside any per-op handler.

- `check_resolved_config` — config-consistency conflicts on the resolved
  theme (E221-E224), reading the `UserOverrides` record.
- `check_cross_reference` — dangling-reference checks over the final
  state graph (E400, E401).
- `UserOverrides` — a record of what the input explicitly set, packed
  from the applied state and the theme builder.
"""

from ._cross_reference import check_cross_reference
from ._resolved_config import check_resolved_config
from ._user_overrides import UserOverrides

__all__ = [
    "UserOverrides",
    "check_cross_reference",
    "check_resolved_config",
]
