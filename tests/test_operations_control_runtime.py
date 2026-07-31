import json
import subprocess
import sys
from pathlib import Path

from estate.core.operations_control_runtime import OperationsControlRuntime
from estate.core.operations_manager import OperationsDecision


def test_review_generation_no_upstream_artifacts_reports_warnings(tmp_path):
    review, paths = OperationsControlRuntime(tmp_path).generate_review()
    assert review.warnings
    assert Path(paths["summary_json"]).exists()
    assert Path(paths["summary_md"]).exists()


def test_review_generation_reads_provider_health_artifact(tmp_path):
    p = tmp_path / "runtime/providers/health/status/summary.json"
    p.parent.mkdir(parents=True)
    p.write_text(json.dumps({"available_count": 2, "blocked_count": 1, "out_of_quota_count": 1, "saturated_count": 3}), encoding="utf-8")
    review, _ = OperationsControlRuntime(tmp_path).generate_review()
    assert review.provider_available_count == 2
    assert review.provider_blocked_count == 2
    assert review.provider_saturated_count == 3


def test_review_generation_reads_assignment_board_artifact(tmp_path):
    p = tmp_path / "runtime/workers/assignments/status/board.json"
    p.parent.mkdir(parents=True)
    p.write_text(json.dumps({"active_count": 4, "blocked_count": 2}), encoding="utf-8")
    review, _ = OperationsControlRuntime(tmp_path).generate_review()
    assert review.assignment_active_count == 4
    assert review.assignment_blocked_count == 2


def test_decision_and_summary_artifacts_are_written(tmp_path):
    runtime = OperationsControlRuntime(tmp_path)
    decision = OperationsDecision.create(decided_by="Steward", decision_type="assign", target_type="work_package", target_id="WP-0609", reason="Assign", assignment_label="A2C2")
    paths = runtime.record_decision(decision)
    assert Path(paths["decision"]).exists()
    assert Path(paths["summary_json"]).exists()
    assert Path(paths["summary_md"]).exists()
    assert "A2C2" in Path(paths["decision"]).read_text(encoding="utf-8")


def test_cli_operations_review_succeeds(tmp_path):
    result = subprocess.run([sys.executable, "-m", "estate.cli.main", "operations-review"], cwd=tmp_path, env={"PYTHONPATH": str(Path.cwd() / "src"), "ESTATE_ROOT": str(tmp_path)}, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr + result.stdout
    assert "Operations review generated" in result.stdout


def test_cli_operations_decide_succeeds_for_valid_decision(tmp_path):
    result = subprocess.run([sys.executable, "-m", "estate.cli.main", "operations-decide", "--decision-type", "assign", "--target-type", "work_package", "--target-id", "WP-0609", "--assignment-label", "A2C2", "--decided-by", "Steward", "--reason", "Assign orchestration runtime to C2"], cwd=tmp_path, env={"PYTHONPATH": str(Path.cwd() / "src"), "ESTATE_ROOT": str(tmp_path)}, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr + result.stdout
    assert "A2C2" in result.stdout


def test_cli_operations_decide_fails_for_invalid_decision(tmp_path):
    result = subprocess.run([sys.executable, "-m", "estate.cli.main", "operations-decide", "--decision-type", "execute", "--target-type", "system", "--decided-by", "Steward", "--reason", "bad"], cwd=tmp_path, env={"PYTHONPATH": str(Path.cwd() / "src"), "ESTATE_ROOT": str(tmp_path)}, text=True, capture_output=True)
    assert result.returncode != 0


def test_cli_operations_decisions_list_succeeds_with_no_decisions(tmp_path):
    result = subprocess.run([sys.executable, "-m", "estate.cli.main", "operations-decisions-list"], cwd=tmp_path, env={"PYTHONPATH": str(Path.cwd() / "src"), "ESTATE_ROOT": str(tmp_path)}, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr + result.stdout
    assert "No operations decisions" in result.stdout


def test_codex_technical_decision_does_not_require_qwen_extension():
    decision = OperationsDecision.create(
        decided_by="Engineering", decision_type="authorize_dispatch", target_type="dispatch",
        reason="Bounded Codex review", technical_execution=True,
        selected_provider_id="codex.execution.cli", provider_extension=None,
    )
    decision.validate()


def test_steward_technical_intake_fails_closed_when_bounded_fields_are_missing(tmp_path):
    request = tmp_path / "request.json"
    request.write_text(json.dumps({"required_capability": "documentation_draft"}), encoding="utf-8")
    result = subprocess.run([
        sys.executable, "-m", "estate.cli.main", "grace-operations", "conduct",
        "--title", "missing technical intake", "--summary", "missing fields",
        "--technical-request-file", str(request), "--json",
    ], cwd=tmp_path, env={"PYTHONPATH": str(Path.cwd() / "src"), "ESTATE_ROOT": str(tmp_path)}, text=True, capture_output=True)
    assert result.returncode != 0
    assert "missing required governed fields" in result.stderr
