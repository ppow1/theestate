"""Ownership-aware lifecycle control for governed GPU runtime lanes.

This module extends the registered runtime-lane process model.  It never
resets a GPU, mutates a device, or terminates a process based on its executable
name alone.  Every destructive operation is lane scoped and fails closed.
"""
from __future__ import annotations

import json
import os
import platform
import subprocess
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable
from uuid import uuid4

from estate.core.compute_resources import collect_nvidia_smi
from estate.core.gpu_runtime_lanes import LANE_EVIDENCE, RuntimeLane, load_registered_lanes
from estate.core.operational_events import OperationalEvent, append_event_artifact

CLEANUP_RECEIPTS = Path("runtime/compute_resources/cleanup_receipts")
LIFECYCLE_STATE = Path("runtime/compute_resources/runtime_lifecycle_state.json")
RESERVATIONS = Path("runtime/engineering_scheduler/compute_reservations.json")
DISPATCH_QUEUE = Path("runtime/execution_dispatch/queue.json")
ACTIVITY_CURRENT = Path("runtime/execution_activity/current.json")
RECONCILIATIONS = Path("runtime/execution_adapters/reconciliation")
ACTIVE_RESERVATION_STATES = {"active", "held", "pending", "reserved"}
ACTIVE_DISPATCH_STATES = {"Running"}
PENDING_DISPATCH_STATES = {"Awaiting Approval", "Queued", "Ready", "Waiting"}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class ProcessRecord:
    pid: int
    parent_pid: int | None
    name: str | None
    executable_path: str | None
    command_line: str | None
    created_at: str | None = None

    @classmethod
    def from_dict(cls, row: dict[str, Any]) -> "ProcessRecord":
        pid_value = row.get("ProcessId") if row.get("ProcessId") is not None else row.get("pid")
        parent_value = row.get("ParentProcessId") if row.get("ParentProcessId") is not None else row.get("parent_pid")
        return cls(
            pid=int(pid_value),
            parent_pid=int(parent_value) if parent_value is not None else None,
            name=row.get("Name") or row.get("name"),
            executable_path=row.get("ExecutablePath") or row.get("executable_path"),
            command_line=row.get("CommandLine") or row.get("command_line"),
            created_at=row.get("CreationDate") or row.get("created_at"),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _default_process_inventory() -> list[ProcessRecord]:
    if platform.system() != "Windows":
        return []
    script = "Get-CimInstance Win32_Process | Select-Object ProcessId,ParentProcessId,Name,ExecutablePath,CommandLine,CreationDate | ConvertTo-Json -Compress"
    result = subprocess.run(["powershell", "-NoProfile", "-Command", script], capture_output=True, text=True, timeout=15, check=False)
    if result.returncode != 0 or not result.stdout.strip():
        raise RuntimeError("Windows process inventory is unavailable")
    payload = json.loads(result.stdout)
    rows = payload if isinstance(payload, list) else [payload]
    return [ProcessRecord.from_dict(row) for row in rows if isinstance(row, dict) and row.get("ProcessId") is not None]


def _default_port_inventory() -> dict[int, int]:
    if platform.system() != "Windows":
        return {}
    script = "Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Select-Object LocalPort,OwningProcess | ConvertTo-Json -Compress"
    result = subprocess.run(["powershell", "-NoProfile", "-Command", script], capture_output=True, text=True, timeout=15, check=False)
    if result.returncode != 0:
        raise RuntimeError("Windows listening-port inventory is unavailable")
    if not result.stdout.strip():
        return {}
    payload = json.loads(result.stdout)
    rows = payload if isinstance(payload, list) else [payload]
    return {int(row["LocalPort"]): int(row["OwningProcess"]) for row in rows if isinstance(row, dict) and row.get("LocalPort") is not None and row.get("OwningProcess") is not None}


def _default_terminate_owned_tree(root_pid: int, child_pids: list[int]) -> dict[str, Any]:
    """Ask each already-proven owned process to exit, then force only survivors."""
    before = {item.pid: item for item in _default_process_inventory() if item.pid in {root_pid, *child_pids}}
    requested: list[int] = []
    errors: list[str] = []
    for pid in list(reversed(child_pids)) + [root_pid]:
        result = subprocess.run(["taskkill", "/PID", str(pid)], capture_output=True, text=True, timeout=10, check=False)
        requested.append(pid)
        if result.returncode != 0 and "not found" not in (result.stderr or "").lower():
            errors.append(f"PID {pid}: {(result.stderr or result.stdout).strip()[:300]}")
    time.sleep(1.0)
    after = {item.pid: item for item in _default_process_inventory() if item.pid in set(requested)}
    survivors = {pid for pid, item in after.items() if before.get(pid) == item}
    changed_identity = set(after) - survivors
    for pid in sorted(changed_identity):
        errors.append(f"PID {pid} identity changed during shutdown; force termination refused")
    forced: list[int] = []
    for pid in sorted(survivors):
        result = subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True, text=True, timeout=10, check=False)
        forced.append(pid)
        if result.returncode != 0 and "not found" not in (result.stderr or "").lower():
            errors.append(f"PID {pid} force: {(result.stderr or result.stdout).strip()[:300]}")
    return {"shutdown_requested": requested, "forced_after_graceful_request": forced, "errors": errors}


def _read_json(path: Path) -> tuple[Any, str | None]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except (OSError, json.JSONDecodeError) as exc:
        return None, f"{path.as_posix()}: {exc}"


def _contains_identity(value: Any, lane: RuntimeLane) -> bool:
    identities = {lane.runtime_lane_id, lane.compute_resource_id, lane.gpu_uuid}
    if isinstance(value, dict):
        return any(_contains_identity(item, lane) for item in value.values())
    if isinstance(value, list):
        return any(_contains_identity(item, lane) for item in value)
    return isinstance(value, str) and value in identities


def _rows(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        if isinstance(value.get("items"), list):
            return [item for item in value["items"] if isinstance(item, dict)]
        return [value]
    return []


def _lane_port(lane: RuntimeLane) -> int:
    from urllib.parse import urlparse
    return int(urlparse(lane.endpoint_address).port or 0)


def _descendants(root_pid: int, by_pid: dict[int, ProcessRecord]) -> list[ProcessRecord]:
    result: list[ProcessRecord] = []
    frontier = [root_pid]
    seen = {root_pid}
    while frontier:
        parent = frontier.pop()
        children = [item for item in by_pid.values() if item.parent_pid == parent and item.pid not in seen]
        result.extend(children)
        frontier.extend(item.pid for item in children)
        seen.update(item.pid for item in children)
    return result


def _parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _root_ownership(evidence: dict[str, Any], process: ProcessRecord | None) -> tuple[str, list[str]]:
    if process is None:
        return "ESTATE_OWNED_STOPPED", ["registered root PID is not running"]
    expected_path = evidence.get("executable_path")
    expected_command = evidence.get("process_command_line")
    expected_started = _parse_time(evidence.get("started_at"))
    observed_started = _parse_time(process.created_at)
    if not expected_path or not expected_command or expected_started is None or observed_started is None:
        return "UNKNOWN", ["registry lacks production-grade executable, command, or process-start evidence"]
    if os.path.normcase(os.path.abspath(str(expected_path))) != os.path.normcase(os.path.abspath(str(process.executable_path or ""))):
        return "EXTERNAL", ["registered executable path does not match the live PID"]
    if str(process.command_line or "").strip().lower() != str(expected_command).strip().lower():
        return "EXTERNAL", ["registered command line does not match the live PID"]
    if abs((observed_started - expected_started).total_seconds()) > 15:
        return "EXTERNAL", ["registered start time does not match the live PID creation time"]
    return "ESTATE_OWNED", ["PID, executable, command line, and process start match the registered lane root"]


def _gate_evidence(base: Path, lane: RuntimeLane) -> dict[str, Any]:
    unknown: list[str] = []
    reservations, error = _read_json(base / RESERVATIONS)
    if error:
        unknown.append(error)
        reservation_rows: list[dict[str, Any]] = []
    else:
        reservation_rows = [row for row in _rows(reservations) if row.get("resource_id") == lane.compute_resource_id and str(row.get("state") or "").lower() in ACTIVE_RESERVATION_STATES]

    dispatches, error = _read_json(base / DISPATCH_QUEUE)
    if error:
        unknown.append(error)
        dispatch_rows: list[dict[str, Any]] = []
    else:
        dispatch_rows = [row for row in _rows(dispatches) if _contains_identity(row, lane)]
    active_dispatches = [row for row in dispatch_rows if row.get("state") in ACTIVE_DISPATCH_STATES]
    pending_tasks = [row for row in dispatch_rows if row.get("state") in PENDING_DISPATCH_STATES]

    activity, error = _read_json(base / ACTIVITY_CURRENT)
    if error:
        unknown.append(error)
        active_provider: list[dict[str, Any]] = []
    else:
        active_provider = [row for row in (activity.get("active", []) if isinstance(activity, dict) else []) if isinstance(row, dict) and _contains_identity(row, lane)]

    in_flight_reconciliation: list[str] = []
    recon_dir = base / RECONCILIATIONS
    if not recon_dir.is_dir():
        unknown.append(f"{RECONCILIATIONS.as_posix()}: directory is unavailable")
    else:
        dispatch_ids = {str(row.get("dispatch_id")) for row in dispatch_rows if row.get("dispatch_id")}
        for path in recon_dir.glob("*.json"):
            payload, recon_error = _read_json(path)
            if recon_error:
                unknown.append(recon_error)
            elif isinstance(payload, dict) and str(payload.get("dispatch_id")) in dispatch_ids and payload.get("status") not in {"reconciled", "completed"}:
                in_flight_reconciliation.append(str(payload.get("dispatch_id")))
    return {
        "active_reservations": [row.get("reservation_id") for row in reservation_rows],
        "active_dispatches": [row.get("dispatch_id") for row in active_dispatches],
        "active_provider_invocations": [row.get("request_id") for row in active_provider],
        "pending_tasks": [row.get("dispatch_id") for row in pending_tasks],
        "in_flight_reconciliations": in_flight_reconciliation,
        "unknown_checks": unknown,
    }


def _lane_evidence(base: Path) -> dict[str, dict[str, Any]]:
    payload, _ = _read_json(base / LANE_EVIDENCE)
    return {str(row.get("runtime_lane_id")): row for row in (payload.get("lanes", []) if isinstance(payload, dict) else []) if isinstance(row, dict)}


def _persisted_states(base: Path) -> dict[str, dict[str, Any]]:
    payload, _ = _read_json(base / LIFECYCLE_STATE)
    return {str(row.get("runtime_lane_id")): row for row in (payload.get("lanes", []) if isinstance(payload, dict) else []) if isinstance(row, dict)}


def _write_lane_state(base: Path, lane: RuntimeLane, state: str, *, cleanup_id: str | None = None, result: str | None = None) -> None:
    path = base / LIFECYCLE_STATE
    existing = _persisted_states(base)
    existing[lane.runtime_lane_id] = {"runtime_lane_id": lane.runtime_lane_id, "resource_id": lane.compute_resource_id, "gpu_uuid": lane.gpu_uuid, "state": state, "cleanup_id": cleanup_id, "cleanup_result": result, "updated_at": utc_now()}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"schema_version": "estate.gpu-runtime-lifecycle-state.v1", "lanes": list(existing.values())}, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def inspect_gpu_runtime_lanes(root: str | Path, *, lane_id: str | None = None,
                              process_inventory: Callable[[], list[ProcessRecord]] | None = None,
                              port_inventory: Callable[[], dict[int, int]] | None = None,
                              now: datetime | None = None) -> dict[str, Any]:
    base = Path(root)
    lanes = [lane for lane in load_registered_lanes(base) if lane_id is None or lane.runtime_lane_id == lane_id]
    if lane_id and not lanes:
        raise ValueError(f"unknown registered runtime lane: {lane_id}")
    errors: list[str] = []
    try:
        processes = (process_inventory or _default_process_inventory)()
        ports = (port_inventory or _default_port_inventory)()
    except Exception as exc:
        processes, ports = [], {}
        errors.append(str(exc)[:500])
    by_pid = {item.pid: item for item in processes}
    evidence = _lane_evidence(base)
    persisted_states = _persisted_states(base)
    current = now or datetime.now(timezone.utc)
    rows: list[dict[str, Any]] = []
    for lane in lanes:
        lane_record = evidence.get(lane.runtime_lane_id, {})
        root_pid = int(lane_record["process_id"]) if lane_record.get("process_id") is not None else None
        root_process = by_pid.get(root_pid) if root_pid is not None else None
        ownership, ownership_reasons = _root_ownership(lane_record, root_process)
        children = _descendants(root_pid, by_pid) if root_pid is not None and root_process is not None else []
        port = _lane_port(lane)
        port_owner = ports.get(port)
        owned_pids = {root_pid, *(item.pid for item in children)} if root_pid is not None else set()
        gates = _gate_evidence(base, lane)
        blockers = [key for key in ("active_reservations", "active_dispatches", "active_provider_invocations", "pending_tasks", "in_flight_reconciliations") if gates[key]]
        if port_owner is not None and port_owner not in owned_pids:
            gates["unknown_checks"].append(f"lane port {port} is owned by unrelated PID {port_owner}")
        heartbeat = _parse_time(lane_record.get("observed_at"))
        stale = bool(heartbeat and (current - heartbeat).total_seconds() > lane.freshness_seconds)
        persisted = persisted_states.get(lane.runtime_lane_id, {})
        if persisted.get("state") == "QUIESCING" and ownership == "ESTATE_OWNED":
            state = "QUIESCING"
        elif persisted.get("state") == "CLEANUP_FAILURE" and ownership == "ESTATE_OWNED":
            state = "CLEANUP_FAILURE"
        elif errors or gates["unknown_checks"] or ownership in {"UNKNOWN", "EXTERNAL"}:
            state = "UNKNOWN"
        elif ownership == "ESTATE_OWNED_STOPPED":
            state = "STOPPED"
        elif blockers:
            state = "ACTIVE"
        elif stale:
            state = "STALE_CANDIDATE"
        else:
            state = "IDLE"
        quiesce_allowed = ownership == "ESTATE_OWNED" and not blockers and not gates["unknown_checks"] and not errors
        rows.append({
            "runtime_lane_id": lane.runtime_lane_id, "provider_id": lane.provider_id,
            "resource_id": lane.compute_resource_id, "gpu_uuid": lane.gpu_uuid,
            "endpoint_address": lane.endpoint_address, "port": port,
            "state": state, "ownership": ownership, "ownership_reasons": ownership_reasons,
            "root_pid": root_pid, "root_process": root_process.to_dict() if root_process else None,
            "child_pids": [item.pid for item in children], "children": [item.to_dict() for item in children],
            "port_owner_pid": port_owner, "gates": gates, "stale_candidate": stale,
            "quiesce_allowed": quiesce_allowed,
            "last_cleanup_id": persisted.get("cleanup_id"), "last_cleanup_result": persisted.get("cleanup_result"),
        })
    return {"schema_version": "estate.gpu-runtime-lifecycle-status.v1", "observed_at": utc_now(), "read_only": True, "lanes": rows, "errors": errors}


def _gpu_memory(gpu_uuid: str, telemetry: Callable[[], Iterable[Any]]) -> dict[str, Any] | None:
    item = next((row for row in telemetry() if getattr(row, "nvidia_uuid", None) == gpu_uuid), None)
    return None if item is None else {"memory_used_mib": item.memory_used_mib, "memory_free_mib": item.memory_free_mib, "memory_total_mib": item.memory_total_mib, "utilization_percent": item.utilization_percent, "observed_at": item.observation_timestamp}


def _write_receipt(base: Path, receipt: dict[str, Any]) -> str:
    path = base / CLEANUP_RECEIPTS / f"{receipt['cleanup_id']}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return str(path.relative_to(base)).replace("\\", "/")


def _emit_cleanup_event(base: Path, lane: RuntimeLane, result: str, receipt_path: str) -> None:
    succeeded = result in {"COMPLETED", "ALREADY_STOPPED"}
    event = OperationalEvent.create(
        event_type="GPU Runtime Cleanup Succeeded" if succeeded else "GPU Runtime Cleanup Failed",
        state="Completed" if succeeded else "Failed", classification="Estate Internal",
        message=f"GPU runtime cleanup {result.lower()} for lane {lane.runtime_lane_id}.",
        provider_id=lane.provider_id, requires_attention=not succeeded,
        artifact_paths=[receipt_path], metadata={"runtime_lane_id": lane.runtime_lane_id, "resource_id": lane.compute_resource_id, "gpu_uuid": lane.gpu_uuid},
    )
    append_event_artifact(event, base, allow_extension_event_types=True)


def emit_stale_runtime_blocked_event(root: str | Path, lane_id: str, *,
                                     process_inventory: Callable[[], list[ProcessRecord]] | None = None,
                                     port_inventory: Callable[[], dict[int, int]] | None = None,
                                     now: datetime | None = None) -> str:
    """Scheduler hook for a stale owned lane that is blocking admission."""
    base = Path(root)
    status = inspect_gpu_runtime_lanes(base, lane_id=lane_id, process_inventory=process_inventory, port_inventory=port_inventory, now=now)["lanes"][0]
    if status["ownership"] != "ESTATE_OWNED" or not status["stale_candidate"]:
        raise ValueError("stale-runtime event requires positive owned stale-lane evidence")
    event = OperationalEvent.create(
        event_type="GPU Runtime Stale Candidate", state="Blocked", classification="Estate Internal",
        message=f"Stale Estate-owned GPU runtime {lane_id} is blocking scheduling.",
        provider_id=status["provider_id"], requires_attention=True,
        metadata={"runtime_lane_id": lane_id, "resource_id": status["resource_id"], "gpu_uuid": status["gpu_uuid"]},
    )
    return str(append_event_artifact(event, base, allow_extension_event_types=True).relative_to(base)).replace("\\", "/")


def quiesce_runtime_lane(root: str | Path, lane_id: str, *, actor: str,
                         process_inventory: Callable[[], list[ProcessRecord]] | None = None,
                         port_inventory: Callable[[], dict[int, int]] | None = None,
                         terminate_owned_tree: Callable[[int, list[int]], dict[str, Any]] | None = None,
                         telemetry: Callable[[], Iterable[Any]] | None = None) -> dict[str, Any]:
    if actor not in {"engineering", "operator", "scheduler-runtime-cleanup"}:
        raise PermissionError("GPU runtime quiesce requires operator, engineering, or scheduler-runtime-cleanup authority")
    base = Path(root)
    lane = next((item for item in load_registered_lanes(base) if item.runtime_lane_id == lane_id), None)
    if lane is None:
        raise ValueError(f"unknown registered runtime lane: {lane_id}")
    process_source = process_inventory or _default_process_inventory
    port_source = port_inventory or _default_port_inventory
    telemetry_source = telemetry or collect_nvidia_smi
    before = inspect_gpu_runtime_lanes(base, lane_id=lane_id, process_inventory=process_source, port_inventory=port_source)
    status = before["lanes"][0]
    cleanup_id = f"gpu-cleanup-{uuid4().hex}"
    receipt: dict[str, Any] = {
        "schema_version": "estate.gpu-runtime-cleanup-receipt.v1", "cleanup_id": cleanup_id,
        "timestamp": utc_now(), "actor": actor, "runtime_lane_id": lane.runtime_lane_id,
        "resource_id": lane.compute_resource_id, "gpu_uuid": lane.gpu_uuid,
        "root_pid": status["root_pid"], "child_pids": status["child_pids"],
        "ownership": status["ownership"], "pre_cleanup_state": status["state"],
        "active_reservations_checked": status["gates"]["active_reservations"],
        "active_dispatches_checked": status["gates"]["active_dispatches"],
        "active_provider_invocations_checked": status["gates"]["active_provider_invocations"],
        "pending_tasks_checked": status["gates"]["pending_tasks"],
        "in_flight_reconciliations_checked": status["gates"]["in_flight_reconciliations"],
        "unknown_checks": status["gates"]["unknown_checks"],
        "pre_cleanup_gpu": _gpu_memory(lane.gpu_uuid, telemetry_source),
        "shutdown_requested": [], "forced_after_graceful_request": [],
        "processes_exited": False, "port_released": status["port_owner_pid"] is None,
        "post_cleanup_gpu": None, "result": "BLOCKED", "errors": [],
    }
    if status["ownership"] == "ESTATE_OWNED_STOPPED":
        receipt.update({"result": "ALREADY_STOPPED", "processes_exited": True, "post_cleanup_gpu": _gpu_memory(lane.gpu_uuid, telemetry_source)})
    elif not status["quiesce_allowed"]:
        receipt["errors"] = ["ownership or inactivity gates did not prove this lane is safe to quiesce"]
    else:
        _write_lane_state(base, lane, "QUIESCING", cleanup_id=cleanup_id)
        outcome = (terminate_owned_tree or _default_terminate_owned_tree)(int(status["root_pid"]), list(status["child_pids"]))
        receipt["shutdown_requested"] = outcome.get("shutdown_requested", [])
        receipt["forced_after_graceful_request"] = outcome.get("forced_after_graceful_request", [])
        receipt["errors"] = outcome.get("errors", [])
        after = inspect_gpu_runtime_lanes(base, lane_id=lane_id, process_inventory=process_source, port_inventory=port_source)
        after_status = after["lanes"][0]
        receipt["processes_exited"] = after_status["root_process"] is None and not after_status["child_pids"]
        receipt["port_released"] = after_status["port_owner_pid"] is None
        receipt["post_cleanup_gpu"] = _gpu_memory(lane.gpu_uuid, telemetry_source)
        receipt["result"] = "COMPLETED" if receipt["processes_exited"] and receipt["port_released"] and not receipt["errors"] else "FAILED"
    receipt_path = _write_receipt(base, receipt)
    receipt["receipt_path"] = receipt_path
    final_state = "STOPPED" if receipt["result"] in {"COMPLETED", "ALREADY_STOPPED"} else "CLEANUP_FAILURE"
    _write_lane_state(base, lane, final_state, cleanup_id=cleanup_id, result=receipt["result"])
    _emit_cleanup_event(base, lane, receipt["result"], receipt_path)
    return receipt
