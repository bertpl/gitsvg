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
        file: Source file path where the error originates.
        line: 1-based line number within `file`.
        code: Error code (e.g. `"E210"`). Must be registered in the catalog.
        message: Short, human-readable error message.
        field: Name of the offending field on the op, if applicable.
        suggestion: Optional remediation hint shown alongside the error.

    Raises:
        ValueError: If `code` is not in the catalog (no `<code>.md` under
            `gitsvg/errors/catalog/`).
    """

    file: str
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
        """Return the default plain-text rendering: `file:line: [code] field: message`."""
        field_part = f" {self.field}:" if self.field else ""
        return f"{self.file}:{self.line}: [{self.code}]{field_part} {self.message}"
