"""Operations Runtime service model and cycle coordinator.

The runtime observes local Estate artifacts and creates governed requests/status only.
It never executes providers, dispatch queues, repair logic, stash, or acceptance flows.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from estate.core.background_operations_runtime import BackgroundOperationsRuntime, format_background_operations_report
from estate.core.operational_targets_runtime import OperationalTargetRuntime
from estate.core.paths import ESTATE_ROOT

RUNTIME_BASE = Path("runtime/operations_runtime")
STATUS_DIR = RUNTIME_BASE / "status"
REPORTS_DIR = RUNTIME_BASE / "reports"
CYCLES_DIR = RUNTIME_BASE / "cycles"
HEARTBEAT = RUNTIME_BASE / "heartbeat.json"
LOCK = RUNTIME_BASE / "lock.json"
STOP_REQUEST = RUNTIME_BASE / "stop_requested.json"
ALLOWED_RUNTIME_STATES = {"idle", "starting", "running", "sleeping", "stop_requested", "stopped", "blocked", "failed"}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _root(root: Path | None = None) -> Path:
    return root or (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


@dataclass
class OperationsRuntimeCycle:
    cycle_id: str
    started_at: str
    finished_at: str | None
    runtime_state: str
    targets_evaluated: int = 0
    watches_evaluated: int = 0
    requests_created: int = 0
    events_created: int = 0
    audits_requested: int = 0
    git_hygiene_findings: int = 0
    ring2_requests_created: int = 0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    provider_execution_performed: bool = False
    dispatch_execution_performed: bool = False
    artifacts: dict[str, str] = field(default_factory=dict)

    @classmethod
    def start(cls) -> "OperationsRuntimeCycle":
        return cls(cycle_id=f"orc-{uuid4().hex}", started_at=utc_now_iso(), finished_at=None, runtime_state="running")

    def to_dict(self) -> dict[str, Any]:
        if self.runtime_state not in ALLOWED_RUNTIME_STATES:
            raise ValueError(f"unknown runtime_state {self.runtime_state}")
        return asdict(self)


class OperationsRuntime:
    def __init__(self, root: Path | None = None) -> None:
        self.root = _root(root)
        self.background = BackgroundOperationsRuntime(self.root)
        self.targets = OperationalTargetRuntime(self.root)

    @property
    def base(self) -> Path:
        return self.root / RUNTIME_BASE

    def ensure_dirs(self) -> None:
        for rel in [STATUS_DIR, REPORTS_DIR, CYCLES_DIR]:
            (self.root / rel).mkdir(parents=True, exist_ok=True)

    def run_cycle(self, *, dry_run: bool = False) -> dict[str, Any]:
        self.ensure_dirs()
        cycle = OperationsRuntimeCycle.start()
        try:
            target_status = self.targets.write_status()
            watches = self.background.load_watches()
            before_requests = len(self.background.list_requests())
            background_status = self.background.run_cycle(write=not dry_run)
            after_requests = len(self.background.list_requests()) if not dry_run else before_requests + len(background_status.get("requests", []))
            enabled_targets = [t for t in target_status.get("available_targets", []) if t.get("watch_state") == "enabled"]
            hygiene = target_status.get("latest_git_hygiene_issue_by_target") or {}
            cycle.targets_evaluated = len(enabled_targets)
            cycle.watches_evaluated = len([w for w in watches if w.enabled])
            cycle.requests_created = max(0, after_requests - before_requests) if not dry_run else len(background_status.get("requests", []))
            cycle.events_created = len(background_status.get("events", []))
            cycle.audits_requested = sum(1 for r in background_status.get("requests", []) if r.get("request_type") == "post_merge_audit_request")
            cycle.git_hygiene_findings = sum(len(v.get("issues") or []) for v in hygiene.values())
            cycle.ring2_requests_created = sum(1 for e in background_status.get("events", []) if e.get("event_type") == "ring2_review_needed")
            cycle.warnings.extend(background_status.get("summary", {}).get("warnings") or [])
            cycle.artifacts = {
                "background_status": "runtime/background_operations/status/latest.json",
                "operational_targets_status": "runtime/operational_targets/status/latest.json",
            }
            cycle.runtime_state = "stopped"
        except Exception as exc:  # cycle status must persist failures for Office visibility
            cycle.runtime_state = "failed"
            cycle.errors.append(str(exc))
        cycle.finished_at = utc_now_iso()
        payload = cycle.to_dict()
        if not dry_run:
            self.write_status(payload)
        return payload

    def write_status(self, cycle: dict[str, Any], *, state: str | None = None) -> dict[str, Any]:
        summary = self.summary_from_cycle(cycle, state=state)
        payload = {"available": True, "generated_at": utc_now_iso(), "latest_cycle": cycle, "summary": summary, "provider_execution_performed": False, "dispatch_execution_performed": False}
        _write_json(self.root / CYCLES_DIR / f"{cycle['cycle_id']}.json", cycle)
        _write_json(self.root / STATUS_DIR / "latest.json", payload)
        _write_json(self.root / STATUS_DIR / "summary.json", summary)
        _write_json(self.root / HEARTBEAT, {"heartbeat_at": utc_now_iso(), **summary})
        (self.root / REPORTS_DIR / "latest.md").write_text(format_operations_runtime_report(payload), encoding="utf-8")
        return payload

    def load_status(self) -> dict[str, Any]:
        path = self.root / STATUS_DIR / "latest.json"
        if path.exists():
            return _read_json(path)
        return {"available": True, "generated_at": utc_now_iso(), "latest_cycle": None, "summary": self.empty_summary("idle"), "provider_execution_performed": False, "dispatch_execution_performed": False}

    def request_stop(self) -> dict[str, Any]:
        payload = {"stop_requested": True, "requested_at": utc_now_iso()}
        _write_json(self.root / STOP_REQUEST, payload)
        status = self.load_status()
        status["summary"]["operations_runtime_state"] = "stop_requested"
        _write_json(self.root / STATUS_DIR / "latest.json", status)
        _write_json(self.root / STATUS_DIR / "summary.json", status["summary"])
        return payload

    def stop_requested(self) -> bool:
        return (self.root / STOP_REQUEST).exists()

    def clear_stop_request(self) -> None:
        p = self.root / STOP_REQUEST
        if p.exists():
            p.unlink()

    def empty_summary(self, state: str) -> dict[str, Any]:
        return {"operations_runtime_available": True, "operations_runtime_state": state, "last_cycle_id": None, "last_cycle_at": None, "active_targets_count": 0, "enabled_watches_count": 0, "requests_created_last_cycle": 0, "audits_requested_last_cycle": 0, "git_hygiene_findings_count": 0, "ring2_requests_count": 0, "runtime_warnings": []}

    def summary_from_cycle(self, cycle: dict[str, Any], *, state: str | None = None) -> dict[str, Any]:
        return {"operations_runtime_available": True, "operations_runtime_state": state or cycle.get("runtime_state", "stopped"), "last_cycle_id": cycle.get("cycle_id"), "last_cycle_at": cycle.get("finished_at") or cycle.get("started_at"), "active_targets_count": cycle.get("targets_evaluated", 0), "enabled_watches_count": cycle.get("watches_evaluated", 0), "requests_created_last_cycle": cycle.get("requests_created", 0), "audits_requested_last_cycle": cycle.get("audits_requested", 0), "git_hygiene_findings_count": cycle.get("git_hygiene_findings", 0), "ring2_requests_count": cycle.get("ring2_requests_created", 0), "runtime_warnings": cycle.get("warnings", []) + cycle.get("errors", [])}


def format_operations_runtime_report(status: dict[str, Any]) -> str:
    s = status.get("summary", {})
    lines = ["# Operations Runtime Service Loop", "", f"Generated: {status.get('generated_at')}", "", "## Health"]
    for key in ["operations_runtime_state", "last_cycle_id", "last_cycle_at", "active_targets_count", "enabled_watches_count", "requests_created_last_cycle", "audits_requested_last_cycle", "git_hygiene_findings_count", "ring2_requests_count"]:
        lines.append(f"- {key}: {s.get(key)}")
    lines += ["", "Boundary: observes, evaluates, requests, and reports only. No provider or dispatch execution is performed."]
    return "\n".join(lines).rstrip() + "\n"


def load_operations_runtime_status(root: Path | None = None) -> dict[str, Any]:
    return OperationsRuntime(root).load_status()
