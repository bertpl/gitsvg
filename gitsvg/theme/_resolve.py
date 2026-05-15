"""End-of-state-stage default resolution for orientation-aware fields.

Mutates a `Theme` in place, replacing every `None`-default sentinel
on an orientation-resolved field with a concrete pixel value. Called
by the state engine as the last step of `apply_ops` so the renderer
never sees a `None`.

Sentinel semantics: `None` means "still default — fill from the
orientation-resolved formula"; any concrete value means "user-set,
sticky." A field set to `null` mid-stream by a later `theme:` op
resets to `None`, which lets the resolver re-fill it — the supported
"opt back into the default" mechanism.

Currently fills the four visual-side margins (`margin_left`,
`margin_right`, `margin_top`, `margin_bottom`) using the
bottom-to-top default formulas directly. The function is structured
to extend with additional orientation-aware fields and per-orientation
defaults as the theme surface grows.
"""

from gitsvg.theme._theme import Theme, _resolve_int_or_float


def resolve_defaults(theme: Theme) -> None:
    """Fill `None`-default fields on `theme` with concrete pixel values.

    Mutates in place. Idempotent: a second call leaves the theme
    unchanged because every field is now non-`None`.

    Args:
        theme: The accumulated live theme, post-`apply_ops`. Fields
            the user explicitly set are kept; `None` fields are
            filled from the bottom-to-top default formula.
    """
    _resolve_margins(theme)


def _resolve_margins(theme: Theme) -> None:
    """Fill `None` margins with the bottom-to-top default × spacing.

    Defaults at orientation `bt` (the only orientation today):

    - `margin_left` / `margin_right`: `1.0 × branch_spacing`
    - `margin_top` / `margin_bottom`: `0.5 × commit_spacing`

    `_resolve_int_or_float` keeps whole-number results as `int` so the
    SVG attribute formatting matches the pre-rename baseline exactly
    (drawsvg writes `width="100"` from int and `width="100.0"` from
    float; the byte-identical output gate depends on this).
    """
    branch_default = _resolve_int_or_float(1.0 * theme.branch_spacing)
    commit_default = _resolve_int_or_float(0.5 * theme.commit_spacing)
    if theme.margin_left is None:
        theme.margin_left = branch_default
    if theme.margin_right is None:
        theme.margin_right = branch_default
    if theme.margin_top is None:
        theme.margin_top = commit_default
    if theme.margin_bottom is None:
        theme.margin_bottom = commit_default
