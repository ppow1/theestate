import json
import subprocess
import sys

from estate.core.work_package_validation import validate_work_package, get_validation_recipe


def init_git(root):
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
    (root / "README.md").write_text("test\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=root, check=True, capture_output=True)


def test_known_work_package_recipe_execution_and_artifacts(tmp_path):
    init_git(tmp_path)
    payload = validate_work_package("WP-0079", tmp_path)
    assert payload["work_package_id"] == "WP-0079"
    assert payload["recipe_id"] == "wp-0079-validation-execution-engine-self-check"
    assert payload["commands_run"]
    assert (tmp_path / "operations/validation/reports/WP-0079_validation.md").exists()
    report = json.loads((tmp_path / "runtime/validation/work_packages/WP-0079_validation.json").read_text())
    assert report["command_results"][0]["started_at"]
    assert report["command_results"][0]["completed_at"]
    assert "duration_seconds" in report["command_results"][0]
    latest = json.loads((tmp_path / "runtime/validation/work_packages/latest.json").read_text())
    assert latest["work_package_id"] == "WP-0079"
    assert latest["latest_validation_report_path"] == "operations/validation/reports/WP-0079_validation.md"
    assert latest["markdown_report"] == "operations/validation/reports/WP-0079_validation.md"
    assert latest["json_report"] == "runtime/validation/work_packages/WP-0079_validation.json"


def test_unknown_work_package_generates_no_recipe_report(tmp_path):
    init_git(tmp_path)
    payload = validate_work_package("WP-9999", tmp_path)
    assert payload["validation_status"] == "no_recipe"
    assert payload["warnings"] == ["No validation recipe is registered for WP-9999."]
    md = (tmp_path / "operations/validation/reports/WP-9999_validation.md").read_text()
    assert "Recipe used: none" in md


def test_required_vs_observational_command_handling_and_failed_capture(tmp_path, monkeypatch):
    init_git(tmp_path)
    from estate.core import work_package_validation as mod
    monkeypatch.setitem(mod.VALIDATION_RECIPES, "WP-1234", {
        "recipe_id": "test-recipe",
        "continue_on_failure": True,
        "commands": [
            {"command": f'{sys.executable} -c "import sys; print(\'bad\', file=sys.stderr); sys.exit(3)"', "required": False},
            {"command": f'{sys.executable} -c "import sys; sys.exit(4)"', "required": True},
        ],
    })
    payload = validate_work_package("WP-1234", tmp_path)
    assert payload["validation_status"] == "failed"
    assert payload["findings"] and payload["failures"]
    assert payload["command_results"][0]["status"] == "finding"
    assert payload["command_results"][1]["status"] == "failed"
    assert "stderr_path" in payload["command_results"][0]


def test_markdown_json_required_fields_and_self_check_recipe(tmp_path):
    assert get_validation_recipe("WP-0079") is not None
    init_git(tmp_path)
    payload = validate_work_package("WP-9998", tmp_path)
    required = {"work_package_id", "validation_id", "generated_at", "git_branch", "git_commit_before", "git_commit_after", "validation_status", "recipe_id", "commands_run", "command_results", "stdout_summary", "stderr_summary", "files_written", "warnings", "failures", "findings", "reviewer_recommendation"}
    assert required <= set(payload)
    md = (tmp_path / "operations/validation/reports/WP-9998_validation.md").read_text()
    for section in ["# Work Package Validation Report", "## Commands Run", "## Findings", "## Warnings", "## Failures", "## Generated Artifacts", "## Reviewer Recommendation"]:
        assert section in md


def test_recipe_expansion_registers_next_validation_recipes():
    existing = {"WP-0056", "WP-0057", "WP-0058", "WP-0059", "WP-0060", "WP-0074", "WP-0079"}
    expanded = {"WP-0075", "WP-0076", "WP-0077", "WP-0078", "WP-0086", "WP-0091"}
    for work_package_id in existing | expanded:
        recipe = get_validation_recipe(work_package_id)
        assert recipe is not None
        assert recipe["commands"]


def test_wp_0075_and_wp_0076_execute_real_recipe_commands(tmp_path):
    init_git(tmp_path)
    wp_0075 = validate_work_package("WP-0075", tmp_path)
    wp_0076 = validate_work_package("WP-0076", tmp_path)

    assert wp_0075["validation_status"] != "no_recipe"
    assert wp_0076["validation_status"] != "no_recipe"
    assert wp_0075["commands_run"]
    assert wp_0076["commands_run"]
    assert wp_0075["command_results"]
    assert wp_0076["command_results"]
    assert "operational-readiness-dashboard --json" in wp_0075["commands_run"][0]
    assert "estate-capability-registry --json" in wp_0076["commands_run"][0]


def test_wp_0077_and_wp_0078_execute_real_recipe_commands(tmp_path):
    init_git(tmp_path)
    wp_0077 = validate_work_package("WP-0077", tmp_path)
    wp_0078 = validate_work_package("WP-0078", tmp_path)

    assert wp_0077["validation_status"] != "no_recipe"
    assert wp_0078["validation_status"] != "no_recipe"
    assert wp_0077["commands_run"]
    assert wp_0078["commands_run"]
    assert wp_0077["command_results"]
    assert wp_0078["command_results"]
    assert "capability-dependency-visualization --json" in wp_0077["commands_run"][0]
    assert "capability-gap-report --json" in wp_0078["commands_run"][0]


def test_wp_0091_self_check_recipe_targets_new_expanded_recipes():
    recipe = get_validation_recipe("WP-0091")
    assert recipe is not None
    commands = recipe["commands"]
    assert any("validate-work-package --id WP-0077 --json" in command["command"] for command in commands)
    assert any("validate-work-package --id WP-0078 --json" in command["command"] for command in commands)


def test_wp_0086_self_check_recipe_targets_expanded_recipes():
    recipe = get_validation_recipe("WP-0086")
    assert recipe is not None
    commands = recipe["commands"]
    assert any("validate-work-package --id WP-0075 --json" in command["command"] for command in commands)
    assert any("validate-work-package --id WP-0076 --json" in command["command"] for command in commands)


def test_safe_wrapper_refuses_unrelated_changes_and_no_broad_staging():
    script = open("operations/validation/scripts/run_and_commit_validation.ps1", encoding="utf-8").read()
    assert "git status --porcelain" in script
    assert "Refusing to validate with unrelated local changes" in script
    assert "Refusing to stage non-validation artifacts" in script
    assert "git add ." not in script
    assert "git add -- $path" in script
    assert "git add -f -- $p" in script
