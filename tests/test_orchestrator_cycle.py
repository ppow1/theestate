import json
import subprocess
import sys
from pathlib import Path

from estate.core.orchestrator_cycle import OrchestratorCycleRuntime
from estate.core.provider_capacity import ProviderCapacityRecord, write_capacity_record
from estate.core.provider_health import ProviderHealthRecord, write_health_record


def write_catalog(root, status="implemented"):
    path = root / "config/providers/catalog.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"capabilities":[{"capability_id":"implementation","display_name":"Implementation","description":"x","category":"execution","classification":"Estate Internal"}],"providers":[{"provider_id":"prov.execution","display_name":"Provider","provider_type":"execution","implementation_kind":"manual","status":status,"classification_ceiling":"Estate Internal","capabilities":["implementation"]}]}), encoding="utf-8")


def write_schedule(root, **overrides):
    item = {"schedule_id":"sch-1","intake_id":"int-1","created_at":"2026-01-01T00:00:00Z","updated_at":"2026-01-01T00:00:00Z","scheduled_by":"test","state":"scheduled","priority":"normal","classification":"Estate Internal","provider_id":"prov.execution","required_capabilities":["implementation"],"validation_required":True,"approval_reference":"dec-1","mission":"Mission","summary":"Summary","metadata":{"summary_safe": True}}
    item.update(overrides)
    path = root / "runtime/orchestrator/schedule/status/queue.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"scheduled":[item],"deferred":[],"blocked":[]}), encoding="utf-8")
    return item


def make_available(root):
    write_health_record(ProviderHealthRecord.create(provider_id="prov.execution", status="available", reported_by="test", message="ok"), root=root, force=True)
    write_capacity_record(ProviderCapacityRecord.create(provider_id="prov.execution", capacity_state="available", reported_by="test"), root=root, force=True)


def test_dry_run_with_no_work_exits_cleanly_and_writes_no_dispatch(tmp_path):
    state = OrchestratorCycleRuntime(root=tmp_path).run_cycle(dry_run=True)
    assert state.items_evaluated == 0
    assert not list((tmp_path / "runtime/orchestrator/dispatch/pending").glob("*.json"))


def test_single_cycle_with_no_work_exits_cleanly(tmp_path):
    state = OrchestratorCycleRuntime(root=tmp_path).run_cycle(dry_run=False)
    assert state.state == "completed_with_warnings"


def test_eligible_scheduled_item_creates_pending_dispatch(tmp_path):
    write_catalog(tmp_path); write_schedule(tmp_path); make_available(tmp_path)
    state = OrchestratorCycleRuntime(root=tmp_path).run_cycle()
    assert state.dispatches_created == 1
    assert list((tmp_path / "runtime/orchestrator/dispatch/pending").glob("*.json"))


def test_missing_approval_creates_blocked_dispatch(tmp_path):
    write_catalog(tmp_path); write_schedule(tmp_path, approval_reference=None); make_available(tmp_path)
    OrchestratorCycleRuntime(root=tmp_path).run_cycle()
    data = json.loads(next((tmp_path / "runtime/orchestrator/dispatch/blocked").glob("*.json")).read_text())
    assert "Approval" in data["blocked_reason"]


def test_missing_boundary_review_creates_blocked_dispatch(tmp_path):
    write_catalog(tmp_path); write_schedule(tmp_path, boundary_review_required=True); make_available(tmp_path)
    OrchestratorCycleRuntime(root=tmp_path).run_cycle()
    data = json.loads(next((tmp_path / "runtime/orchestrator/dispatch/blocked").glob("*.json")).read_text())
    assert "Boundary" in data["blocked_reason"]


def test_provider_unavailable_creates_deferred_dispatch(tmp_path):
    write_catalog(tmp_path); write_schedule(tmp_path)
    state = OrchestratorCycleRuntime(root=tmp_path).run_cycle()
    assert state.items_deferred == 1


def test_provider_blocked_creates_blocked_dispatch(tmp_path):
    write_catalog(tmp_path, status="blocked"); write_schedule(tmp_path); make_available(tmp_path)
    OrchestratorCycleRuntime(root=tmp_path).run_cycle()
    data = json.loads(next((tmp_path / "runtime/orchestrator/dispatch/blocked").glob("*.json")).read_text())
    assert "blocked" in data["blocked_reason"]


def test_unknown_provider_catalog_creates_deferred_dispatch(tmp_path):
    write_schedule(tmp_path)
    OrchestratorCycleRuntime(root=tmp_path).run_cycle()
    assert list((tmp_path / "runtime/orchestrator/dispatch/deferred").glob("*.json"))


def test_dispatch_queue_and_runtime_status_written(tmp_path):
    write_catalog(tmp_path); write_schedule(tmp_path); make_available(tmp_path)
    OrchestratorCycleRuntime(root=tmp_path).run_cycle()
    assert (tmp_path / "runtime/orchestrator/dispatch/status/queue.json").exists()
    assert (tmp_path / "runtime/orchestrator/runtime/status/latest.json").exists()


def test_cli_commands_succeed(tmp_path):
    env = {"PYTHONPATH": str(Path.cwd() / "src")}
    r = subprocess.run([sys.executable, "-m", "estate.cli.main", "orchestrator-cycle", "--dry-run"], cwd=Path.cwd(), env=env, text=True, capture_output=True)
    assert r.returncode == 0
    r = subprocess.run([sys.executable, "-m", "estate.cli.main", "orchestrator-cycle", "--single"], cwd=Path.cwd(), env=env, text=True, capture_output=True)
    assert r.returncode == 0
    r = subprocess.run([sys.executable, "-m", "estate.cli.main", "orchestrator-dispatch-list"], cwd=Path.cwd(), env=env, text=True, capture_output=True)
    assert r.returncode == 0


def test_malformed_upstream_artifact_reports_warning_or_error(tmp_path):
    path = tmp_path / "runtime/orchestrator/schedule/status/queue.json"
    path.parent.mkdir(parents=True)
    path.write_text("{bad", encoding="utf-8")
    state = OrchestratorCycleRuntime(root=tmp_path).run_cycle()
    assert state.errors
