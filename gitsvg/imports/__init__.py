"""Import resolution — expand `import` ops into the imported file's op stream.

Sits between the parser and the state engine in the validator pipeline:

    parse → resolve_imports → state-apply → (eventually) end-of-file checks

The state engine never touches the filesystem; everything import-related
is finished by the time apply_ops runs.
"""

from gitsvg.imports._resolver import DEFAULT_DEPTH_LIMIT, resolve_imports

__all__ = [
    "DEFAULT_DEPTH_LIMIT",
    "resolve_imports",
]
