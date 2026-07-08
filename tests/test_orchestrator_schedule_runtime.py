import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from estate.core.orchestrator_intake import OrchestratorIntakeRequest
from estate.core.orchestrator_intake_decisions import OrchestratorIntakeDecisionRuntime
from estate.core.orchestrator_intake_runtime import OrchestratorIntakeRuntime
from estate.core.orchestrator_schedule_runtime import OrchestratorScheduleRuntime


def payload(intake_id="schedule-1", **overrides):
    data = {
        "intake_id": intake_id,
        "created_at": "2026-07-08T00:00:00Z",
        "requested_by": "tests",
        "source": "manual",
        "classification": "Estate Internal",
        "mission": "Prepare schedule item",
        "summary": "Safe schedule summary.",
        "priority": "normal",
        "metadata": {"summary_safe": True},
    }
    data.update(overrides)
    return data


def submit_approved(root, intake_id="schedule-1", **overrides):
    OrchestratorIntakeRuntime(root).submit(OrchestratorIntakeRequest.from_dict(payload(intake_id, **overrides)))
    OrchestratorIntakeDecisionRuntime(root).decide(intake_id=intake_id, decision="approve", decided_by="Steward", metadata={"summary_safe": True, "boundary_review_completed": True})


def copy_catalog(root):
    target = root / "config" / "providers"
    target.mkdir(parents=True)
    shutil.copy(Path("config/providers/catalog.json"), target / "catalog.json")


def test_valid_approved_intake_schedules_successfully(tmp_path):
    copy_catalog(tmp_path)
    submit_approved(tmp_path, "approved-ok")
    record, paths = OrchestratorScheduleRuntime(tmp_path).schedule(intake_id="approved-ok", scheduled_by="tests")
    assert record.state == "scheduled"
    assert Path(paths["artifact"]).exists()
    assert "/scheduled/" in paths["artifact"].replace("\\", "/")


def test_rejected_intake_creates_blocked_record(tmp_path):
    OrchestratorIntakeRuntime(tmp_path).submit(OrchestratorIntakeRequest.from_dict(payload("rejected")))
    OrchestratorIntakeDecisionRuntime(tmp_path).decide(intake_id="rejected", decision="reject", decided_by="Steward")
    record, paths = OrchestratorScheduleRuntime(tmp_path).schedule(intake_id="rejected")
    assert record.state == "blocked"
    assert "rejected" in record.blocked_reason
    assert "/blocked/" in paths["artifact"].replace("\\", "/")


def test_needs_revision_intake_creates_blocked_record(tmp_path):
    OrchestratorIntakeRuntime(tmp_path).submit(OrchestratorIntakeRequest.from_dict(payload("revision")))
    OrchestratorIntakeDecisionRuntime(tmp_path).decide(intake_id="revision", decision="mark_needs_revision", decided_by="Steward")
    record, _ = OrchestratorScheduleRuntime(tmp_path).schedule(intake_id="revision")
    assert record.state == "blocked"
    assert "needs_revision" in record.blocked_reason


def test_restricted_without_boundary_review_creates_blocked_record(tmp_path):
    request = payload("restricted", classification="Restricted", boundary_review_required=True, metadata={"summary_safe": True, "approval": True})
    OrchestratorIntakeRuntime(tmp_path).submit(OrchestratorIntakeRequest.from_dict(request))
    record, _ = OrchestratorScheduleRuntime(tmp_path).schedule(intake_id="restricted")
    assert record.state == "blocked"
    assert "Boundary review" in record.blocked_reason


def test_unavailable_provider_creates_deferred_record(tmp_path):
    copy_catalog(tmp_path)
    submit_approved(tmp_path, "missing-provider", requested_provider_id="missing.provider", requested_provider_type="execution")
    record, paths = OrchestratorScheduleRuntime(tmp_path).schedule(intake_id="missing-provider")
    assert record.state == "deferred"
    assert "not registered" in record.metadata["deferred_reason"]
    assert "/deferred/" in paths["artifact"].replace("\\", "/")


def test_provider_capability_mismatch_creates_blocked_record(tmp_path):
    copy_catalog(tmp_path)
    submit_approved(tmp_path, "cap-mismatch", requested_provider_id="estate.audit.local", requested_provider_type="validation", required_capabilities=["repository_implementation"])
    record, _ = OrchestratorScheduleRuntime(tmp_path).schedule(intake_id="cap-mismatch")
    assert record.state == "blocked"
    assert "Provider requirements" in record.blocked_reason


def test_queue_status_artifact_written_with_all_states(tmp_path):
    copy_catalog(tmp_path)
    submit_approved(tmp_path, "scheduled")
    OrchestratorScheduleRuntime(tmp_path).schedule(intake_id="scheduled")
    OrchestratorScheduleRuntime(tmp_path).schedule(intake_id="missing")
    queue = json.loads((tmp_path / "runtime/orchestrator/schedule/status/queue.json").read_text())
    assert queue["scheduled"]
    assert queue["blocked"]


def run_cli(args, cwd):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")
    return subprocess.run([sys.executable, "-m", "estate.cli.main", *args], cwd=cwd, text=True, capture_output=True, env=env)


def test_cli_schedule_works_for_approved_request_file(tmp_path):
    request = tmp_path / "approved.json"
    request.write_text(json.dumps(payload("cli-schedule", state="approved", metadata={"summary_safe": True, "approval": True})), encoding="utf-8")
    result = run_cli(["orchestrator-schedule", "--request", str(request)], Path.cwd())
    assert result.returncode == 0, result.stdout + result.stderr
    assert "SCHEDULED" in result.stdout


def test_cli_schedule_clearly_reports_blocked_intake(tmp_path):
    request = tmp_path / "blocked.json"
    request.write_text(json.dumps(payload("cli-blocked", state="rejected", metadata={"summary_safe": True})), encoding="utf-8")
    result = run_cli(["orchestrator-schedule", "--request", str(request)], Path.cwd())
    assert result.returncode == 0
    assert "BLOCKED" in result.stdout
    assert "Blocked reason" in result.stdout


def test_cli_list_succeeds_with_empty_queue(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = run_cli(["orchestrator-schedule-list"], Path.cwd())
    assert result.returncode == 0
    assert "Orchestrator Schedule Queue" in result.stdout


def test_cli_list_reports_scheduled_deferred_blocked_items(tmp_path):
    scheduled = tmp_path / "scheduled.json"
    deferred = tmp_path / "deferred.json"
    blocked = tmp_path / "blocked.json"
    scheduled.write_text(json.dumps(payload("cli-list-s", state="approved", metadata={"approval": True, "summary_safe": True})), encoding="utf-8")
    deferred.write_text(json.dumps(payload("cli-list-d", state="approved", requested_provider_id="missing", metadata={"approval": True, "summary_safe": True})), encoding="utf-8")
    blocked.write_text(json.dumps(payload("cli-list-b", state="rejected", metadata={"summary_safe": True})), encoding="utf-8")
    assert run_cli(["orchestrator-schedule", "--request", str(scheduled)], Path.cwd()).returncode == 0
    assert run_cli(["orchestrator-schedule", "--request", str(deferred)], Path.cwd()).returncode == 0
    assert run_cli(["orchestrator-schedule", "--request", str(blocked)], Path.cwd()).returncode == 0
    result = run_cli(["orchestrator-schedule-list"], Path.cwd())
    assert result.returncode == 0
    assert "cli-list-s" in result.stdout
    assert "cli-list-d" in result.stdout
    assert "cli-list-b" in result.stdout
