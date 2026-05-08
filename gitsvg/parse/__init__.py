"""JSONL parser for gitsvg input files.

Public surface:

- `parse_jsonl_file(path)` — parse a `.gitsvg.jsonl` file from disk.
- `parse_jsonl_text(text, file=...)` — parse JSONL text in-memory.
- `ParsedOp` — a successfully validated op paired with its source location.

Both parse functions return `(parsed_ops, report)`. Errors accumulate in
the report rather than raising; consumers print the report or react to it
as needed.
"""

from gitsvg.parse._parsed_op import ParsedOp
from gitsvg.parse._parser import parse_jsonl_file, parse_jsonl_text

__all__ = [
    "ParsedOp",
    "parse_jsonl_file",
    "parse_jsonl_text",
]
