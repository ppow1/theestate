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


def test_run_once_cycle_produces_heartbeat_and_status(tmp_path):
    write_target(tmp_path)
    write_watch(tmp_path)
    cycle = OperationsRuntime(tmp_path).run_cycle()
    assert cycle["targets_evaluated"] == 1
    assert cycle["watches_evaluated"] == 1
    assert (tmp_path / "runtime/operations_runtime/heartbeat.json").exists()
    status = json.loads((tmp_path / "runtime/operations_runtime/status/latest.json").read_text())
    assert status["summary"]["operations_runtime_available"] is True
    assert status["provider_execution_performed"] is False
    assert status["dispatch_execution_performed"] is False
    assert "recovery_posture" in status["summary"]
    assert "recovery_pending_actions" in status["summary"]


def test_enabled_targets_evaluated_and_disabled_skipped(tmp_path):
    write_target(tmp_path, "enabled-target", "enabled")
    rt = OperationalTargetRuntime(tmp_path)
    targets = rt.load_targets()
    targets.append(OperationalTarget(**{**targets[0].to_dict(), "target_id": "paused-target", "watch_state": "paused", "watch_enabled": False}))
    rt.write_targets(targets)
    write_watch(tmp_path)
    cycle = OperationsRuntime(tmp_path).run_cycle()
    assert cycle["targets_evaluated"] == 1


def test_watches_create_governed_requests_and_audit_request(tmp_path):
    write_target(tmp_path)
    write_watch(tmp_path)
    cycle = OperationsRuntime(tmp_path).run_cycle()
    assert cycle["requests_created"] == 1
    assert cycle["audits_requested"] == 1
    requests = list((tmp_path / "runtime/background_operations/requests").glob("*.json"))
    assert requests
    payload = json.loads(requests[0].read_text())
    assert payload["requires_human_review"] is True
    assert payload["metadata"]["no_live_provider_calls"] is True


def test_no_provider_dispatch_or_tree_repair(tmp_path):
    dirty = tmp_path / "sentinel-dirty-file.txt"
    dirty.write_text("do not stash or repair", encoding="utf-8")
    write_target(tmp_path)
    write_watch(tmp_path)
    cycle = OperationsRuntime(tmp_path).run_cycle()
    assert dirty.exists()
    assert dirty.read_text(encoding="utf-8") == "do not stash or repair"
    assert cycle["provider_execution_performed"] is False
    assert cycle["dispatch_execution_performed"] is False
