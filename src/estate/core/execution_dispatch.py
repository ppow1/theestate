"""Provider-agnostic local execution dispatch queue.

The dispatch queue stores planned execution work and provider intent. It does
not schedule work intelligently or invoke live providers.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
import time
import uuid
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field, fields
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from estate.core.paths import ESTATE_ROOT

RUNTIME_DIR = Path("runtime/execution_dispatch")
QUEUE_OUTPUT = RUNTIME_DIR / "queue.json"
EVENTS_OUTPUT = RUNTIME_DIR / "events.jsonl"
QUEUE_LOCK = RUNTIME_DIR / ".queue.lock"
CURRENT_OUTPUT = RUNTIME_DIR / "current.json"
REPORT_OUTPUT = RUNTIME_DIR / "report.md"
HANDOFF_DIR = RUNTIME_DIR / "handoffs"

DISPATCH_STATES = {
    "Queued",
    "Waiting",
    "Ready",
    "Running",
    "Blocked",
    "Awaiting Approval",
    "Validation",
    "Completed",
    "Failed",
    "Cancelled",
}
TERMINAL_STATES = {"Completed", "Failed", "Cancelled"}
FUTURE_WORK_STATES = {"Queued", "Waiting", "Ready"}
ATTENTION_STATES = {"Blocked", "Awaiting Approval", "Failed"}
CODEX_PROVIDERS = {"codex-cli-openai", "codex-cli-ollama"}

REQUIRED_EVENT_TYPES = {
    "dispatch_enqueued",
    "dispatch_ready",
    "dispatch_started",
    "dispatch_blocked",
    "dispatch_awaiting_approval",
    "dispatch_cancelled",
    "dispatch_completed",
    "dispatch_failed",
    "dispatch_handoff_prepared",
    "dispatch_handoff_blocked",
    "dispatch_handoff_validated",
}
EVENT_TYPES = REQUIRED_EVENT_TYPES | {
    "dispatch_state_updated",
    "dispatch_waiting",
    "dispatch_validation",
}

STATE_EVENT_TYPES = {
    "Queued": "dispatch_enqueued",
    "Waiting": "dispatch_waiting",
    "Ready": "dispatch_ready",
    "Running": "dispatch_started",
    "Blocked": "dispatch_blocked",
    "Awaiting Approval": "dispatch_awaiting_approval",
    "Validation": "dispatch_validation",
    "Completed": "dispatch_completed",
    "Failed": "dispatch_failed",
    "Cancelled": "dispatch_cancelled",
}

PRIORITY_ORDER = {
    "Critical": 0,
    "Urgent": 0,
    "High": 1,
    "Normal": 2,
    "Medium": 2,
    "Low": 3,
}


def _root(root: str | Path | None = None) -> Path:
    if root is not None:
        return Path(root)
    return ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _safe_id(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", str(value).strip())
    return safe[:120] or f"dispatch-{uuid.uuid4().hex[:12]}"


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _coerce_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, tuple):
        return [str(item) for item in value]
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    return [str(value)]


def _clean_state(value: str | None) -> str:
    text = str(value or "Queued").strip()
    for state in DISPATCH_STATES:
        if state.lower() == text.lower():
            return state
    return text


def _jsonable(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    return value


@dataclass
class DispatchRequest:
    dispatch_id: str = field(default_factory=lambda: f"dispatch-{uuid.uuid4().hex[:12]}")
    work_package_id: str | None = None
    title: str | None = None
    requested_by: str = "Steward"
    assigned_worker: str | None = None
    provider: str | None = None
    profile_label: str | None = None
    classification: str | None = None
    priority: str = "Normal"
    state: str = "Queued"
    prompt_source: str | None = None
    sandbox: str = "read-only"
    model: str | None = None
    allowed_read_paths: list[str] = field(default_factory=list)
    allowed_write_paths: list[str] = field(default_factory=list)
    expected_outputs: list[str] = field(default_factory=list)
    allowed_providers: list[str] = field(default_factory=list)
    forbidden_providers: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    validation_commands: list[str] = field(default_factory=list)
    attention_required: bool = False
    attention_reason: str | None = None
    provider_metadata: dict[str, Any] = field(default_factory=dict)
    compute_resource_requirements: dict[str, Any] = field(default_factory=dict)
    created_at: str | None = None
    updated_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return _jsonable(asdict(self))


@dataclass
class DispatchQueueItem(DispatchRequest):
    block_reason: str | None = None
    result_reference: str | None = None
    handoff_reference: str | None = None


def dispatch_request_from_dict(data: dict[str, Any]) -> DispatchRequest:
    if not isinstance(data, dict):
        raise ValueError("dispatch request must be a JSON object")
    allowed = {field_info.name for field_info in fields(DispatchRequest)}
    values = {key: value for key, value in data.items() if key in allowed}
    now = _now()
    values.setdefault("dispatch_id", f"dispatch-{uuid.uuid4().hex[:12]}")
    values.setdefault("state", "Queued")
    values.setdefault("priority", "Normal")
    values.setdefault("created_at", now)
    values.setdefault("updated_at", values.get("created_at") or now)
    for key in (
        "allowed_read_paths",
        "allowed_write_paths",
        "allowed_providers",
        "forbidden_providers",
        "dependencies",
        "validation_commands",
        "expected_outputs",
    ):
        values[key] = _coerce_list(values.get(key))
    metadata = values.get("provider_metadata")
    values["provider_metadata"] = metadata if isinstance(metadata, dict) else {}
    requirements = values.get("compute_resource_requirements")
    values["compute_resource_requirements"] = requirements if isinstance(requirements, dict) else {}
    values["state"] = _clean_state(values.get("state"))
    return DispatchRequest(**values)


def dispatch_item_from_dict(data: dict[str, Any]) -> DispatchQueueItem:
    allowed = {field_info.name for field_info in fields(DispatchQueueItem)}
    values = {key: value for key, value in data.items() if key in allowed}
    request = dispatch_request_from_dict(values)
    return DispatchQueueItem(**request.to_dict(), block_reason=values.get("block_reason"), result_reference=values.get("result_reference"), handoff_reference=values.get("handoff_reference"))


def load_dispatch_request(path: str | Path) -> DispatchRequest:
    return dispatch_request_from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def _validate_request(request: DispatchRequest, root: Path | None = None) -> None:
    errors: list[str] = []
    if not str(request.dispatch_id or "").strip():
        errors.append("dispatch_id is required")
    if not str(request.classification or "").strip():
        errors.append("classification is required")
    if request.state not in DISPATCH_STATES:
        errors.append(f"state must be one of {sorted(DISPATCH_STATES)}")
    if request.allowed_providers and request.provider not in request.allowed_providers:
        errors.append("provider is not in allowed_providers")
    if request.provider and request.provider in request.forbidden_providers:
        errors.append("provider is forbidden")
    try:
        from estate.core.compute_resources import ComputeResourceRequirements
        requirements = ComputeResourceRequirements.from_dict(request.compute_resource_requirements)
        requirements.validate()
    except ValueError as exc:
        errors.append(f"compute resource requirements are invalid: {exc}")
    # Technical work is admitted to Dispatch only after Engineering has made a
    # durable authorization.  This deliberately does not affect ordinary
    # operational Dispatch items.
    technical = (request.provider_metadata or {}).get("technical_execution") is True
    if technical:
        metadata = request.provider_metadata or {}
        for key in (
            "grace_objective_id",
            "engineering_commission_id",
            "engineering_authorization_id",
            "helen_determination_id",
        ):
            if not str(metadata.get(key) or "").strip():
                errors.append(f"technical execution requires {key}")
        if metadata.get("capability_disposition") != "qualified_and_available":
            errors.append("technical execution requires qualified_and_available capability determination")
        binding = metadata.get("ptm_readiness")
        if not isinstance(binding, dict):
            errors.append("technical execution requires PTM readiness evidence")
        elif root is not None:
            try:
                from estate.core.ptm_readiness_integration import PtmReadinessGateError, revalidate_readiness
                revalidate_readiness(root, binding, commission_id=str(metadata.get("engineering_commission_id") or ""))
            except (PtmReadinessGateError, ValueError, OSError) as exc:
                errors.append(f"PTM readiness revalidation failed: {exc}")
    if errors:
        raise ValueError("; ".join(errors))


def _queue_path(root: Path) -> Path:
    return root / QUEUE_OUTPUT


@contextmanager
def _queue_mutation_lock(root: Path, *, timeout_seconds: float = 10.0):
    """Cross-process lock for the queue read/modify/atomic-replace section."""
    path = root / QUEUE_LOCK
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = path.open("a+b")
    handle.seek(0)
    if handle.tell() == 0:
        handle.write(b"0")
        handle.flush()
    acquired = False
    started = time.monotonic()
    try:
        while not acquired:
            try:
                if os.name == "nt":
                    import msvcrt
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                acquired = True
            except (OSError, BlockingIOError):
                if time.monotonic() - started >= timeout_seconds:
                    raise TimeoutError(f"timed out acquiring Dispatch queue lock: {path}")
                time.sleep(0.01)
        yield
    finally:
        if acquired:
            if os.name == "nt":
                import msvcrt
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()


def _events_path(root: Path) -> Path:
    return root / EVENTS_OUTPUT


def _read_queue_payload(root: Path) -> dict[str, Any]:
    path = _queue_path(root)
    if not path.exists():
        return {"version": 1, "updated_at": None, "items": []}
    last_error: json.JSONDecodeError | None = None
    last_permission_error: PermissionError | None = None
    for attempt in range(5):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            break
        except json.JSONDecodeError as exc:
            last_error = exc
            if attempt < 4:
                time.sleep(0.01)
            else:
                raise ValueError(f"execution dispatch queue is malformed JSON: {exc}") from exc
        except PermissionError as exc:
            last_permission_error = exc
            if attempt < 4:
                time.sleep(0.01)
            else:
                raise
    else:
        if last_permission_error is not None:
            raise last_permission_error
        raise ValueError(f"execution dispatch queue is malformed JSON: {last_error}")
    if isinstance(raw, list):
        return {"version": 1, "updated_at": None, "items": raw}
    if not isinstance(raw, dict):
        raise ValueError("execution dispatch queue must be a JSON object")
    raw.setdefault("items", [])
    return raw


def _write_queue(root: Path, items: list[DispatchQueueItem]) -> dict[str, Any]:
    payload = {
        "version": 1,
        "updated_at": _now(),
        "item_count": len(items),
        "items": [item.to_dict() for item in _sort_items(items)],
    }
    path = _queue_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    temporary_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent,
            prefix=f"{path.name}.", suffix=".tmp", delete=False,
        ) as handle:
            temporary_path = handle.name
            handle.write(serialized)
            handle.flush()
            os.fsync(handle.fileno())
        replacement_error: OSError | None = None
        for attempt in range(5):
            try:
                os.replace(temporary_path, path)
                replacement_error = None
                break
            except PermissionError as exc:
                replacement_error = exc
                if attempt < 4:
                    time.sleep(0.01)
        if replacement_error is not None:
            raise replacement_error
    finally:
        if temporary_path:
            try:
                os.unlink(temporary_path)
            except FileNotFoundError:
                pass
    return payload


def load_dispatch_queue(root: str | Path | None = None) -> list[DispatchQueueItem]:
    base = _root(root)
    payload = _read_queue_payload(base)
    items = []
    for raw in payload.get("items") or []:
        if isinstance(raw, dict):
            items.append(dispatch_item_from_dict(raw))
    return _sort_items(items)


def _priority_rank(priority: str | None) -> int:
    if not priority:
        return 9
    return PRIORITY_ORDER.get(str(priority).strip().title(), 9)


def _sort_items(items: list[DispatchQueueItem]) -> list[DispatchQueueItem]:
    return sorted(items, key=lambda item: (_priority_rank(item.priority), str(item.created_at or ""), str(item.dispatch_id or "")))


def _find_item(items: list[DispatchQueueItem], dispatch_id: str) -> DispatchQueueItem:
    for item in items:
        if item.dispatch_id == dispatch_id:
            return item
    raise KeyError(f"dispatch item not found: {dispatch_id}")


def _replace_item(items: list[DispatchQueueItem], updated: DispatchQueueItem) -> list[DispatchQueueItem]:
    replaced = False
    output: list[DispatchQueueItem] = []
    for item in items:
        if item.dispatch_id == updated.dispatch_id:
            output.append(updated)
            replaced = True
        else:
            output.append(item)
    if not replaced:
        raise KeyError(f"dispatch item not found: {updated.dispatch_id}")
    return _sort_items(output)


def _next_event_number(path: Path) -> int:
    if not path.exists():
        return 1
    try:
        return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip()) + 1
    except OSError:
        return 1


def _emit_event(root: Path, item: DispatchQueueItem, event_type: str, summary: str) -> dict[str, Any]:
    if event_type not in EVENT_TYPES:
        raise ValueError(f"unsupported dispatch event type: {event_type}")
    path = _events_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    sequence = _next_event_number(path)
    timestamp = _now()
    event = {
        "event_id": f"{_safe_id(item.dispatch_id)}-{sequence:04d}-{event_type}",
        "event_type": event_type,
        "source": "execution_dispatch",
        "dispatch_id": item.dispatch_id,
        "request_id": item.dispatch_id,
        "work_package_id": item.work_package_id,
        "title": item.title,
        "assigned_worker": item.assigned_worker,
        "worker_label": item.assigned_worker,
        "provider": item.provider,
        "profile_label": item.profile_label,
        "state": item.state,
        "current_state": item.state,
        "priority": item.priority,
        "classification": item.classification,
        "security_classification": item.classification,
        "timestamp": timestamp,
        "attention_required": bool(item.attention_required),
        "human_attention_required": bool(item.attention_required),
        "summary": summary,
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")
    return event


def _event_type_for_state(state: str) -> str:
    return STATE_EVENT_TYPES.get(state, "dispatch_state_updated")


def enqueue_dispatch_request(request: DispatchRequest | dict[str, Any], root: str | Path | None = None) -> DispatchQueueItem:
    base = _root(root)
    req = dispatch_request_from_dict(request) if isinstance(request, dict) else request
    now = _now()
    req.state = _clean_state(req.state)
    req.created_at = req.created_at or now
    req.updated_at = req.updated_at or req.created_at
    _validate_request(req, base)
    with _queue_mutation_lock(base):
        items = load_dispatch_queue(base)
        if any(item.dispatch_id == req.dispatch_id for item in items):
            raise ValueError(f"dispatch item already exists: {req.dispatch_id}")
        item = DispatchQueueItem(**req.to_dict())
        items.append(item)
        _write_queue(base, items)
    _emit_event(base, item, "dispatch_enqueued", f"Dispatch item {item.dispatch_id} queued.")
    generate_current_dispatch_snapshot(base, write=True)
    return item


def list_dispatch_items(root: str | Path | None = None, *, state: str | None = None) -> list[DispatchQueueItem]:
    items = load_dispatch_queue(root)
    if state is None:
        return items
    wanted = _clean_state(state)
    return [item for item in items if item.state == wanted]


def inspect_dispatch_item(dispatch_id: str, root: str | Path | None = None) -> DispatchQueueItem:
    return _find_item(load_dispatch_queue(root), dispatch_id)


def update_dispatch_state(
    dispatch_id: str,
    state: str,
    root: str | Path | None = None,
    *,
    summary: str | None = None,
    attention_required: bool | None = None,
) -> DispatchQueueItem:
    base = _root(root)
    new_state = _clean_state(state)
    if new_state not in DISPATCH_STATES:
        raise ValueError(f"state must be one of {sorted(DISPATCH_STATES)}")
    with _queue_mutation_lock(base):
        items = load_dispatch_queue(base)
        item = _find_item(items, dispatch_id)
        item.state = new_state
        item.updated_at = _now()
        if attention_required is None:
            if new_state in ATTENTION_STATES:
                item.attention_required = True
            elif new_state in TERMINAL_STATES | {"Running", "Ready"}:
                item.attention_required = False
        else:
            item.attention_required = bool(attention_required)
        items = _replace_item(items, item)
        _write_queue(base, items)
    event_type = _event_type_for_state(new_state)
    _emit_event(base, item, event_type, summary or f"Dispatch item {dispatch_id} state updated to {new_state}.")
    generate_current_dispatch_snapshot(base, write=True)
    return item


def block_dispatch_item(dispatch_id: str, reason: str, root: str | Path | None = None) -> DispatchQueueItem:
    base = _root(root)
    with _queue_mutation_lock(base):
        items = load_dispatch_queue(base)
        item = _find_item(items, dispatch_id)
        item.state = "Blocked"
        item.block_reason = reason
        item.attention_required = True
        item.attention_reason = reason
        item.updated_at = _now()
        items = _replace_item(items, item)
        _write_queue(base, items)
    _emit_event(base, item, "dispatch_blocked", f"Dispatch item {dispatch_id} blocked: {reason}")
    generate_current_dispatch_snapshot(base, write=True)
    return item


def mark_dispatch_attention(
    dispatch_id: str,
    root: str | Path | None = None,
    *,
    attention_required: bool = True,
    reason: str | None = None,
) -> DispatchQueueItem:
    base = _root(root)
    with _queue_mutation_lock(base):
        items = load_dispatch_queue(base)
        item = _find_item(items, dispatch_id)
        item.attention_required = bool(attention_required)
        item.attention_reason = reason if attention_required else None
        item.updated_at = _now()
        items = _replace_item(items, item)
        _write_queue(base, items)
    event_type = "dispatch_awaiting_approval" if attention_required else "dispatch_state_updated"
    summary = reason or ("Dispatch item requires Steward attention." if attention_required else "Dispatch item attention flag cleared.")
    _emit_event(base, item, event_type, summary)
    generate_current_dispatch_snapshot(base, write=True)
    return item


def cancel_dispatch_item(dispatch_id: str, root: str | Path | None = None, *, reason: str | None = None) -> DispatchQueueItem:
    summary = f"Dispatch item {dispatch_id} cancelled" + (f": {reason}" if reason else ".")
    return update_dispatch_state(dispatch_id, "Cancelled", root, summary=summary, attention_required=False)


def complete_dispatch_item(dispatch_id: str, root: str | Path | None = None, *, result_reference: str | None = None) -> DispatchQueueItem:
    base = _root(root)
    with _queue_mutation_lock(base):
        items = load_dispatch_queue(base)
        item = _find_item(items, dispatch_id)
        item.state = "Completed"
        item.result_reference = result_reference
        item.attention_required = False
        item.updated_at = _now()
        items = _replace_item(items, item)
        _write_queue(base, items)
    summary = f"Dispatch item {dispatch_id} completed" + (f"; result: {result_reference}" if result_reference else ".")
    _emit_event(base, item, "dispatch_completed", summary)
    generate_current_dispatch_snapshot(base, write=True)
    return item


def _ensure_codex_handoff_ready(item: DispatchQueueItem) -> None:
    errors: list[str] = []
    if item.provider not in CODEX_PROVIDERS:
        errors.append("Codex Bridge handoff requires provider codex-cli-openai or codex-cli-ollama")
    if not item.prompt_source:
        errors.append("prompt_source is required for Codex Bridge handoff")
    if not item.classification:
        errors.append("classification is required for Codex Bridge handoff")
    if not item.allowed_read_paths:
        errors.append("allowed_read_paths are required for Codex Bridge handoff")
    if item.sandbox == "workspace-write" and not item.allowed_write_paths:
        errors.append("workspace-write handoff requires allowed_write_paths")
    if errors:
        raise ValueError("; ".join(errors))


def prepare_codex_bridge_handoff(
    dispatch_id: str,
    root: str | Path | None = None,
    *,
    write: bool = True,
) -> dict[str, Any]:
    base = _root(root)
    items = load_dispatch_queue(base)
    item = _find_item(items, dispatch_id)
    _ensure_codex_handoff_ready(item)
    request = {
        "request_id": item.dispatch_id,
        "dispatch_id": item.dispatch_id,
        "work_package_id": item.work_package_id,
        "requested_by": item.requested_by,
        "provider": item.provider,
        "model": item.model,
        "codex_home_profile": item.profile_label or "default",
        "profile_label": item.profile_label,
        "worker_label": item.assigned_worker or "execution-dispatch",
        "cwd": ".",
        "sandbox": item.sandbox,
        "approval_policy": "never",
        "json_mode": True,
        "prompt_source": item.prompt_source,
        "classification": item.classification,
        "allowed_read_paths": item.allowed_read_paths,
        "allowed_write_paths": item.allowed_write_paths,
        "validation_commands": item.validation_commands,
        "cloud_allowed": False,
        "cloud_dispatch_requested": False,
        "cloud_apply_requested": False,
        "danger_full_access_requested": False,
        "bypass_flags": [],
        "dry_run": True,
        "handoff_mode": "dry_run_only_no_live_provider_invocation",
        "source": "execution_dispatch",
    }
    if write:
        path = base / HANDOFF_DIR / f"{_safe_id(item.dispatch_id)}_codex_bridge_request.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(_jsonable(request), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        with _queue_mutation_lock(base):
            latest_item = _find_item(load_dispatch_queue(base), dispatch_id)
            latest_item.handoff_reference = _rel(path, base)
            latest_item.updated_at = _now()
            _write_queue(base, _replace_item(load_dispatch_queue(base), latest_item))
            item = latest_item
    _emit_event(base, item, "dispatch_handoff_prepared", f"Codex Bridge dry-run handoff prepared for {dispatch_id}.")
    generate_current_dispatch_snapshot(base, write=True)
    if write:
        request["handoff_path"] = item.handoff_reference
    return request


def _state_items(items: list[DispatchQueueItem], state: str) -> list[dict[str, Any]]:
    return [item.to_dict() for item in _sort_items([item for item in items if item.state == state])]


def _attention_items(items: list[DispatchQueueItem]) -> list[dict[str, Any]]:
    return [item.to_dict() for item in _sort_items([item for item in items if item.attention_required])]


def _dependency_items(items: list[DispatchQueueItem]) -> list[dict[str, Any]]:
    waiting = [item for item in items if item.dependencies and item.state not in TERMINAL_STATES]
    return [item.to_dict() for item in _sort_items(waiting)]


def _provider_assignments(items: list[DispatchQueueItem]) -> list[dict[str, Any]]:
    buckets: dict[tuple[str, str], list[DispatchQueueItem]] = {}
    for item in items:
        provider = item.provider or "unknown"
        profile = item.profile_label or "no profile"
        buckets.setdefault((provider, profile), []).append(item)
    assignments = []
    for (provider, profile), bucket in buckets.items():
        state_counts: dict[str, int] = {}
        for item in bucket:
            state_counts[item.state] = state_counts.get(item.state, 0) + 1
        assignments.append(
            {
                "provider": provider,
                "profile_label": profile,
                "assigned_workers": sorted({item.assigned_worker for item in bucket if item.assigned_worker}),
                "work_package_ids": sorted({item.work_package_id for item in bucket if item.work_package_id}),
                "future_work_count": sum(1 for item in bucket if item.state in FUTURE_WORK_STATES),
                "running_count": sum(1 for item in bucket if item.state == "Running"),
                "blocked_count": sum(1 for item in bucket if item.state in {"Blocked", "Awaiting Approval"}),
                "attention_required_count": sum(1 for item in bucket if item.attention_required),
                "state_counts": dict(sorted(state_counts.items())),
                "saturation_status": "unknown",
                "capacity_known": False,
            }
        )
    return sorted(assignments, key=lambda item: (item["provider"], item["profile_label"]))


def build_current_dispatch_snapshot(
    items: list[DispatchQueueItem],
    *,
    generated_at: str | None = None,
) -> dict[str, Any]:
    state_counts = {state: sum(1 for item in items if item.state == state) for state in sorted(DISPATCH_STATES)}
    snapshot = {
        "version": 1,
        "generated_at": generated_at or _now(),
        "source": str(QUEUE_OUTPUT).replace("\\", "/"),
        "queue_path": str(QUEUE_OUTPUT).replace("\\", "/"),
        "events_path": str(EVENTS_OUTPUT).replace("\\", "/"),
        "report_path": str(REPORT_OUTPUT).replace("\\", "/"),
        "queued": _state_items(items, "Queued"),
        "waiting": _state_items(items, "Waiting"),
        "ready": _state_items(items, "Ready"),
        "running": _state_items(items, "Running"),
        "blocked": _state_items(items, "Blocked"),
        "awaiting_approval": _state_items(items, "Awaiting Approval"),
        "validation": _state_items(items, "Validation"),
        "attention_required": _attention_items(items),
        "waiting_on_dependencies": _dependency_items(items),
        "completed": _state_items(items, "Completed"),
        "failed": _state_items(items, "Failed"),
        "cancelled": _state_items(items, "Cancelled"),
        "provider_assignments": _provider_assignments(items),
        "summary": {
            "item_count": len(items),
            "queued_count": state_counts.get("Queued", 0),
            "waiting_count": state_counts.get("Waiting", 0),
            "ready_count": state_counts.get("Ready", 0),
            "running_count": state_counts.get("Running", 0),
            "blocked_count": state_counts.get("Blocked", 0) + state_counts.get("Awaiting Approval", 0),
            "awaiting_approval_count": state_counts.get("Awaiting Approval", 0),
            "validation_count": state_counts.get("Validation", 0),
            "attention_required_count": sum(1 for item in items if item.attention_required),
            "waiting_on_dependencies_count": sum(1 for item in items if item.dependencies and item.state not in TERMINAL_STATES),
            "completed_count": state_counts.get("Completed", 0),
            "failed_count": state_counts.get("Failed", 0),
            "cancelled_count": state_counts.get("Cancelled", 0),
            "provider_profile_assignment_count": len(_provider_assignments(items)),
            "state_counts": state_counts,
        },
        "office_integration": {
            "current_json_path": str(CURRENT_OUTPUT).replace("\\", "/"),
            "report_path": str(REPORT_OUTPUT).replace("\\", "/"),
            "cli_json_command": "python -m estate.cli.main execution-dispatch list --json",
            "cli_report_command": "python -m estate.cli.main execution-dispatch-report",
            "local_only": True,
            "does_not_dispatch_live_providers": True,
        },
        "provider_handoff": {
            "codex_bridge_dry_run_supported": True,
            "live_provider_invocation_default": False,
            "handoff_directory": str(HANDOFF_DIR).replace("\\", "/"),
        },
        "known_limitations": [
            "This is not the full Orchestrator.",
            "This does not decide final scheduling policy.",
            "This does not perform live provider execution by default.",
            "Provider saturation and quota data may remain unknown.",
            "ChatGPT CLI dispatch shape is not finalized.",
            "Final Operations Office authority remains an architectural question for Steward review.",
        ],
    }
    return _jsonable(snapshot)


def generate_current_dispatch_snapshot(
    root: str | Path | None = None,
    *,
    write: bool = True,
    generated_at: str | None = None,
) -> dict[str, Any]:
    base = _root(root)
    items = load_dispatch_queue(base)
    snapshot = build_current_dispatch_snapshot(items, generated_at=generated_at)
    if write:
        (base / RUNTIME_DIR).mkdir(parents=True, exist_ok=True)
        if not (base / QUEUE_OUTPUT).exists():
            with _queue_mutation_lock(base):
                if not (base / QUEUE_OUTPUT).exists():
                    _write_queue(base, items)
        if not (base / EVENTS_OUTPUT).exists():
            (base / EVENTS_OUTPUT).write_text("", encoding="utf-8")
        (base / CURRENT_OUTPUT).write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (base / REPORT_OUTPUT).write_text(format_execution_dispatch_report(snapshot) + "\n", encoding="utf-8")
    return snapshot


def format_execution_dispatch_report(snapshot: dict[str, Any]) -> str:
    summary = snapshot.get("summary") or {}
    lines = [
        "# Execution Dispatch Queue",
        "",
        f"Generated: {snapshot.get('generated_at')}",
        f"Source: `{snapshot.get('source')}`",
        "",
        "## Summary",
        f"- Items: {summary.get('item_count', 0)}",
        f"- Queued: {summary.get('queued_count', 0)}",
        f"- Ready: {summary.get('ready_count', 0)}",
        f"- Running: {summary.get('running_count', 0)}",
        f"- Blocked/Awaiting approval: {summary.get('blocked_count', 0)}",
        f"- Attention required: {summary.get('attention_required_count', 0)}",
        f"- Waiting on dependencies: {summary.get('waiting_on_dependencies_count', 0)}",
        "",
    ]
    for key, title in (
        ("queued", "Queued"),
        ("waiting", "Waiting"),
        ("ready", "Ready"),
        ("running", "Running"),
        ("blocked", "Blocked"),
        ("awaiting_approval", "Awaiting Approval"),
        ("validation", "Validation"),
        ("attention_required", "Requires Steward Attention"),
        ("waiting_on_dependencies", "Waiting On Dependencies"),
        ("failed", "Failed"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ):
        lines.append(f"## {title}")
        items = snapshot.get(key) or []
        if not items:
            lines.append("- None.")
        for item in items:
            deps = ", ".join(item.get("dependencies") or []) or "none"
            reason = item.get("block_reason") or item.get("attention_reason") or "No reason recorded."
            lines.append(
                "- "
                f"{item.get('dispatch_id')} | "
                f"{item.get('work_package_id') or 'unassigned'} | "
                f"{item.get('provider') or 'unknown provider'} | "
                f"{item.get('profile_label') or 'no profile'} | "
                f"{item.get('state')} | "
                f"priority={item.get('priority')} | "
                f"dependencies={deps} | "
                f"{reason}"
            )
        lines.append("")
    lines.append("## Provider/Profile Assignments")
    providers = snapshot.get("provider_assignments") or []
    if not providers:
        lines.append("- No provider assignments are queued.")
    for provider in providers:
        lines.append(
            "- "
            f"{provider.get('provider')} / {provider.get('profile_label')}: "
            f"future={provider.get('future_work_count')}, running={provider.get('running_count')}, "
            f"blocked={provider.get('blocked_count')}, attention={provider.get('attention_required_count')}, "
            f"saturation={provider.get('saturation_status')}"
        )
    lines.extend(
        [
            "",
            "## Boundary Notes",
            "- This queue stores local dispatch intent only.",
            "- It does not invoke Codex, OpenAI, ChatGPT, Ollama, GitHub, or browser providers by default.",
            "- Codex Bridge handoff files are dry-run request shapes for later explicit bridge execution.",
        ]
    )
    return "\n".join(lines)


def format_execution_dispatch_summary(snapshot: dict[str, Any]) -> str:
    summary = snapshot.get("summary") or {}
    return "\n".join(
        [
            "Execution Dispatch Queue",
            f"Generated: {snapshot.get('generated_at')}",
            f"Items: {summary.get('item_count', 0)}",
            f"Queued: {summary.get('queued_count', 0)}",
            f"Ready: {summary.get('ready_count', 0)}",
            f"Running: {summary.get('running_count', 0)}",
            f"Blocked: {summary.get('blocked_count', 0)}",
            f"Attention required: {summary.get('attention_required_count', 0)}",
            f"Current JSON: {CURRENT_OUTPUT}",
            f"Report: {REPORT_OUTPUT}",
        ]
    )


def format_dispatch_item(item: DispatchQueueItem) -> str:
    return "\n".join(
        [
            f"Dispatch: {item.dispatch_id}",
            f"Work package: {item.work_package_id or 'unassigned'}",
            f"Title: {item.title or 'Untitled dispatch'}",
            f"State: {item.state}",
            f"Provider: {item.provider or 'unknown'}",
            f"Profile: {item.profile_label or 'no profile'}",
            f"Priority: {item.priority}",
            f"Classification: {item.classification or 'missing'}",
            f"Attention required: {item.attention_required}",
            f"Prompt source: {item.prompt_source or 'not recorded'}",
        ]
    )
