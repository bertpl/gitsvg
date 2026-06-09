"""Dark theme — One Dark-inspired palette for dark backgrounds.

`DarkTheme` overrides every color-bearing `_resolve_*` on
`DefaultTheme` to swap the muted light-background palette for the
well-known One Dark color set. Geometry, spacings, typography, and
label angles inherit unchanged — only color-adjacent fields change.

The commit-dot stroke color matches the canvas background so the
outline reads as a "carved out" gap separating the dot from any
branch line passing through it, rather than the white halo
`DefaultTheme` uses against light backgrounds.

Pill text is hard-coded white in the pill primitives, so pill
backgrounds inherit the branch's palette color and read legibly on
the dark canvas without an extra resolver.
"""

from gitsvg.theme._default_theme import DefaultTheme


class DarkTheme(DefaultTheme):
    """One Dark-inspired palette inversion of `DefaultTheme`.

    Overrides `_resolve_background_color`, `_resolve_colors`,
    `_resolve_label_color`, `_resolve_hash_color`,
    `_resolve_branch_guide_color`, and `_resolve_commit_stroke_color`.
    Every other field inherits from `DefaultTheme`.
    """

    @classmethod
    def _resolve_background_color(cls) -> str:
        """Cool dark blue-gray canvas (One Dark `bg`).

        Softer than pure black, family-coherent with the palette below.
        """
        return "#282c34"

    @classmethod
    def _resolve_colors(cls) -> dict[str, str]:
        """One Dark branch palette.

        `main` is the editor's default text color — a soft cool gray
        that sits in the same family as the background and reads as a
        deliberate neutral rather than a desaturated branch. The four
        `branch*` slots cycle through green, blue, coral, and purple
        in declaration order (the inherited
        `_resolve_default_branch_color_cycle` preserves the order).
        """
        return {
            "main": "#abb2bf",
            "branch1": "#98c379",
            "branch2": "#61afef",
            "branch3": "#e06c75",
            "branch4": "#c678dd",
        }

    @classmethod
    def _resolve_label_color(cls) -> str:
        """One Dark default text — same soft gray as `main`, keeps the typography coherent with the palette family."""
        return "#abb2bf"

    @classmethod
    def _resolve_hash_color(cls) -> str:
        """Mid-gray between `label_color` (`#abb2bf`) and `background_color` (`#282c34`).

        Preserves the secondary-line hierarchy while staying legible at the
        small hash font size.
        """
        return "#7f848e"

    @classmethod
    def _resolve_branch_guide_color(cls) -> str:
        """One Dark cursor-line gray — present but recedes against the background."""
        return "#3e4451"

    @classmethod
    def _resolve_commit_stroke_color(cls) -> str:
        """Match the canvas background so the dot outline reads as a separating gap rather than a halo."""
        return "#282c34"
