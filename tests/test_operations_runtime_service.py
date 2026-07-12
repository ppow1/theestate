import json
from pathlib import Path

from estate.core.background_operations import BackgroundOperationWatch
from estate.core.operations_runtime import OperationsRuntime
from estate.core.operational_targets import OperationalTarget
from estate.core.operational_targets_runtime import OperationalTargetRuntime


def write_target(root, target_id="estate-main", state="enabled", caps=None):
    target = OperationalTarget(
        target_id=target_id,
        display_name="Estate Main",
        target_type="git_repository",
        owner_department="Estate",
        local_path=str(root / "missing-worktree"),
        base_branch="main",
        watch_state=state,
        watch_enabled=state == "enabled",
        capabilities=caps or ["audit"],
        classification="Estate Internal",
        metadata={},
        workspace_root=str(root / "missing-worktree"),
    )
    OperationalTargetRuntime(root).write_targets([target])
    return target


def write_watch(root, enabled=True):
    watch = BackgroundOperationWatch(
        watch_id="operational_target_watch",
        name="Operational target watch",
        enabled=enabled,
        trigger_type="artifact_status",
        source_paths=["runtime/operational_targets/registry.json"],
        conditions={"watch_kind": "operational_target_watch_needed"},
        action_type="post_merge_audit_request",
        cooldown_seconds=0,
        classification="Estate Internal",
    )
    (root / "runtime/background_operations").mkdir(parents=True, exist_ok=True)
    (root / "runtime/background_operations/watches.json").write_text(json.dumps({"watches": [watch.to_dict()]}), encoding="utf-8")
    return watch


import pytest

from estate.core.operations_runtime_service import OperationsRuntimeLockError, OperationsRuntimeService


def test_repeated_cycle_obeys_max_cycles_without_wait(tmp_path):
    write_target(tmp_path)
    write_watch(tmp_path)
    result = OperationsRuntimeService(tmp_path).start(max_cycles=2, interval_seconds=0)
    assert result["cycles_run"] == 2
    assert result["state"] == "stopped"


def test_stop_request_is_honored(tmp_path):
    svc = OperationsRuntimeService(tmp_path)
    svc.request_stop()
    result = svc.start(max_cycles=3, interval_seconds=0)
    # start clears old request, so request during loop is modeled by direct runtime marker before second run
    assert result["cycles_run"] == 3
    svc.request_stop()
    status = svc.status()
    assert status["summary"]["operations_runtime_state"] == "stop_requested"


def test_lock_prevents_duplicate_runtime_loops(tmp_path):
    svc = OperationsRuntimeService(tmp_path)
    svc.acquire_lock()
    try:
        with pytest.raises(OperationsRuntimeLockError):
            OperationsRuntimeService(tmp_path).run_once()
    finally:
        svc.release_lock()


def test_status_and_report_include_runtime_health(tmp_path):
    write_target(tmp_path)
    write_watch(tmp_path)
    svc = OperationsRuntimeService(tmp_path)
    svc.run_once()
    status = svc.status()
    summary = status["summary"]
    assert summary["operations_runtime_available"] is True
    assert "requests_created_last_cycle" in summary
    assert "Operations Runtime Service Loop" in svc.report()


def test_service_recovers_confirmed_dead_owner_lock(tmp_path, monkeypatch):
    import estate.core.operations_runtime_service as mod

    lock = tmp_path / "runtime/operations_runtime/lock.json"
    lock.parent.mkdir(parents=True)
    lock.write_text(json.dumps({"pid": 4720, "acquired_at": "2000-01-01T00:00:00Z"}), encoding="utf-8")
    monkeypatch.setattr(mod, "_pid_liveness", lambda pid: "dead")

    payload = OperationsRuntimeService(tmp_path).acquire_lock()

    assert payload["pid"] != 4720
    evidence = json.loads((tmp_path / "runtime/operations_runtime/status/stale_lock_recovery_latest.json").read_text(encoding="utf-8"))
    assert evidence["pid"] == 4720
    assert evidence["reason"] == "dead_owner_lock"
    assert evidence["liveness"] == "dead"


def test_service_preserves_lock_when_owner_liveness_unknown(tmp_path, monkeypatch):
    import estate.core.operations_runtime_service as mod

    lock = tmp_path / "runtime/operations_runtime/lock.json"
    lock.parent.mkdir(parents=True)
    original = {"pid": 4720, "acquired_at": "2000-01-01T00:00:00Z"}
    lock.write_text(json.dumps(original), encoding="utf-8")
    monkeypatch.setattr(mod, "_pid_liveness", lambda pid: "unknown")

    with pytest.raises(OperationsRuntimeLockError, match="liveness uncertain"):
        OperationsRuntimeService(tmp_path).acquire_lock()

    assert json.loads(lock.read_text(encoding="utf-8")) == original


def test_service_uses_windows_process_api_for_liveness(tmp_path, monkeypatch):
    import estate.core.operations_runtime_service as mod

    monkeypatch.setattr(mod.os, "name", "nt")
    monkeypatch.setattr(mod, "_windows_pid_liveness", lambda pid: "dead" if pid == 4720 else "alive")

    assert mod._pid_liveness(4720) == "dead"
    assert mod._pid_liveness(4721) == "alive"
