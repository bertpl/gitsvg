"""ValidationError — a single error record produced during validation."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ValidationError:
    """One validation error tied to an input location.

    Attributes:
        file: Source file path where the error originates.
        line: 1-based line number within `file`.
        code: Error code (e.g. `"E210"`).
        message: Short, human-readable error message.
        field: Name of the offending field on the op, if applicable.
        suggestion: Optional remediation hint shown alongside the error.
    """

    file: str
    line: int
    code: str
    message: str
    field: str | None = None
    suggestion: str | None = None

    def format(self) -> str:
        """Return the default plain-text rendering: `file:line: [code] field: message`."""
        field_part = f" {self.field}:" if self.field else ""
        return f"{self.file}:{self.line}: [{self.code}]{field_part} {self.message}"
