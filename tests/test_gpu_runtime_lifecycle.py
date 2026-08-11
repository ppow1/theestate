from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from estate.core.compute_office_panel import build_compute_panel
from estate.core.compute_resources import ComputeResourceObservation
from estate.core.gpu_runtime_lifecycle import ProcessRecord, emit_stale_runtime_blocked_event, inspect_gpu_runtime_lanes, quiesce_runtime_lane


GPU_A = "GPU-A"


def _setup(root: Path, *, lane_id="lane-a", gpu_uuid=GPU_A, resource_id="host:nvidia:GPU-A", pid=4100):
    lane = {
        "runtime_lane_id": lane_id, "provider_id": "qwen.local.text", "endpoint_type": "ollama-http",
        "endpoint_address": "http://127.0.0.1:12409", "host_id": "host", "compute_resource_id": resource_id,
        "gpu_uuid": gpu_uuid, "model_identity": "qwen3:8b",
        "environment_binding": {"CUDA_VISIBLE_DEVICES": gpu_uuid, "OLLAMA_HOST": "127.0.0.1:12409"},
    }
    path = root / "config/runtime/gpu_runtime_lanes.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"lanes": [lane]}), encoding="utf-8")
    executable = str((root / "bin/ollama.exe").resolve())
    started = "2026-08-11T18:00:00Z"
    evidence = {**lane, "process_id": pid, "process_identity": "ollama.exe serve", "executable_path": executable, "process_command_line": f'"{executable}" serve', "started_at": started, "observed_at": started}
    evidence_path = root / "runtime/compute_resources/runtime_lanes.json"
    evidence_path.parent.mkdir(parents=True)
    evidence_path.write_text(json.dumps({"lanes": [evidence]}), encoding="utf-8")
    (root / "runtime/engineering_scheduler").mkdir(parents=True)
    (root / "runtime/engineering_scheduler/compute_reservations.json").write_text("[]", encoding="utf-8")
    (root / "runtime/execution_dispatch").mkdir(parents=True)
    (root / "runtime/execution_dispatch/queue.json").write_text("[]", encoding="utf-8")
    (root / "runtime/execution_activity").mkdir(parents=True)
    (root / "runtime/execution_activity/current.json").write_text(json.dumps({"active": []}), encoding="utf-8")
    (root / "runtime/execution_adapters/reconciliation").mkdir(parents=True)
    process = ProcessRecord(pid=pid, parent_pid=1, name="ollama.exe", executable_path=executable, command_line=f'"{executable}" serve', created_at=started)
    return lane, process


def _telemetry(gpu_uuid=GPU_A, used=8000):
    return [ComputeResourceObservation(resource_id=f"host:nvidia:{gpu_uuid}", host_id="host", nvidia_uuid=gpu_uuid, name="GPU", memory_total_mib=16000, memory_used_mib=used, memory_free_mib=16000-used, utilization_percent=0)]


def test_estate_owned_idle_lane_without_reservation_is_quiescible(tmp_path):
    _, process = _setup(tmp_path)
    result = inspect_gpu_runtime_lanes(tmp_path, process_inventory=lambda: [process], port_inventory=lambda: {12409: process.pid}, now=datetime(2026, 8, 11, 18, 0, 30, tzinfo=timezone.utc))
    lane = result["lanes"][0]
    assert lane["ownership"] == "ESTATE_OWNED"
    assert lane["state"] == "IDLE"
    assert lane["quiesce_allowed"] is True


def test_windows_process_inventory_shape_preserves_pid_zero():
    record = ProcessRecord.from_dict({"ProcessId": 0, "ParentProcessId": 0, "Name": "System Idle Process"})
    assert record.pid == 0
    assert record.parent_pid == 0


def test_windows_powershell_date_and_command_quoting_correlate(tmp_path):
    _, process = _setup(tmp_path)
    millis = int(datetime(2026, 8, 11, 18, 0, tzinfo=timezone.utc).timestamp() * 1000)
    observed = ProcessRecord(**{**process.to_dict(), "command_line": process.command_line.replace('"', ''), "created_at": f"/Date({millis})/"})
    lane = inspect_gpu_runtime_lanes(tmp_path, process_inventory=lambda: [observed], port_inventory=lambda: {12409: observed.pid})["lanes"][0]
    assert lane["ownership"] == "ESTATE_OWNED"
    assert lane["quiesce_allowed"] is True


@pytest.mark.parametrize(("artifact", "payload", "gate"), [
    ("runtime/engineering_scheduler/compute_reservations.json", [{"reservation_id": "r1", "resource_id": "host:nvidia:GPU-A", "state": "reserved"}], "active_reservations"),
    ("runtime/execution_dispatch/queue.json", [{"dispatch_id": "d1", "state": "Running", "compute_resource_requirements": {"required_gpu_uuid": GPU_A}}], "active_dispatches"),
    ("runtime/execution_dispatch/queue.json", [{"dispatch_id": "d1", "state": "Ready", "provider_extension": {"runtime_lane_id": "lane-a"}}], "pending_tasks"),
    ("runtime/execution_activity/current.json", {"active": [{"request_id": "d1", "runtime_lane_id": "lane-a"}]}, "active_provider_invocations"),
])
def test_active_or_pending_governed_work_blocks_quiesce(tmp_path, artifact, payload, gate):
    _, process = _setup(tmp_path)
    (tmp_path / artifact).write_text(json.dumps(payload), encoding="utf-8")
    lane = inspect_gpu_runtime_lanes(tmp_path, process_inventory=lambda: [process], port_inventory=lambda: {12409: process.pid})["lanes"][0]
    assert lane["quiesce_allowed"] is False
    assert lane["gates"][gate]


def test_in_flight_reconciliation_blocks_quiesce(tmp_path):
    _, process = _setup(tmp_path)
    dispatch = {"dispatch_id": "d1", "state": "Validation", "provider_extension": {"runtime_lane_id": "lane-a"}}
    (tmp_path / "runtime/execution_dispatch/queue.json").write_text(json.dumps([dispatch]), encoding="utf-8")
    (tmp_path / "runtime/execution_adapters/reconciliation/d1.json").write_text(json.dumps({"dispatch_id": "d1", "status": "in_progress"}), encoding="utf-8")
    lane = inspect_gpu_runtime_lanes(tmp_path, process_inventory=lambda: [process], port_inventory=lambda: {12409: process.pid})["lanes"][0]
    assert lane["gates"]["in_flight_reconciliations"] == ["d1"]
    assert lane["quiesce_allowed"] is False


def test_unknown_ownership_and_external_port_owner_fail_closed(tmp_path):
    _, process = _setup(tmp_path)
    evidence_path = tmp_path / "runtime/compute_resources/runtime_lanes.json"
    payload = json.loads(evidence_path.read_text())
    payload["lanes"][0].pop("executable_path")
    evidence_path.write_text(json.dumps(payload), encoding="utf-8")
    lane = inspect_gpu_runtime_lanes(tmp_path, process_inventory=lambda: [process], port_inventory=lambda: {12409: 9999})["lanes"][0]
    assert lane["ownership"] == "UNKNOWN"
    assert lane["state"] == "UNKNOWN"
    assert lane["quiesce_allowed"] is False
    assert "unrelated PID 9999" in lane["gates"]["unknown_checks"][0]


def test_external_process_reusing_registered_pid_is_blocked(tmp_path):
    _, process = _setup(tmp_path)
    external = ProcessRecord(**{**process.to_dict(), "command_line": "ollama.exe unrelated"})
    lane = inspect_gpu_runtime_lanes(tmp_path, process_inventory=lambda: [external], port_inventory=lambda: {})["lanes"][0]
    assert lane["ownership"] == "EXTERNAL"
    assert lane["quiesce_allowed"] is False


def test_owned_child_is_cleaned_and_unrelated_same_gpu_process_is_untouched(tmp_path):
    _, root = _setup(tmp_path)
    child = ProcessRecord(pid=4200, parent_pid=root.pid, name="llama-server.exe", executable_path="C:/ollama/llama-server.exe", command_line="llama-server --model small", created_at=root.created_at)
    unrelated = ProcessRecord(pid=4300, parent_pid=1, name="other.exe", executable_path="C:/other.exe", command_line="other", created_at=root.created_at)
    current = {item.pid: item for item in (root, child, unrelated)}
    ports = {12409: root.pid}
    stopped = []
    def terminate(root_pid, children):
        stopped.extend(children + [root_pid])
        for pid in children + [root_pid]: current.pop(pid, None)
        ports.clear()
        return {"shutdown_requested": children + [root_pid], "forced_after_graceful_request": [], "errors": []}
    receipt = quiesce_runtime_lane(tmp_path, "lane-a", actor="operator", process_inventory=lambda: list(current.values()), port_inventory=lambda: dict(ports), terminate_owned_tree=terminate, telemetry=lambda: _telemetry())
    assert receipt["result"] == "COMPLETED"
    assert receipt["processes_exited"] is True
    assert receipt["port_released"] is True
    assert stopped == [child.pid, root.pid]
    assert unrelated.pid in current
    assert (tmp_path / receipt["receipt_path"]).is_file()
    schema = json.loads(Path("schemas/gpu_runtime_cleanup_receipt_v1.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(json.loads((tmp_path / receipt["receipt_path"]).read_text()))


def test_cleanup_failure_is_recorded_truthfully(tmp_path):
    _, root = _setup(tmp_path)
    receipt = quiesce_runtime_lane(tmp_path, "lane-a", actor="engineering", process_inventory=lambda: [root], port_inventory=lambda: {12409: root.pid}, terminate_owned_tree=lambda root_pid, children: {"shutdown_requested": [root_pid], "forced_after_graceful_request": [], "errors": ["shutdown failed"]}, telemetry=lambda: _telemetry())
    assert receipt["result"] == "FAILED"
    assert receipt["processes_exited"] is False
    assert receipt["port_released"] is False
    stored = json.loads((tmp_path / receipt["receipt_path"]).read_text())
    assert stored["errors"] == ["shutdown failed"]


def test_missing_required_gate_artifact_blocks_without_termination(tmp_path):
    _, root = _setup(tmp_path)
    (tmp_path / "runtime/execution_activity/current.json").unlink()
    calls = []
    receipt = quiesce_runtime_lane(tmp_path, "lane-a", actor="operator", process_inventory=lambda: [root], port_inventory=lambda: {12409: root.pid}, terminate_owned_tree=lambda *args: calls.append(args) or {}, telemetry=lambda: _telemetry())
    assert receipt["result"] == "BLOCKED"
    assert calls == []
    assert receipt["unknown_checks"]


def test_stopped_registry_is_safe_noop_not_pid_kill(tmp_path):
    _setup(tmp_path)
    calls = []
    receipt = quiesce_runtime_lane(tmp_path, "lane-a", actor="operator", process_inventory=lambda: [], port_inventory=lambda: {}, terminate_owned_tree=lambda *args: calls.append(args) or {}, telemetry=lambda: _telemetry())
    assert receipt["result"] == "ALREADY_STOPPED"
    assert calls == []


def test_operator_authority_is_required(tmp_path):
    _setup(tmp_path)
    with pytest.raises(PermissionError, match="authority"):
        quiesce_runtime_lane(tmp_path, "lane-a", actor="grace")


def test_office_projects_lifecycle_and_cleanup_state(tmp_path, monkeypatch):
    lane, _ = _setup(tmp_path)
    monkeypatch.setattr("estate.core.compute_office_panel.inspect_gpu_runtime_lanes", lambda root: {"lanes": [{"runtime_lane_id": "lane-a", "state": "STALE_CANDIDATE", "ownership": "ESTATE_OWNED", "quiesce_allowed": True, "stale_candidate": True, "last_cleanup_result": None}]})
    observation = ComputeResourceObservation(resource_id=lane["compute_resource_id"], host_id="host", nvidia_uuid=GPU_A, name="GPU", health_state="healthy", capacity_state="available")
    panel = build_compute_panel(tmp_path, observations=[observation])
    projected = panel["resources"][0]["runtime_lanes"][0]
    assert projected["lifecycle_state"] == "STALE_CANDIDATE"
    assert projected["quiesce_allowed"] is True


def test_stale_runtime_blocked_event_uses_existing_operational_event_log(tmp_path):
    _, process = _setup(tmp_path)
    path = emit_stale_runtime_blocked_event(tmp_path, "lane-a", process_inventory=lambda: [process], port_inventory=lambda: {12409: process.pid}, now=datetime(2026, 8, 11, 19, 0, tzinfo=timezone.utc))
    payload = json.loads((tmp_path / path).read_text().splitlines()[-1])
    assert payload["event_type"] == "GPU Runtime Stale Candidate"
    assert payload["requires_attention"] is True


def test_lifecycle_is_generic_for_multiple_resources(tmp_path):
    lane_a, process_a = _setup(tmp_path)
    lane_b = {**lane_a, "runtime_lane_id": "lane-b", "endpoint_address": "http://127.0.0.1:12100", "compute_resource_id": "host:nvidia:GPU-B", "gpu_uuid": "GPU-B", "environment_binding": {"CUDA_VISIBLE_DEVICES": "GPU-B", "OLLAMA_HOST": "127.0.0.1:12100"}}
    config = tmp_path / "config/runtime/gpu_runtime_lanes.json"
    config.write_text(json.dumps({"lanes": [lane_a, lane_b]}), encoding="utf-8")
    payload = json.loads((tmp_path / "runtime/compute_resources/runtime_lanes.json").read_text())
    payload["lanes"].append({**payload["lanes"][0], **lane_b, "process_id": 5100})
    (tmp_path / "runtime/compute_resources/runtime_lanes.json").write_text(json.dumps(payload), encoding="utf-8")
    status = inspect_gpu_runtime_lanes(tmp_path, process_inventory=lambda: [process_a], port_inventory=lambda: {12409: process_a.pid})
    assert {row["runtime_lane_id"] for row in status["lanes"]} == {"lane-a", "lane-b"}
    assert next(row for row in status["lanes"] if row["runtime_lane_id"] == "lane-b")["state"] == "STOPPED"


def test_cleanup_source_contains_no_gpu_reset_or_device_mutation():
    source = Path("src/estate/core/gpu_runtime_lifecycle.py").read_text(encoding="utf-8").lower()
    for forbidden in ("--gpu-reset", "devcon", "disable-pnpdevice", "enable-pnpdevice", "shutdown.exe", "restart-computer"):
        assert forbidden not in source
