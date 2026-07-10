import json

from estate.core.office_end_to_end_regression import run_office_end_to_end_regression
from estate.core.work_package_validation import get_validation_recipe


def test_wp0521_recipe_registered():
    recipe = get_validation_recipe("WP-0521")
    assert recipe is not None
    commands = [command["command"] for command in recipe["commands"]]
    assert any("test_office_end_to_end_regression.py" in command for command in commands)


def test_office_end_to_end_regression_writes_required_outputs(tmp_path):
    payload = run_office_end_to_end_regression(tmp_path, validate=False)
    assert payload["work_package_id"] == "WP-0521"
    assert payload["passed"] is True
    assert all(payload["browser_checks"].values())
    assert all(item["passed"] for item in payload["primary_workflows"])
    assert all(item["passed"] for item in payload["recovery_workflows"])

    required = [
        "runtime/steward/office_end_to_end_regression.json",
        "runtime/steward/office_operational_readiness.json",
        "operations/steward/office_operational_readiness.md",
        "runtime/steward/office_remaining_defects.json",
        "collaboration/work_packages/completions/WP-0521_codex_done.json",
    ]
    for rel in required:
        assert (tmp_path / rel).exists(), rel

    readiness = json.loads((tmp_path / "runtime/steward/office_operational_readiness.json").read_text())
    completion = json.loads((tmp_path / "collaboration/work_packages/completions/WP-0521_codex_done.json").read_text())
    assert readiness["institutional_acceptance_granted"] is False
    assert completion["parallel_office_created"] is False
    assert completion["provider_router_created"] is False
    assert completion["validation_recipe_registered"] is True


def test_recovery_paths_are_truthful_and_diagnostics_visible(tmp_path):
    payload = run_office_end_to_end_regression(tmp_path, validate=False)
    by_case = {item["case"]: item for item in payload["recovery_workflows"]}
    assert by_case["malformed_or_unregistered_action"]["result"]["outcome"] == "blocked"
    for item in payload["recovery_workflows"]:
        assert item["result"]["steward_message"]
        assert item["result"]["source_handler"]
