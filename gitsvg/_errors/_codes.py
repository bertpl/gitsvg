"""Error code registry for the gitsvg validator.

Each error site declares its code via `register()` exactly once. The
numeric range encodes the validation phase the code belongs to:

- E001-E099: parse / JSONL syntax
- E100-E199: per-op shape (pydantic-level)
- E200-E299: per-op semantic (state-aware)
- E300-E399: imports (cycle, depth, path, ordering)
- E400-E499: end-of-file cross-reference checks
- E500+:     reserved for future categories

PR2 ships zero codes — the registry is empty until PR3 introduces the
first parser/shape codes alongside the error sites that emit them.

Codes may still be renumbered through 0.0.x. Strive for stability from
0.1.0 onward.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ErrorCode:
    """A single declared error code with its short summary.

    Attributes:
        code: The textual code (e.g. `"E210"`).
        summary: One-line description shown in the `gitsvg errors` index.
    """

    code: str
    summary: str


_REGISTERED_CODES: dict[str, ErrorCode] = {}


def register(code: str, summary: str) -> ErrorCode:
    """Declare a new error code and add it to the global registry.

    Args:
        code: The textual code (must match the `E###` convention).
        summary: One-line description for the `gitsvg errors` index.

    Returns:
        The registered `ErrorCode` entry.

    Raises:
        ValueError: If `code` is already registered.
    """
    if code in _REGISTERED_CODES:
        raise ValueError(f"error code {code!r} is already registered")
    entry = ErrorCode(code=code, summary=summary)
    _REGISTERED_CODES[code] = entry
    return entry


def get(code: str) -> ErrorCode | None:
    """Return the registered `ErrorCode` for `code`, or None if unknown."""
    return _REGISTERED_CODES.get(code)


def all_codes() -> list[ErrorCode]:
    """Return all registered codes in declaration order."""
    return list(_REGISTERED_CODES.values())
