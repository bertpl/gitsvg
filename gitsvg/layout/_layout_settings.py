"""LayoutSettings — the layout pipeline stage's slice of `Theme`.

Empty by design today. The layout engine's `compute_layout(state)` is
a pure grid transformation that reads nothing from `Theme` — orientation
flips, spacings, and every other presentational concern enter only at
the renderer's transform boundary. The class exists as the
architectural home for future layout-affecting fields (lane reuse
policy, branch-axis hint, pin policy for the rebase-rebuild pattern,
etc.); the pipeline-split meta-test enforces that `gitsvg/layout/`
keeps consuming only this class (and `State`), never `Theme` directly.

Constructed by `Theme.split()`; the orchestrator hands it to the
layout entry point alongside `State` when the entry point grows a
settings argument (today it does not).
"""

from pydantic import BaseModel, ConfigDict


class LayoutSettings(BaseModel):
    """The layout pipeline stage's slice of `Theme`.

    Carries no fields today — the layout engine reads nothing from
    `Theme`. The class marks the pipeline boundary; future layout-
    affecting fields land here, leaving `RendererSettings` narrower.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)
