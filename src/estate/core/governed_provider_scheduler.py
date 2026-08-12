from __future__ import annotations

import json, os
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from estate.core.paths import ESTATE_ROOT
from estate.core.provider_health import utc_now_iso, _write_json
from estate.core.worker_assignment_runtime import WorkerAssignmentRuntime
from estate.core.engineering_provider_health_runtime import load_current_provider_health
from estate.core.engineering_provider_routing_runtime import recommend_engineering_provider
from estate.core.compute_resources import ComputeReservationLedger, ComputeResourceRequirements, select_resource

SCHED_ROOT = Path("runtime/engineering_scheduler")
QUEUE = SCHED_ROOT / "queue.json"
HISTORY = SCHED_ROOT / "decisions.jsonl"
REPORT_JSON = SCHED_ROOT / "report.json"
REPORT_MD = SCHED_ROOT / "report.md"
OFFICE_MD = Path("operations/engineering_capacity/provider_scheduler.md")
LOCK = SCHED_ROOT / ".lock"
PRIORITY = {"urgent": 0, "high": 1, "normal": 2, "low": 3}
ACTIVE_ASSIGNMENT_STATES = {"assigned", "accepted", "blocked", "awaiting_approval", "deferred"}


def _root(root: str | Path | None = None) -> Path:
    return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


def _read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


@contextmanager
def _lock(root: Path):
    path = root / LOCK
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = None
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode())
        yield
    finally:
        if fd is not None:
            os.close(fd)
        try:
            path.unlink()
        except FileNotFoundError:
            pass


class GovernedProviderScheduler:
    """File-backed governed scheduling coordinator.

    The scheduler orders and reserves approved worker assignments. It never
    dispatches execution; release produces an auditable handoff decision for
    the existing Dispatch authority path.
    """

    def __init__(self, root: str | Path | None = None) -> None:
        self.root = _root(root)

    def _queue(self) -> dict[str, Any]:
        return _read_json(self.root / QUEUE, {"schema_version": "1.0", "items": [], "paused": False, "provider_exclusions": {}, "updated_at": utc_now_iso()})

    def _save_queue(self, q: dict[str, Any]) -> None:
        q["updated_at"] = utc_now_iso()
        _write_json(self.root / QUEUE, q)

    def _event(self, event_type: str, item: dict[str, Any] | None, actor: str, rationale: str, evidence: dict[str, Any] | None = None) -> dict[str, Any]:
        ev = {"decision_id": f"sd-{uuid4().hex}", "event_type": event_type, "timestamp": utc_now_iso(), "actor": actor, "assignment_id": (item or {}).get("assignment_id"), "queue_item_id": (item or {}).get("queue_item_id"), "provider_id": (item or {}).get("provider_id"), "rationale": rationale, "policy_version": "WP-0541/v1", "evidence_snapshot": evidence or {}}
        path = self.root / HISTORY
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(ev, sort_keys=True) + "\n")
        return ev

    def enqueue(self, assignment_id: str, *, actor: str = "scheduler", manual_provider: str | None = None, force: bool = False) -> dict[str, Any]:
        with _lock(self.root):
            q = self._queue()
            existing = next((i for i in q["items"] if i["assignment_id"] == assignment_id and i.get("state") not in {"completed", "cancelled"}), None)
            if existing and not force:
                self._event("enqueue_idempotent", existing, actor, "Assignment already queued; enqueue is idempotent.")
                self._save_queue(q); return existing
            assignment = WorkerAssignmentRuntime(self.root).load_assignment(assignment_id).to_dict()
            item = {"queue_item_id": f"qi-{uuid4().hex}", "assignment_id": assignment_id, "state": "queued", "created_at": utc_now_iso(), "updated_at": utc_now_iso(), "priority": assignment.get("priority", "normal"), "classification": assignment.get("classification"), "work_package_id": assignment.get("work_package_id"), "provider_id": manual_provider or assignment.get("provider_id"), "manual_pin": bool(manual_provider), "attempt_count": 0, "defer_until": None, "reservation": None, "release": None, "failures": [], "overrides": [], "evidence_refs": [f"runtime/workers/assignments/records/{assignment_id}.json"], "compute_resource_requirements": (assignment.get("metadata") or {}).get("compute_resource_requirements") or {}}
            q["items"].append(item)
            self._event("enqueue", item, actor, "Approved assignment entered governed scheduling queue.", {"assignment": assignment})
            self._save_queue(q); return item

    def recover(self, *, actor: str = "scheduler", now: datetime | None = None) -> dict[str, Any]:
        now = now or datetime.now(timezone.utc); recovered=[]
        with _lock(self.root):
            q=self._queue()
            for item in q["items"]:
                res=item.get("reservation") or {}
                exp=_parse_ts(res.get("expires_at"))
                if item.get("state") == "reserved" and exp and exp <= now:
                    item["state"]="queued"; item["reservation"]["expired_at"]=utc_now_iso(); recovered.append(item["assignment_id"])
                    reservation_id = (item.get("reservation") or {}).get("reservation_id")
                    if reservation_id:
                        ComputeReservationLedger(self.root).release(reservation_id)
                    self._event("recover_expired_reservation", item, actor, "Expired reservation returned to queue.", {"reservation": res})
            self._save_queue(q)
        return {"recovered_assignment_ids": recovered, "recovered_count": len(recovered)}

    def recommend(self, *, actor: str = "scheduler") -> dict[str, Any]:
        self.recover(actor=actor)
        q = self._queue(); health = load_current_provider_health(root=self.root)
        health_by = {p.get("provider_id"): p for p in health.get("providers", [])}
        assignments = {a.assignment_id: a.to_dict() for a in WorkerAssignmentRuntime(self.root).load_assignments()}
        decisions=[]
        active_by_provider={}
        for i in q["items"]:
            if i.get("state") == "reserved" and i.get("provider_id"):
                active_by_provider[i["provider_id"]] = active_by_provider.get(i["provider_id"], 0) + 1
        for item in q["items"]:
            if item.get("state") not in {"queued", "deferred"}: continue
            assignment = assignments.get(item["assignment_id"])
            reasons=[]; eligible=True
            if not assignment or assignment.get("state") not in ACTIVE_ASSIGNMENT_STATES:
                eligible=False; reasons.append("assignment is missing or not in a schedulable state")
            if q.get("paused"):
                eligible=False; reasons.append("scheduler is paused")
            provider = item.get("provider_id")
            if not provider and assignment:
                route = recommend_engineering_provider({"routing_request_id": item["queue_item_id"], "mission_summary": assignment.get("summary") or assignment.get("mission"), "work_type": assignment.get("mission") or "assignment", "requires_repo_write": True, "validation_required": assignment.get("validation_required", True)}, root=self.root, write=False)
                provider = route.get("recommended_provider"); item["provider_id"] = provider; item["routing_snapshot"] = route
            ph = health_by.get(provider, {})
            requirements = ComputeResourceRequirements.from_dict(item.get("compute_resource_requirements"))
            if requirements.requires_gpu:
                snapshot_path = self.root / "runtime/compute_resources/gpus.json"
                snapshot = _read_json(snapshot_path, {})
                resources = snapshot.get("resources") if isinstance(snapshot, dict) else []
                observations = []
                for raw in resources or []:
                    try:
                        from estate.core.compute_resources import ComputeResourceObservation
                        observations.append(ComputeResourceObservation(**raw))
                    except (TypeError, ValueError):
                        continue
                placement = select_resource(observations, requirements)
                if not placement.get("eligible"):
                    eligible = False; reasons.append(placement.get("reason") or "compute placement unavailable")
                item["compute_placement_snapshot"] = placement
            if provider in q.get("provider_exclusions", {}): eligible=False; reasons.append("provider is manually excluded")
            if ph and ph.get("health_state") in {"offline", "maintenance"}: eligible=False; reasons.append("provider health excludes scheduling")
            if ph and ph.get("is_stale"): eligible=False; reasons.append("provider evidence is stale")
            max_jobs = ph.get("max_jobs") or ph.get("metadata", {}).get("max_jobs") or 1
            if active_by_provider.get(provider, 0) >= int(max_jobs or 1): eligible=False; reasons.append("provider reservation capacity is full")
            rank = (PRIORITY.get(item.get("priority", "normal"), 2), item.get("created_at"), item.get("assignment_id"))
            decisions.append({"queue_item_id": item["queue_item_id"], "assignment_id": item["assignment_id"], "provider_id": provider, "eligible": eligible, "rank": rank, "reasons": reasons or ["eligible under current governed scheduling evidence"], "compute_placement": item.get("compute_placement_snapshot"), "constraints": {"dispatch_required": True, "recommendation_only_routing": True}})
        decisions.sort(key=lambda d: (not d["eligible"], d["rank"]))
        return {"generated_at": utc_now_iso(), "paused": q.get("paused", False), "decisions": decisions, "constraints": {"does_not_dispatch": True, "existing_dispatch_only_release_path": True}, "source_artifacts": [str(QUEUE), "runtime/provider_health/current.json", "runtime/workers/assignments/status/board.json"]}

    def reserve(self, *, actor: str = "scheduler", ttl_minutes: int = 30) -> dict[str, Any]:
        rec = self.recommend(actor=actor)
        with _lock(self.root):
            q = self._queue()
            current_reserved = {i.get("assignment_id") for i in q["items"] if i.get("state") == "reserved"}
            chosen = next((d for d in rec["decisions"] if d["eligible"] and d["assignment_id"] not in current_reserved), None)
            if not chosen:
                return {"reserved": False, "reason": "no eligible queue items", "recommendation": rec}
            item = next(i for i in q["items"] if i["queue_item_id"] == chosen["queue_item_id"] and i.get("state") in {"queued", "deferred"})
            item["state"] = "reserved"; item["provider_id"] = chosen["provider_id"]
            item["reservation"] = {"reservation_id": f"rs-{uuid4().hex}", "reserved_by": actor, "reserved_at": utc_now_iso(), "expires_at": (datetime.now(timezone.utc)+timedelta(minutes=ttl_minutes)).replace(microsecond=0).isoformat().replace("+00:00","Z"), "dispatch_required": True}
            requirements = ComputeResourceRequirements.from_dict(item.get("compute_resource_requirements"))
            if requirements.requires_gpu:
                resource_id = (chosen.get("compute_placement") or {}).get("selected") or (item.get("compute_placement_snapshot") or {}).get("selected")
                if not resource_id:
                    item["state"] = "queued"
                    return {"reserved": False, "reason": "compute resource selection disappeared before reservation", "recommendation": rec}
                try:
                    ComputeReservationLedger(self.root).reserve(reservation_id=item["reservation"]["reservation_id"], resource_id=resource_id, workload_id=item["assignment_id"], minimum_vram_mib=requirements.minimum_vram_mib)
                except ValueError as exc:
                    item["state"] = "queued"
                    return {"reserved": False, "reason": str(exc), "recommendation": rec}
            self._event("reserve", item, actor, "Capacity reservation prepared; Dispatch authorization remains required.", chosen)
            self._save_queue(q); return {"reserved": True, "item": item}

    def release(self, assignment_id: str, *, actor: str = "scheduler", rationale: str = "Released for existing governed Dispatch review") -> dict[str, Any]:
        with _lock(self.root):
            q=self._queue(); item=next((i for i in q["items"] if i["assignment_id"]==assignment_id), None)
            if not item: raise ValueError(f"queue item not found for assignment: {assignment_id}")
            item["state"]="released_to_dispatch"; item["release"]={"released_at": utc_now_iso(), "released_by": actor, "rationale": rationale, "dispatch_required": True}
            reservation_id = (item.get("reservation") or {}).get("reservation_id")
            if reservation_id:
                ComputeReservationLedger(self.root).release(reservation_id)
            self._event("release", item, actor, rationale, {"dispatch_boundary": "existing execution_dispatch remains sole execution release path"})
            self._save_queue(q); return item

    def defer(self, assignment_id: str, *, actor: str, reason: str, retry_after_minutes: int = 60) -> dict[str, Any]:
        with _lock(self.root):
            q=self._queue(); item=next((i for i in q["items"] if i["assignment_id"]==assignment_id), None)
            if not item: raise ValueError(f"queue item not found for assignment: {assignment_id}")
            item["state"]="deferred"; item["defer_until"]=(datetime.now(timezone.utc)+timedelta(minutes=retry_after_minutes)).replace(microsecond=0).isoformat().replace("+00:00","Z"); item["failures"].append({"at": utc_now_iso(), "reason": reason})
            self._event("defer", item, actor, reason); self._save_queue(q); return item

    def pause(self, *, actor: str, reason: str, paused: bool = True) -> dict[str, Any]:
        with _lock(self.root):
            q=self._queue(); q["paused"]=paused; self._event("pause" if paused else "resume", None, actor, reason); self._save_queue(q); return q

    def exclude_provider(self, provider_id: str, *, actor: str, reason: str, excluded: bool = True) -> dict[str, Any]:
        with _lock(self.root):
            q=self._queue(); ex=q.setdefault("provider_exclusions", {})
            if excluded: ex[provider_id]={"actor": actor, "reason": reason, "at": utc_now_iso()}
            else: ex.pop(provider_id, None)
            self._event("provider_exclusion" if excluded else "provider_inclusion", {"provider_id": provider_id}, actor, reason); self._save_queue(q); return q

    def report(self, *, write: bool = True) -> dict[str, Any]:
        payload = self.recommend()
        payload["queue"] = self._queue()
        if write:
            _write_json(self.root / REPORT_JSON, payload)
            text = format_scheduler_report(payload)
            for rel in (REPORT_MD, OFFICE_MD):
                p=self.root/rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(text, encoding="utf-8")
        return payload


def format_scheduler_report(payload: dict[str, Any]) -> str:
    lines=["# Governed Provider Scheduling Report", "", f"Generated: {payload.get('generated_at')}", "", "This report is advisory and reservation-oriented. Existing Dispatch remains the only execution release path.", "", "Assignment | Provider | Eligible | Reasons"]
    for d in payload.get("decisions", []):
        lines.append(f"{d.get('assignment_id')} | {d.get('provider_id')} | {d.get('eligible')} | {'; '.join(d.get('reasons') or [])}")
    return "\n".join(lines).rstrip()+"\n"
