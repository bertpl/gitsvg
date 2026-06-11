"""ValidationError — a single error record produced during validation."""

from dataclasses import dataclass

from ._codes import find_error_code


@dataclass(frozen=True, slots=True)
class ValidationError:
    """One validation error tied to an input location.

    Construction enforces that `code` is in the global error catalog —
    constructing with an unregistered code raises `ValueError`. This
    keeps the emit sites and the catalog in lock-step: a code with no
    catalog entry simply cannot be emitted.

    Attributes:
        file: Source file path the error originates from, or `None` for errors with no specific source location.
        line: 1-based line number within `file`.
        code: Error code (e.g. `"E210"`). Must be registered in the catalog.
        message: Short, human-readable error message.
        field: Name of the offending field on the op, if applicable.
        suggestion: Closest declared name when the error is a likely
            typo'd reference, if any. Carried structurally (e.g. in
            `--json` output) and rendered by `format()` as a
            did-you-mean tail.

    Raises:
        ValueError: If `code` is not in the catalog (no `<code>.md` under
            `gitsvg/errors/catalog/`).
    """

    file: str | None
    line: int
    code: str
    message: str
    field: str | None = None
    suggestion: str | None = None

    def __post_init__(self) -> None:
        """Reject construction with an unregistered code."""
        if find_error_code(self.code) is None:
            raise ValueError(
                f"error code {self.code!r} is not in the catalog (add `{self.code}.md` to `gitsvg/errors/catalog/`)"
            )

    def format(self) -> str:
        """Return the default plain-text rendering.

        `file:line: [code] field: message`, or `[code] field: message` when
        the error has no source location (`file is None`). A set
        `suggestion` is appended as ` — did you mean '<suggestion>'?`,
        so every error that carries one renders it without per-site
        wording.
        """
        field_part = f" {self.field}:" if self.field else ""
        location = f"{self.file}:{self.line}: " if self.file is not None else ""
        suggestion_part = f" — did you mean {self.suggestion!r}?" if self.suggestion else ""
        return f"{location}[{self.code}]{field_part} {self.message}{suggestion_part}"
