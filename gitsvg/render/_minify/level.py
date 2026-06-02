"""Minification level type — selects which post-processor steps run."""

from typing import Literal

MinifyLevel = Literal[0, 1, 2, 3]
"""Minification level selected by the CLI's `--small` flag.

See the `gitsvg.render._minify` package docstring for the level ladder.
"""
