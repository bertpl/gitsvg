"""ValidationReport — collection of `ValidationError` records from a run."""

from gitsvg._errors._validation_error import ValidationError


class ValidationReport:
    """Accumulator for `ValidationError` entries during a validation run.

    Errors are appended in the order they are discovered. Consumers
    (CLI, in-process callers) read them via `errors` after the run
    completes.
    """

    def __init__(self) -> None:
        """Create an empty report."""
        self._errors: list[ValidationError] = []

    def add(self, error: ValidationError) -> None:
        """Append `error` to the report."""
        self._errors.append(error)

    @property
    def errors(self) -> list[ValidationError]:
        """Return the accumulated errors in insertion order (defensive copy)."""
        return list(self._errors)

    def is_clean(self) -> bool:
        """Return True iff no errors have been added."""
        return not self._errors

    def __len__(self) -> int:
        """Return the number of accumulated errors."""
        return len(self._errors)
