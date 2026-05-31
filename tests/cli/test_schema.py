"""CLI tests for `gitsvg schema`."""

import json

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
    assert lines == ["compact", "dark", "default", "muted"]


# ==================================================================================================
#  schema theme <name> (inspect)
# ==================================================================================================
def test_schema_theme_default_emits_resolved_json() -> None:
    # --- arrange ----------------------
    runner = CliRunner()

    # --- act --------------------------
    result = runner.invoke(cli, ["schema", "theme", "default"])

    # --- assert -----------------------
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["orientation"] == "bt"
    assert payload["branch_spacing"] == 100
    assert payload["background_color"] is None


def test_schema_theme_dark_emits_dark_palette() -> None:
    # --- arrange ----------------------
    runner = CliRunner()

    # --- act --------------------------
    result = runner.invoke(cli, ["schema", "theme", "dark"])

    # --- assert -----------------------
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["background_color"] == "#282c34"
    assert payload["colors"]["main"] == "#abb2bf"
    assert payload["commit_stroke_color"] == "#282c34"


def test_schema_theme_muted_emits_pre_refresh_palette_and_styles() -> None:
    # --- arrange ----------------------
    runner = CliRunner()

    # --- act --------------------------
    result = runner.invoke(cli, ["schema", "theme", "muted"])

    # --- assert -----------------------
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["colors"]["main"] == "#5c6370"
    assert payload["branch_line_style"] == "rounded"
    assert payload["merge_commit_style"] == "circle"


def test_schema_theme_default_emits_refreshed_palette_and_styles() -> None:
    # --- arrange ----------------------
    runner = CliRunner()

    # --- act --------------------------
    result = runner.invoke(cli, ["schema", "theme", "default"])

    # --- assert -----------------------
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["colors"]["main"] == "#4a4f5a"
    assert payload["colors"]["branch1"] == "#56b393"
    assert payload["branch_line_style"] == "bezier"
    assert payload["merge_commit_style"] == "checkmark"


def test_schema_theme_compact_emits_tighter_metrics() -> None:
    # --- arrange ----------------------
    runner = CliRunner()

    # --- act --------------------------
    result = runner.invoke(cli, ["schema", "theme", "compact"])

    # --- assert -----------------------
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["branch_spacing"] == 75
    assert payload["commit_spacing"] == 35
    assert payload["label_font_size"] == 9.5


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
