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
    expanded = {"WP-0015", "WP-0019", "WP-0021", "WP-0027", "WP-0029", "WP-0036", "WP-0037", "WP-0038", "WP-0052", "WP-0053", "WP-0065", "WP-0066", "WP-0067", "WP-0068", "WP-0070", "WP-0075", "WP-0076", "WP-0077", "WP-0078", "WP-0080", "WP-0081", "WP-0085", "WP-0086", "WP-0091", "WP-0092", "WP-0103"}
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


def test_historical_complete_receipt_recipes_execute_representative_commands(tmp_path):
    init_git(tmp_path)
    wp_0015 = validate_work_package("WP-0015", tmp_path)
    wp_0027 = validate_work_package("WP-0027", tmp_path)
    wp_0081 = validate_work_package("WP-0081", tmp_path)

    for payload in (wp_0015, wp_0027, wp_0081):
        assert payload["validation_status"] != "no_recipe"
        assert payload["recipe_id"]
        assert payload["commands_run"]
        assert payload["command_results"]

    assert "message-ack --help" in wp_0015["commands_run"][0]
    assert "estate-search" in wp_0027["commands_run"][0]
    assert "estate-service-catalog --json" in wp_0081["commands_run"][0]


def test_wp_0103_self_check_recipe_targets_historical_coverage():
    recipe = get_validation_recipe("WP-0103")
    assert recipe is not None
    commands = [command["command"] for command in recipe["commands"]]
    assert any("validation-production-readiness --json" in command for command in commands)
    assert any("validate-work-package --id WP-0015 --json" in command for command in commands)
    assert any("validate-work-package --id WP-0027 --json" in command for command in commands)


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


def test_wp_0102_and_wp_0105_recipes_registered():
    wp_0102 = get_validation_recipe("WP-0102")
    wp_0105 = get_validation_recipe("WP-0105")
    assert wp_0102 is not None
    assert wp_0102["recipe_id"] == "wp-0102-backlog-codex-template-retrofit-closure"
    assert any("WP-0102 Template Retrofit Notice" in command["command"] for command in wp_0102["commands"])
    assert wp_0105 is not None
    assert wp_0105["recipe_id"] == "wp-0105-validation-closure-repair-0102-0103"
    assert any("validate-work-package --id WP-0102 --json" in command["command"] for command in wp_0105["commands"])




def test_wp_0102_recipe_uses_canonical_template_paths():
    recipe = get_validation_recipe("WP-0102")
    assert recipe is not None
    commands = [command["command"] for command in recipe["commands"]]
    template_command = commands[0]
    assert "python -c" in template_command
    assert "docs/operations/Codex_Task_Template_Standard_v1.md" in template_command
    assert "collaboration/work_packages/pending/WP-0101_SERIES_codex_task_template_standard.md" in template_command
    assert "test -f" not in template_command


def test_wp_0102_template_path_command_validates_current_checkout():
    recipe = get_validation_recipe("WP-0102")
    assert recipe is not None
    command = recipe["commands"][0]["command"]
    result = subprocess.run(command, shell=True, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr


def test_wp_0102_retrofit_notice_command_is_cross_platform_python():
    recipe = get_validation_recipe("WP-0102")
    assert recipe is not None
    commands = [command["command"] for command in recipe["commands"]]
    notice_command = next(command for command in commands if "WP-0102 Template Retrofit Notice" in command)
    assert notice_command.startswith("python -c ")
    assert "for id in" not in notice_command
    assert " do " not in notice_command
    assert "rg -q" not in notice_command


def test_wp_0102_retrofit_notice_command_validates_current_checkout():
    recipe = get_validation_recipe("WP-0102")
    assert recipe is not None
    command = next(command["command"] for command in recipe["commands"] if "WP-0102 Template Retrofit Notice" in command["command"])
    result = subprocess.run(command, shell=True, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr or result.stdout

def test_wp_0105_recipe_depends_on_wp_0102_validation_success():
    recipe = get_validation_recipe("WP-0105")
    assert recipe is not None
    commands = [command["command"] for command in recipe["commands"]]
    assert any("validate-work-package --id WP-0102 --json" in command for command in commands)
    assert any("validation-production-readiness --json" in command for command in commands)

def test_wp_0103_historical_recipe_registrations_preserved():
    for work_package_id in ("WP-0080", "WP-0081", "WP-0085", "WP-0103"):
        recipe = get_validation_recipe(work_package_id)
        assert recipe is not None
        assert recipe["commands"]
    assert get_validation_recipe("WP-0103")["recipe_id"] == "wp-0103-historical-validation-recipe-coverage"


def test_wp_0020_helen_hr_onboarding_recipe_registered():
    recipe = get_validation_recipe("WP-0020")
    assert recipe is not None
    assert recipe["recipe_id"] == "wp-0020-helen-hr-operational-onboarding"
    commands = [command["command"] for command in recipe["commands"]]
    assert any("Helen_HR_Operational_Onboarding.md" in command for command in commands)
    assert any("resolve_personnel_identity('Helen')" in command for command in commands)
    assert any("onboarding-manifest-check --json" in command for command in commands)


def test_wp_0111_recipe_registered_and_self_validating():
    recipe = get_validation_recipe("WP-0111")
    assert recipe is not None
    assert recipe["recipe_id"] == "wp-0111-first-batch-burn-down-self-validation"
    commands = [command["command"] for command in recipe["commands"]]
    assert any("WP-0111_first_batch_report.md" in command for command in commands)
    assert any("WP-0111_first_batch_report.json" in command for command in commands)
    assert any("validate-work-package --id WP-0020 --json" in command for command in commands)
    assert any("validate_receipt('WP-0111')" in command for command in commands)


def test_wp_0111_recipe_uses_cross_platform_python_checks():
    recipe = get_validation_recipe("WP-0111")
    assert recipe is not None
    local_checks = [command["command"] for command in recipe["commands"] if "WP-0111_first_batch_report" in command["command"] or "validate_receipt('WP-0111')" in command["command"]]
    assert local_checks
    for command in local_checks:
        assert command.startswith("python -c ")
        assert "for id in" not in command
        assert " do " not in command
        assert "test -f" not in command
        assert "rg -q" not in command


def test_wp_0111_report_artifacts_identify_wp_0020_first_batch():
    md = open("operations/validation/backlog_burn_down/WP-0111_first_batch_report.md", encoding="utf-8").read()
    data = json.load(open("runtime/validation/backlog_burn_down/WP-0111_first_batch_report.json", encoding="utf-8"))
    assert data["selected_batch_package_ids"] == ["WP-0020"]
    pending = {item["work_package_id"] for item in data["packages_discovered_as_genuinely_pending_unimplemented"]}
    assert {"WP-0106", "WP-0107", "WP-0108", "WP-0109", "WP-0110"} <= pending
    assert "WP-0020" in md
    assert "pending/unimplemented" in md


def test_wp_0114_recipe_registered_and_self_validation_targets():
    recipe = get_validation_recipe("WP-0114")
    assert recipe is not None
    assert recipe["recipe_id"] == "wp-0114-historical-production-readiness-sweep"
    commands = [command["command"] for command in recipe["commands"]]
    assert any("WP-0114_historical_sweep_report.json" in command for command in commands)
    assert any("validation-production-readiness" in command for command in commands)
    assert any("WP-0102" in command for command in commands)
    assert any("validate_receipt('WP-0114')" in command for command in commands)


def test_wp_0113_generated_recipe_registered():
    recipe = get_validation_recipe("WP-0113")
    assert recipe is not None
    assert recipe["recipe_id"] == "wp-0113-helen-next-batch-recommendation"
    commands = [command["command"] for command in recipe["commands"]]
    assert any("WP-0113_helen_next_batch_recommendation.json" in command for command in commands)
    assert any("wp-0106" in command.lower() and "wp-0110" in command.lower() for command in commands)


def test_wp_0115_bootstrap_recipes_registered_and_guarded():
    representative = ["WP-0014", "WP-0022", "WP-0084", "WP-0104"]
    for work_package_id in representative:
        recipe = get_validation_recipe(work_package_id)
        assert recipe is not None
        assert recipe["recipe_id"].endswith("historical-receipt-artifact-presence")
        commands = [command["command"] for command in recipe["commands"]]
        assert all(command.startswith("python -c ") for command in commands)
        assert all("test -f" not in command and " do " not in command for command in commands)

    for skipped in ["WP-0016", "WP-0017", "WP-0018", "WP-0056", "WP-0073", "WP-0094", "WP-0106", "WP-0107", "WP-9999"]:
        recipe = get_validation_recipe(skipped)
        if recipe is not None:
            assert not recipe["recipe_id"].endswith("historical-receipt-artifact-presence")


def test_wp_0115_recipe_and_report_artifacts_registered_and_parse():
    recipe = get_validation_recipe("WP-0115")
    assert recipe is not None
    assert recipe["recipe_id"] == "wp-0115-historical-validation-recipe-bootstrap-sweep"
    commands = [command["command"] for command in recipe["commands"]]
    assert any("validation-production-readiness --json" in command for command in commands)
    assert any("validate-work-package --id WP-0114 --json" in command for command in commands)

    from pathlib import Path
    report_path = Path("runtime/validation/backlog_burn_down/WP-0115_recipe_bootstrap_report.json")
    assert Path("operations/validation/backlog_burn_down/WP-0115_recipe_bootstrap_report.md").is_file()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["production_readiness_totals_before"]
    assert report["production_readiness_totals_after"]
    assert report["packages_considered"]
    assert all(item.get("reason") for item in report["packages_skipped"])


def test_wp_0117_recipe_validates_office_snapshot_export():
    recipe = get_validation_recipe("WP-0117")
    assert recipe is not None
    assert recipe["recipe_id"] == "wp-0117-office-snapshot-export-button"
    commands = [command["command"] for command in recipe["commands"]]
    assert any("office-snapshot-button" in command for command in commands)
    assert any("build_office_snapshot_manifest" in command for command in commands)
    assert any("WP-0117_codex_done.json" in command for command in commands)

def test_wp_0118_recipe_validates_office_verb_surface_backlog_and_template():
    recipe = get_validation_recipe("WP-0118")
    assert recipe is not None
    assert recipe["recipe_id"] == "wp-0118-office-steward-verb-surface-control-backlog"
    commands = [command["command"] for command in recipe["commands"]]
    assert any("Office_of_the_Steward_Verb_Surface_Control_Backlog_v1.md" in command for command in commands)
    assert any("Office_Action_Surface_Work_Package_Template.md" in command for command in commands)
    assert any("OFFICE_TABS" in command for command in commands)
    assert any("safe read-only" in command for command in commands)
    assert any("Per-Tab Verb Matrix" in command for command in commands)
    assert any("validate_receipt('WP-0118')" in command for command in commands)


def test_wp_0121_final_four_recipes_registered():
    for work_package_id in ["WP-0016", "WP-0017", "WP-0073", "WP-0094", "WP-0121"]:
        recipe = get_validation_recipe(work_package_id)
        assert recipe is not None
        assert recipe["commands"]


def test_mission_control_validation_health_includes_wp0073_fields(tmp_path):
    import json
    from estate.core.mission_control_workspace import build_mission_control_workspace

    (tmp_path / "runtime/validation/work_packages").mkdir(parents=True)
    (tmp_path / "operations/validation").mkdir(parents=True)
    (tmp_path / "collaboration/work_packages/completions").mkdir(parents=True)
    (tmp_path / "validation/observations").mkdir(parents=True)
    (tmp_path / "validation/observations/validation_observations.jsonl").write_text(json.dumps({"status":"open","severity":"observation"}) + "\n", encoding="utf-8")
    (tmp_path / "runtime/validation/work_packages/latest.json").write_text(json.dumps({"work_package_id":"WP-TEST","validation_status":"passed","json_report":"runtime/validation/work_packages/WP-TEST_validation.json"}), encoding="utf-8")
    payload = build_mission_control_workspace(tmp_path, write=False)
    validation = payload["data"]["validation_health"]
    assert validation["open_observations_count"] == 1
    assert validation["confirmed_defects_count"] == 0
    assert validation["conditional_pass_count"] == 0
    assert validation["most_recent_validation_activity"]["work_package_id"] == "WP-TEST"
    assert validation["artifact_links"]


def test_operations_center_status_bar_exposes_wp0094_fields():
    from estate.core.steward_command_center import generate_command_center
    payload = generate_command_center(write=False)
    status = payload["status_bar"]
    required = {"estate_status", "validation_state", "active_workers", "active_recall_count", "pending_decisions", "health_state", "recommended_next_action"}
    assert required <= set(status)
    assert payload["layout_framework"]["data"]["quiet_refresh_regions"] == ["status_bar", "bottom_activity_stream"]
    assert payload["activity_console"]["collapsed_by_default"] is True
