"""CLI tests for `gitsvg theme`."""

import json

import pytest
from click.testing import CliRunner

from gitsvg.cli._cli import cli


# ==================================================================================================
#  theme (index)
# ==================================================================================================
def test_theme_no_args_lists_all_themes_with_descriptions() -> None:
    # --- arrange ----------------------
    runner = CliRunner()

    # --- act --------------------------
    result = runner.invoke(cli, ["theme"])

    # --- assert -----------------------
    assert result.exit_code == 0
    for name in ("compact", "dark", "default", "gui", "muted"):
        assert name in result.output
    # The description column renders (dark's docstring summary, backticks stripped).
    assert "One Dark-inspired" in result.output


# ==================================================================================================
#  theme --list-names (bare)
# ==================================================================================================
def test_theme_list_names_prints_bare_names_one_per_line() -> None:
    # --- arrange ----------------------
    runner = CliRunner()

    # --- act --------------------------
    result = runner.invoke(cli, ["theme", "--list-names"])

    # --- assert -----------------------
    assert result.exit_code == 0
    lines = [line for line in result.output.splitlines() if line]
    assert lines == ["compact", "dark", "default", "gui", "muted"]


# ==================================================================================================
#  theme <name> (resolved field values)
# ==================================================================================================
@pytest.mark.parametrize(
    ("name", "expected_fields"),
    [
        (
            "default",
            {
                ("orientation",): "bt",
                ("branch_spacing",): 100,
                ("background_color",): None,
                ("colors", "main"): "#4a4f5a",
                ("colors", "branch1"): "#56b393",
                ("branch_line_style",): "bezier",
                ("merge_commit_style",): "checkmark",
            },
        ),
        (
            "dark",
            {
                ("background_color",): "#282c34",
                ("colors", "main"): "#abb2bf",
                ("commit_stroke_color",): "#282c34",
            },
        ),
        (
            "muted",
            {
                ("colors", "main"): "#5c6370",
                ("branch_line_style",): "rounded",
                ("merge_commit_style",): "circle",
            },
        ),
        (
            "compact",
            {
                ("branch_spacing",): 75,
                ("commit_spacing",): 35,
                ("label_font_size",): 9.5,
            },
        ),
    ],
)
def test_theme_inspect_emits_resolved_fields(name: str, expected_fields: dict) -> None:
    # --- arrange ----------------------
    runner = CliRunner()

    # --- act --------------------------
    result = runner.invoke(cli, ["theme", name])

    # --- assert -----------------------
    assert result.exit_code == 0
    payload = json.loads(result.output)
    for path, value in expected_fields.items():
        resolved = payload
        for key in path:
            resolved = resolved[key]
        assert resolved == value


def test_theme_unknown_exits_non_zero_with_known_list() -> None:
    # --- arrange ----------------------
    runner = CliRunner()

    # --- act --------------------------
    result = runner.invoke(cli, ["theme", "midnight"])

    # --- assert -----------------------
    assert result.exit_code != 0
    assert "Unknown theme" in result.output
    # Lists the registered names so the user can pick one.
    for name in ("compact", "dark", "default", "muted"):
        assert name in result.output
