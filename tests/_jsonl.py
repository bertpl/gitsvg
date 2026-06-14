"""Build `.gitsvg.jsonl` fixture text from op dicts.

Use this instead of hand-writing JSON string literals in fixtures. It escapes
values correctly — a Windows path's backslashes, a message with a quote or
newline — and mirrors how the parser reads input (one ``json.loads`` per
line), so a fixture speaks exactly the encoding the system under test
consumes.

Pass paths as ``str(path)``: a ``Path`` is not JSON-serializable, and keeping
the helper dumb lets ``json.dumps`` own the escaping.
"""

import json
from typing import Any


def build_jsonl(*ops: dict[str, Any]) -> str:
    """Serialize `ops` into JSONL — one compact JSON object per line.

    Each line is terminated by a newline (including the last), matching the
    hand-written fixtures this replaces and what the parser expects.
    """
    return "".join(json.dumps(op) + "\n" for op in ops)
