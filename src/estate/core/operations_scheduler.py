"""Event-driven scheduler for the bounded Operations Runtime.

The scheduler owns timing, leases, retry metadata, and Office-readable status. It
intentionally delegates execution to existing Operations Runtime entry points
instead of becoming a second orchestrator.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from estate.core.operational_events import OperationalEvent
from estate.core.operational_status import record_operational_event
from estate.core.paths import ESTATE_ROOT

SCHEDULER_DIR = Path("runtime/operations_scheduler")
STATE_FILE = SCHEDULER_DIR / "state.json"
STATUS_FILE = SCHEDULER_DIR / "status.json"
STATUS_MD = Path("operations/operations_scheduler/status.md")
EVENT_LOG = SCHEDULER_DIR / "events.jsonl"
LEASE_SECONDS = 15 * 60


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def utc_now_iso() -> str:
    return utc_now().isoformat().replace("+00:00", "Z")


def parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _root(root: Path | None = None) -> Path:
    return root or (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


@dataclass(frozen=True)
class SchedulerJob:
    job_id: str
    description: str
    runtime_mode: str = "observe-only"
    interval_seconds: int | None = None
    calendar: str | None = None  # HH:MM UTC daily
    events: list[str] = field(default_factory=list)
    debounce_seconds: int = 0
    retry_seconds: int = 300
    timeout_seconds: int = 900
    depends_on: list[str] = field(default_factory=list)
    max_catch_up_runs: int = 1
    allow_overlap: bool = False
    enabled: bool = True
    max_audit_requests: int = 1

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


DEFAULT_JOBS: dict[str, SchedulerJob] = {
    "merge_discovery": SchedulerJob("merge_discovery", "Discover merged work packages and create audit requests", "discover-merges", interval_seconds=1800, events=["git.merge", "repo.changed"], debounce_seconds=60, max_audit_requests=5),
    "audit_processing": SchedulerJob("audit_processing", "Process pending post-merge audit requests", "process-audits", interval_seconds=900, events=["audit.requested", "merge_discovery.completed"], debounce_seconds=30, depends_on=["merge_discovery"]),
    "ring2_preparation": SchedulerJob("ring2_preparation", "Prepare Ring 2 audit prompts when required", "process-audits-and-ring2", interval_seconds=3600, events=["ring2.required", "audit.blocked"], debounce_seconds=60, depends_on=["audit_processing"]),
    "health_refresh": SchedulerJob("health_refresh", "Refresh Operations Runtime health and Office status", "observe-only", interval_seconds=300, calendar="00:00", events=["office.refresh", "health.refresh"], debounce_seconds=15),
    "repository_monitoring": SchedulerJob("repository_monitoring", "Monitor repository state and operational targets", "discover-merges", interval_seconds=1200, events=["repo.changed", "work_package.completed"], debounce_seconds=45, max_audit_requests=2),
}


class OperationsScheduler:
    def __init__(self, root: Path | None = None, *, now: datetime | None = None) -> None:
        self.root = _root(root)
        self.now = (now or utc_now()).astimezone(timezone.utc).replace(microsecond=0)

    @property
    def state_path(self) -> Path:
        return self.root / STATE_FILE

    def default_state(self) -> dict[str, Any]:
        now = iso(self.now)
        return {"version": 1, "generated_at": now, "jobs": {jid: {"enabled": job.enabled, "next_run_at": now, "last_run_at": None, "lease": None, "retry_count": 0, "failure_count": 0, "last_failure": None, "pending_events": [], "last_event_at": None} for jid, job in DEFAULT_JOBS.items()}}

    def load_state(self) -> dict[str, Any]:
        state = _read_json(self.state_path, self.default_state())
        for jid, job in DEFAULT_JOBS.items():
            state.setdefault("jobs", {}).setdefault(jid, self.default_state()["jobs"][jid])
            state["jobs"][jid].setdefault("enabled", job.enabled)
            state["jobs"][jid].setdefault("pending_events", [])
        return state

    def save_state(self, state: dict[str, Any]) -> None:
        state["generated_at"] = iso(self.now)
        _write_json(self.state_path, state)
        self.write_status(state)

    def list_jobs(self) -> dict[str, Any]:
        state = self.load_state(); self.write_status(state)
        return {"jobs": [self.describe_job(jid, state) for jid in DEFAULT_JOBS]}

    def describe_job(self, job_id: str, state: dict[str, Any] | None = None) -> dict[str, Any]:
        if job_id not in DEFAULT_JOBS:
            raise ValueError(f"unknown scheduler job {job_id}")
        state = state or self.load_state()
        return {**DEFAULT_JOBS[job_id].to_dict(), "state": state["jobs"].get(job_id, {})}

    def set_enabled(self, job_id: str, enabled: bool) -> dict[str, Any]:
        state = self.load_state(); self.describe_job(job_id, state)
        state["jobs"][job_id]["enabled"] = enabled
        if enabled and not state["jobs"][job_id].get("next_run_at"):
            state["jobs"][job_id]["next_run_at"] = iso(self.now)
        self.save_state(state)
        return self.describe_job(job_id, state)

    def trigger(self, event: str) -> dict[str, Any]:
        state = self.load_state(); matched = []
        for jid, job in DEFAULT_JOBS.items():
            if event in job.events:
                js = state["jobs"][jid]
                js.setdefault("pending_events", []).append({"event": event, "at": iso(self.now)})
                js["last_event_at"] = iso(self.now)
                due_at = self.now + timedelta(seconds=max(0, job.debounce_seconds))
                current = parse_ts(js.get("next_run_at"))
                if current is None or current <= self.now or due_at < current:
                    js["next_run_at"] = iso(due_at)
                matched.append(jid)
        self._append_scheduler_event({"event": event, "matched_jobs": matched, "created_at": iso(self.now)})
        self.save_state(state)
        return {"event": event, "matched_jobs": matched, "jobs_woken": len(matched)}

    def acquire_due(self) -> list[dict[str, Any]]:
        state = self.load_state(); due = []
        completed = {jid for jid, js in state["jobs"].items() if js.get("last_run_status") == "completed"}
        for jid, job in DEFAULT_JOBS.items():
            js = state["jobs"][jid]
            if not js.get("enabled", job.enabled):
                continue
            lease = js.get("lease") or {}
            if lease and parse_ts(lease.get("expires_at")) and parse_ts(lease.get("expires_at")) > self.now and not job.allow_overlap:
                continue
            if any(dep not in completed for dep in job.depends_on):
                continue
            next_run = parse_ts(js.get("next_run_at"))
            if next_run and next_run <= self.now:
                catch_up = min(job.max_catch_up_runs, max(1, int(((self.now - next_run).total_seconds() // max(1, job.interval_seconds or 86400)) + 1)))
                lease_id = f"lease-{uuid4().hex}"
                js["lease"] = {"lease_id": lease_id, "acquired_at": iso(self.now), "expires_at": iso(self.now + timedelta(seconds=job.timeout_seconds or LEASE_SECONDS))}
                due.append({"job": job, "lease_id": lease_id, "catch_up_runs": catch_up})
        self.save_state(state)
        return due

    def complete(self, job_id: str, lease_id: str, status: str, result: dict[str, Any] | None = None, error: str | None = None) -> None:
        state = self.load_state(); job = DEFAULT_JOBS[job_id]; js = state["jobs"][job_id]
        if (js.get("lease") or {}).get("lease_id") != lease_id:
            raise ValueError("scheduler lease mismatch")
        js["lease"] = None; js["last_run_at"] = iso(self.now); js["last_run_status"] = status
        if status == "completed":
            js["retry_count"] = 0; js["pending_events"] = []
            js["next_run_at"] = iso(self._next_time(job))
        else:
            js["retry_count"] = int(js.get("retry_count") or 0) + 1; js["failure_count"] = int(js.get("failure_count") or 0) + 1; js["last_failure"] = error or "unknown failure"
            js["next_run_at"] = iso(self.now + timedelta(seconds=job.retry_seconds))
        js["last_result"] = result or {}
        self._append_scheduler_event({"job_id": job_id, "status": status, "error": error, "created_at": iso(self.now)})
        self.save_state(state)

    def _next_time(self, job: SchedulerJob) -> datetime:
        candidates = []
        if job.interval_seconds:
            candidates.append(self.now + timedelta(seconds=job.interval_seconds))
        if job.calendar:
            hour, minute = [int(x) for x in job.calendar.split(":", 1)]
            cal = self.now.replace(hour=hour, minute=minute, second=0)
            if cal <= self.now: cal += timedelta(days=1)
            candidates.append(cal)
        return min(candidates) if candidates else self.now + timedelta(days=365)

    def _append_scheduler_event(self, payload: dict[str, Any]) -> None:
        path = self.root / EVENT_LOG; path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as h: h.write(json.dumps(payload, sort_keys=True) + "\n")

    def write_status(self, state: dict[str, Any]) -> None:
        status = {"generated_at": iso(self.now), "jobs": [self.describe_job(jid, state) for jid in DEFAULT_JOBS], "summary": {"job_count": len(DEFAULT_JOBS), "enabled_count": sum(1 for j in state["jobs"].values() if j.get("enabled")), "leased_count": sum(1 for j in state["jobs"].values() if j.get("lease")), "boundary": "Schedules existing Operations Runtime functions only; Traffic Controller and provider seams remain authoritative."}}
        _write_json(self.root / STATUS_FILE, status)
        md = ["# Event-Driven Operations Scheduler", "", f"Generated: {status['generated_at']}", "", "Boundary: schedules existing Operations Runtime functions only; no provider calls bypass provider seams.", "", "## Jobs"]
        for item in status["jobs"]:
            st = item["state"]; md.append(f"- {item['job_id']}: enabled={st.get('enabled')} next={st.get('next_run_at')} last={st.get('last_run_at')} status={st.get('last_run_status')}")
        p = self.root / STATUS_MD; p.parent.mkdir(parents=True, exist_ok=True); p.write_text("\n".join(md)+"\n", encoding="utf-8")

    def emit_office_event(self, job_id: str, status: str) -> None:
        record_operational_event(OperationalEvent.create(event_type="Execution Complete" if status == "completed" else "Worker Failed", state="Completed" if status == "completed" else "Failed", classification="Estate Internal", message=f"Operations scheduler job {job_id} {status}.", request_id=f"operations-scheduler:{job_id}", metadata={"summary_safe": True, "scheduler_job": job_id}), root=self.root, allow_extension_event_types=True)


def format_scheduler(payload: dict[str, Any]) -> str:
    jobs = payload.get("jobs") or ([payload] if payload.get("job_id") else [])
    lines = ["# Operations Scheduler", ""]
    for item in jobs:
        st = item.get("state", {})
        lines.append(f"- {item.get('job_id')}: enabled={st.get('enabled')} next={st.get('next_run_at')} last={st.get('last_run_at')} failures={st.get('failure_count', 0)}")
    return "\n".join(lines).rstrip() + "\n"
