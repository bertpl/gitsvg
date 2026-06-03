"""Architecture guard for the merge-dot-style registry.

Every `MergeCommitStyle` must have a spec in `_MERGE_DOT_BUILDERS`, so a
future enum value added without a spec fails the suite here rather than
`KeyError`-ing at render time.
"""

from gitsvg._value_types import MergeCommitStyle
from gitsvg.render._primitives.merge_dot_styles import _MERGE_DOT_BUILDERS


def test_every_merge_commit_style_has_a_builder() -> None:
    # --- assert -----------------------
    assert set(_MERGE_DOT_BUILDERS) == set(MergeCommitStyle)
