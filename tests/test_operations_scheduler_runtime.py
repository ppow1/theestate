from datetime import datetime, timezone

from estate.core.operations_scheduler import OperationsScheduler
from estate.core.operations_scheduler_runtime import OperationsSchedulerRuntime


class FakeService:
    calls = []

    def __init__(self, root=None):
        self.root = root

    def run_once(self, **kwargs):
        self.calls.append(kwargs)
        return {"runtime_state": "stopped", "errors": [], "cycle_id": "fake"}


def test_runtime_runs_due_jobs_through_operations_runtime_service(tmp_path, monkeypatch):
    monkeypatch.setattr("estate.core.operations_scheduler_runtime.OperationsRuntimeService", FakeService)
    now = datetime(2000, 1, 1, 0, 0, tzinfo=timezone.utc)
    scheduler = OperationsScheduler(tmp_path, now=now)
    state = scheduler.load_state()
    state["jobs"]["health_refresh"]["next_run_at"] = "2000-01-01T00:00:00Z"
    scheduler.save_state(state)

    payload = OperationsSchedulerRuntime(tmp_path).run_due()

    assert payload["due_count"] >= 1
    assert any(call["mode"] == "observe-only" for call in FakeService.calls)
    assert scheduler.load_state()["jobs"]["health_refresh"]["lease"] is None


def test_runtime_executes_due_living_diagnostics_job(tmp_path, monkeypatch):
    monkeypatch.setattr("estate.core.operations_scheduler_runtime.OperationsRuntimeService", FakeService)
    monkeypatch.setattr("estate.core.operations_scheduler_runtime.reconcile", lambda root: {"reconciliation_outcome":"IMPLEMENTATION_UNCHANGED","changed_artifacts":[]})
    now=datetime(2000,1,1,0,0,tzinfo=timezone.utc); scheduler=OperationsScheduler(tmp_path,now=now)
    state=scheduler.load_state()
    for job_state in state["jobs"].values(): job_state["enabled"]=False
    state["jobs"]["living_diagnostics_full_reconciliation"].update({"enabled":True,"next_run_at":"2000-01-01T00:00:00Z"})
    scheduler.save_state(state)
    payload=OperationsSchedulerRuntime(tmp_path).run_due()
    assert payload["due_count"]==1 and payload["results"][0]["job_id"]=="living_diagnostics_full_reconciliation"
    assert payload["results"][0]["status"]=="completed" and payload["results"][0]["result"]["reconciliation_outcome"]=="IMPLEMENTATION_UNCHANGED"
