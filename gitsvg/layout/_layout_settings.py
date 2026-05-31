"""LayoutSettings — the layout pipeline stage's slice of `Theme`.

The layout engine's `compute_layout(state, layout_settings)` reads its
layout-policy fields from this class — never from `Theme` directly.
Orientation flips, spacings, and every other presentational concern
stay on the renderer side; only fields that change the integer grid
land here. The pipeline-split meta-test enforces that `gitsvg/layout/`
keeps consuming only this class (and `State`), never `Theme`.

Constructed by `Theme.split()` and handed to `compute_layout` alongside
`State`. It is the architectural home for layout-policy fields (`commit_row_mode`,
`auto_lane_change`; future tenants include lane-reuse policy, branch-axis
hints, and pin policy for the rebase-rebuild pattern).
"""

from pydantic import BaseModel, ConfigDict

from gitsvg.theme._commit_row_mode import CommitRowMode


class LayoutSettings(BaseModel):
    """The layout pipeline stage's slice of `Theme`.

    Carries the layout-policy fields the engine reads. The class marks
    the pipeline boundary so layout code imports `LayoutSettings`, not
    `Theme`.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    commit_row_mode: CommitRowMode = CommitRowMode.SHARED
    auto_lane_change: bool = False
    merge_lane_clearance: int = 1
