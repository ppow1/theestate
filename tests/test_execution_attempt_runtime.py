from datetime import datetime, timezone

import pytest

from estate.core.execution_attempt_runtime import ExecutionAttemptRuntime
from estate.core.execution_provider_adapter import ExecutionProviderAdapterResult


class Clock:
    def __init__(self):
        self.value = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
    def __call__(self):
        return self.value.isoformat(timespec="seconds").replace("+00:00", "Z")
    def set(self, minute):
        self.value = datetime(2026, 1, 1, 0, minute, tzinfo=timezone.utc)


class FakeProcess:
    def __init__(self, observe="process_unknown", cancel=True):
        self.observe_state = observe
        self.cancel = cancel
        self.calls = []
    def observe(self, *, process_id, process_identity, attempt):
        self.calls.append(("observe", process_id, process_identity))
        return self.observe_state
    def request_cancel(self, *, process_id, process_identity, attempt):
        self.calls.append(("cancel", process_id, process_identity))
        return {"status": "cancellation_signal_sent" if self.cancel else "cancellation_failed", "verified_owner": self.cancel, "signal_sent": self.cancel}


def acquire(runtime, dispatch="D1"):
    return runtime.acquire_lease(dispatch_id=dispatch, adapter_request_id=f"A-{dispatch}", provider_id="codex", provider_type="codex-cli", work_package_id="WP-0507", execution_authorization_id="AUTH", workspace_commit="abc")


def test_first_lease_duplicate_independent_and_malformed(tmp_path):
    rt = ExecutionAttemptRuntime(root=tmp_path, clock=Clock())
    first = acquire(rt, "D1")
    assert first["status"] == "acquired"
    with pytest.raises(ValueError, match="active execution lease"):
        acquire(rt, "D1")
    assert acquire(rt, "D2")["status"] == "acquired"
    (tmp_path / "runtime/execution_adapters/leases/BAD.json").parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / "runtime/execution_adapters/leases/BAD.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="malformed"):
        acquire(rt, "BAD")


def test_matching_and_mismatched_heartbeat_and_observer_states(tmp_path):
    clock = Clock(); proc = FakeProcess("process_alive")
    rt = ExecutionAttemptRuntime(root=tmp_path, clock=clock, process_controller=proc, stale_after_seconds=30)
    attempt = acquire(rt)["attempt"]
    assert rt.heartbeat("D1", attempt["execution_attempt_id"], observer_state="process_alive")["status"] == "heartbeat_recorded"
    with pytest.raises(ValueError, match="does not own"):
        rt.heartbeat("D1", "wrong")
    assert rt.inspect_recovery("D1")["classification"] == "running and healthy"
    proc.observe_state = "process_missing"
    assert rt.inspect_recovery("D1")["classification"] == "process missing and no result"
    # unknown + stale is safe for explicit release
    rt2 = ExecutionAttemptRuntime(root=tmp_path / "two", clock=clock, process_controller=FakeProcess("process_unknown"), stale_after_seconds=30)
    a2 = acquire(rt2)["attempt"]["execution_attempt_id"]
    clock.set(2)
    inspection = rt2.inspect_recovery("D1")
    assert inspection["heartbeat_stale"] is True
    assert inspection["stale_release_safe"] is True
    with pytest.raises(ValueError, match="confirm"):
        rt2.release_stale("D1", a2)
    assert rt2.release_stale("D1", a2, confirm_stale_release=True)["status"] == "stale_released"


def test_cancellation_success_failure_and_unknown_outcome(tmp_path):
    clock = Clock(); proc = FakeProcess(cancel=True)
    rt = ExecutionAttemptRuntime(root=tmp_path, clock=clock, process_controller=proc)
    attempt = acquire(rt)["attempt"]["execution_attempt_id"]
    payload = rt.request_cancellation("D1", attempt, requested_by="tester", reason="stop")
    assert payload["cooperative_signal"]["signal_sent"] is True
    assert rt.inspect_recovery("D1")["classification"] == "cancellation requested but outcome unknown"
    rt_fail = ExecutionAttemptRuntime(root=tmp_path / "fail", clock=clock, process_controller=FakeProcess(cancel=False))
    attempt2 = acquire(rt_fail)["attempt"]["execution_attempt_id"]
    assert rt_fail.request_cancellation("D1", attempt2, reason="stop")["cooperative_signal"]["status"] == "cancellation_failed"


def test_completion_releases_lease_and_non_stale_release_blocked(tmp_path):
    rt = ExecutionAttemptRuntime(root=tmp_path, clock=Clock(), process_controller=FakeProcess("process_alive"))
    attempt = acquire(rt)["attempt"]["execution_attempt_id"]
    with pytest.raises(ValueError, match="not proven"):
        rt.release_stale("D1", attempt, confirm_stale_release=True)
    assert rt.complete_attempt(attempt, status="completed", result_reference="result.json")["lease_released"] is True
    assert rt.active_for_dispatch("D1") is None
    a2 = acquire(rt, "D2")["attempt"]["execution_attempt_id"]
    assert rt.complete_attempt(a2, status="failed")["lease_released"] is True


def test_retry_eligibility_no_auto_retry_late_result_and_idempotent_status(tmp_path):
    rt = ExecutionAttemptRuntime(root=tmp_path, clock=Clock())
    attempt = acquire(rt)["attempt"]["execution_attempt_id"]
    rt.complete_attempt(attempt, status="cancelled")
    retry = rt.retry_eligibility("D1")
    assert retry["retry_eligible"] is True
    assert retry["automatic_retry_started"] is False
    result = ExecutionProviderAdapterResult(adapter_request_id="A-D1", dispatch_id="D1", provider_id="codex", status="completed", started_at="2026-01-01T00:00:00Z", artifacts=["artifact.txt"])
    late = rt.preserve_late_result(result, attempt_id=attempt, result_reference="runtime/execution_adapters/results/A-D1.json")
    assert late["late_or_superseded"] is True
    assert rt.status("D1") == rt.status("D1")
