"""CLI tests for `gitsvg schema`."""

import json

import pytest
from click.testing import CliRunner

from gitsvg.cli._cli import cli


def test_schema_no_args_prints_index_with_all_op_names() -> None:
    # --- arrange ----------------------
    runner = CliRunner()

    # --- act --------------------------
    result = runner.invoke(cli, ["schema"])

    # --- assert -----------------------
    assert result.exit_code == 0
    for op_name in ["import", "grid", "branch", "commit", "merge", "pull_request", "remove", "highlight"]:
        assert op_name in result.output
    assert "File-level constraints" in result.output


def test_schema_with_op_name_prints_valid_json_schema() -> None:
    # --- arrange ----------------------
    runner = CliRunner()

    # --- act --------------------------
    result = runner.invoke(cli, ["schema", "commit"])

    # --- assert -----------------------
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["type"] == "object"
    assert "branch" in payload["properties"]


def test_schema_list_ops_prints_bare_names_one_per_line() -> None:
    # --- arrange ----------------------
    runner = CliRunner()

    # --- act --------------------------
    result = runner.invoke(cli, ["schema", "--list-ops"])

    # --- assert -----------------------
    assert result.exit_code == 0
    lines = [line for line in result.output.splitlines() if line]
    assert lines == [
        "import",
        "grid",
        "theme",
        "branch",
        "commit",
        "merge",
        "pull_request",
        "remove",
        "highlight",
    ]


def test_schema_unknown_op_exits_non_zero() -> None:
    # --- arrange ----------------------
    runner = CliRunner()

    # --- act --------------------------
    result = runner.invoke(cli, ["schema", "rebase"])

    # --- assert -----------------------
    assert result.exit_code != 0
    assert "Unknown op" in result.output


# ==================================================================================================
#  schema themes (list)
# ==================================================================================================
def test_schema_themes_lists_registered_names_alphabetically() -> None:
    # --- arrange ----------------------
    runner = CliRunner()

    # --- act --------------------------
    result = runner.invoke(cli, ["schema", "themes"])

    # --- assert -----------------------
    assert result.exit_code == 0
    lines = [line for line in result.output.splitlines() if line]
    assert lines == ["compact", "dark", "default", "gui", "muted"]


# ==================================================================================================
#  schema theme <name> (inspect)
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
def test_schema_theme_inspect_emits_resolved_fields(name: str, expected_fields: dict) -> None:
    # --- arrange ----------------------
    runner = CliRunner()

    # --- act --------------------------
    result = runner.invoke(cli, ["schema", "theme", name])

    # --- assert -----------------------
    assert result.exit_code == 0
    payload = json.loads(result.output)
    for path, value in expected_fields.items():
        resolved = payload
        for key in path:
            resolved = resolved[key]
        assert resolved == value


def test_schema_theme_unknown_exits_non_zero_with_known_list() -> None:
    # --- arrange ----------------------
    runner = CliRunner()

    # --- act --------------------------
    result = runner.invoke(cli, ["schema", "theme", "midnight"])

    # --- assert -----------------------
    assert result.exit_code != 0
    assert "Unknown theme" in result.output
    # Lists the registered names so the user can pick one.
    for name in ("compact", "dark", "default", "muted"):
        assert name in result.output


def test_schema_theme_without_name_still_emits_op_schema() -> None:
    """`schema theme` (no second arg) keeps its existing meaning — the
    JSON schema for the `theme` op — so the new commands don't break
    the original surface."""
    # --- arrange ----------------------
    runner = CliRunner()

    # --- act --------------------------
    result = runner.invoke(cli, ["schema", "theme"])

    # --- assert -----------------------
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["type"] == "object"
    # `keep_prior_overrides` is a `theme` op field — sanity check we're
    # looking at the op schema and not the resolved-theme JSON.
    assert "keep_prior_overrides" in payload["properties"]
    # The layout-policy fields surface on the op schema with their descriptions.
    assert "commit_row_mode" in payload["properties"]
    assert "auto_lane_change" in payload["properties"]
    assert "merge_lane_clearance" in payload["properties"]
