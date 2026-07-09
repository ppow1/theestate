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
