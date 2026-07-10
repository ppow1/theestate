"""Runtime for cross-department operational coordination."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from estate.core.collaboration_events import append_event
from estate.core.department_coordination import DepartmentCoordination, DepartmentHandoff, coordination_event, utc_now_iso
from estate.core.paths import ESTATE_ROOT
from estate.core.traffic_controller import RecommendedAction

COORDINATION_DIR = Path("runtime/department_coordination")
STATE_FILE = COORDINATION_DIR / "coordinations.json"
EVENTS_FILE = COORDINATION_DIR / "events.jsonl"
STATUS_FILE = COORDINATION_DIR / "status.json"


def _root(root: str | Path | None = None) -> Path:
    return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists(): return default
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


class DepartmentCoordinationRuntime:
    """Filesystem runtime for governed department inboxes and sequencing."""

    def __init__(self, root: str | Path | None = None) -> None:
        self.root = _root(root)

    @property
    def state_path(self) -> Path: return self.root / STATE_FILE
    @property
    def events_path(self) -> Path: return self.root / EVENTS_FILE
    @property
    def status_path(self) -> Path: return self.root / STATUS_FILE

    def load_coordinations(self) -> dict[str, DepartmentCoordination]:
        payload = _read_json(self.state_path, {"coordinations": []})
        return {c.coordination_id: c for c in [DepartmentCoordination.from_dict(x) for x in payload.get("coordinations", [])]}

    def save_coordinations(self, coordinations: dict[str, DepartmentCoordination]) -> None:
        _write_json(self.state_path, {"version": 1, "updated_at": utc_now_iso(), "coordinations": [c.to_dict() for c in coordinations.values()]})
        self.write_status(coordinations)

    def register(self, coordination: DepartmentCoordination) -> DepartmentCoordination:
        coordination.validate()
        coordinations = self.load_coordinations(); coordinations[coordination.coordination_id] = coordination; self.save_coordinations(coordinations)
        self._record(coordination, "coordination_created", "Cross-department coordination registered.")
        for request in coordination.requests:
            append_event("message.routed", "department_coordination_runtime", {"coordination_id": coordination.coordination_id, "campaign_id": coordination.campaign_id, "department": request.department, "request_id": request.request_id, "boundary": "department inbox routing only; execution providers remain behind dispatch/adapters"}, subject_id=request.request_id, root=self.root)
        return coordination

    def _record(self, coordination: DepartmentCoordination, event_type: str, summary: str, **metadata: Any) -> dict[str, Any]:
        event = coordination_event(coordination, event_type, summary, **metadata)
        self.events_path.parent.mkdir(parents=True, exist_ok=True)
        with self.events_path.open("a", encoding="utf-8") as handle: handle.write(json.dumps(event, sort_keys=True) + "\n")
        return event

    def _get(self, coordination_id: str) -> tuple[dict[str, DepartmentCoordination], DepartmentCoordination]:
        coordinations = self.load_coordinations()
        if coordination_id not in coordinations: raise KeyError(f"unknown coordination {coordination_id}")
        return coordinations, coordinations[coordination_id]

    def _authorize(self, coordination: DepartmentCoordination, action: str, actor: str, department: str | None = None) -> None:
        if actor != coordination.authority.operations_manager: raise PermissionError("actor is outside Operations Manager delegated authority")
        if action not in coordination.authority.allowed_actions: raise PermissionError(f"action {action} is outside delegated authority")
        if department and coordination.authority.allowed_departments and department not in coordination.authority.allowed_departments: raise PermissionError(f"department {department} is outside delegated authority")

    def acknowledge(self, coordination_id: str, request_id: str, *, acknowledged_by: str, actor: str = "Operations Manager") -> DepartmentCoordination:
        coordinations, coordination = self._get(coordination_id); request = coordination.request(request_id); self._authorize(coordination, "sequence", actor, request.department)
        request.acknowledgement_state = "Acknowledged"; request.acknowledged_by = acknowledged_by; request.acknowledged_at = utc_now_iso()
        if request.ready: request.state = "Ready"
        coordination.updated_at = utc_now_iso(); self._record(coordination, "request_acknowledged", f"{request.department} acknowledged {request_id}.", request_id=request_id, department=request.department); self.save_coordinations(coordinations); return coordination

    def release_dependency(self, coordination_id: str, request_id: str, dependency_id: str, *, actor: str = "Operations Manager") -> DepartmentCoordination:
        coordinations, coordination = self._get(coordination_id); request = coordination.request(request_id); self._authorize(coordination, "release_dependency", actor, request.department)
        dep = next((d for d in request.dependencies if d.dependency_id == dependency_id), None)
        if dep is None: raise KeyError(f"unknown dependency {dependency_id}")
        upstream = coordination.request(dep.upstream_request_id)
        if upstream.state != "Completed": raise ValueError("upstream request must be completed before dependency release")
        dep.state = "Released"; dep.released_at = utc_now_iso()
        if request.ready: request.state = "Ready"
        coordination.updated_at = utc_now_iso(); self._record(coordination, "dependency_released", f"Dependency {dependency_id} released for {request_id}.", request_id=request_id, dependency_id=dependency_id); self.save_coordinations(coordinations); return coordination

    def sequence_ready_work(self, coordination_id: str, ordered_request_ids: list[str] | None = None, *, actor: str = "Operations Manager") -> dict[str, Any]:
        coordinations, coordination = self._get(coordination_id); self._authorize(coordination, "sequence", actor)
        order = ordered_request_ids or [r.request_id for r in coordination.requests]
        ready = []
        for sequence, request_id in enumerate(order, start=1):
            request = coordination.request(request_id)
            self._authorize(coordination, "sequence", actor, request.department)
            if request.ready:
                request.sequence = sequence; request.state = "In Progress"; ready.append({"request_id": request.request_id, "department": request.department, "sequence": sequence, "execution_provider": request.execution_provider})
        coordination.updated_at = utc_now_iso(); self._record(coordination, "work_sequenced", "Operations Manager sequenced routine ready work.", sequenced=ready); self.save_coordinations(coordinations); return {"coordination_id": coordination_id, "sequenced": ready, "blocked": self.dependency_status(coordination_id)["blocked"]}

    def complete_request(self, coordination_id: str, request_id: str, evidence: list[str], *, actor: str = "Operations Manager") -> DepartmentCoordination:
        coordinations, coordination = self._get(coordination_id); request = coordination.request(request_id); self._authorize(coordination, "sequence", actor, request.department)
        request.evidence.extend(evidence); request.state = "Completed"; coordination.updated_at = utc_now_iso(); self._record(coordination, "request_completed", f"Request {request_id} completed with departmental evidence.", request_id=request_id, evidence=evidence); self.save_coordinations(coordinations); return coordination

    def deliver_handoff(self, coordination_id: str, request_id: str, handoff: DepartmentHandoff, *, actor: str = "Operations Manager") -> DepartmentCoordination:
        coordinations, coordination = self._get(coordination_id); request = coordination.request(request_id); self._authorize(coordination, "deliver_handoff", actor, request.department)
        handoff.state = "Delivered"; handoff.delivered_at = utc_now_iso(); request.handoffs.append(handoff); coordination.updated_at = utc_now_iso(); self._record(coordination, "handoff_delivered", f"Handoff {handoff.handoff_id} delivered.", request_id=request_id, handoff_id=handoff.handoff_id); self.save_coordinations(coordinations); return coordination

    def escalate_unresolved(self, coordination_id: str, reason: str, *, actor: str = "Operations Manager") -> dict[str, Any]:
        coordinations, coordination = self._get(coordination_id)
        if actor != coordination.authority.operations_manager: raise PermissionError("only Operations Manager may raise coordination escalation evidence")
        rec = RecommendedAction.create(action_type="escalate", target_type="system", target_id=coordination_id, priority="high", reason=reason, safe_summary="Cross-department contention or authority conflict requires Steward/Traffic Controller review.")
        coordination.state = "Escalated"; coordination.escalations.append(rec.to_dict()); coordination.updated_at = utc_now_iso(); self._record(coordination, "coordination_escalated", rec.safe_summary, recommended_action=rec.to_dict()); self.save_coordinations(coordinations); return rec.to_dict()

    def department_view(self, department: str) -> dict[str, Any]:
        inbox = []; outbox = []
        for coordination in self.load_coordinations().values():
            for request in coordination.requests:
                if request.department == department:
                    inbox.append({"coordination_id": coordination.coordination_id, "campaign_id": coordination.campaign_id, "request": request.to_dict()})
                for handoff in request.handoffs:
                    if handoff.from_department == department: outbox.append({"coordination_id": coordination.coordination_id, "request_id": request.request_id, "handoff": handoff.to_dict()})
        return {"department": department, "inbox": inbox, "outbox": outbox}

    def dependency_status(self, coordination_id: str) -> dict[str, Any]:
        _, coordination = self._get(coordination_id)
        blocked = []; released = []
        completed = {r.request_id for r in coordination.requests if r.state == "Completed"}
        for request in coordination.requests:
            for dep in request.dependencies:
                item = {"request_id": request.request_id, "department": request.department, "dependency_id": dep.dependency_id, "upstream_request_id": dep.upstream_request_id, "state": dep.state}
                if dep.state == "Released" or dep.upstream_request_id in completed: released.append(item)
                else: blocked.append(item)
            for blocker in request.blockers:
                if blocker.state == "Open": blocked.append({"request_id": request.request_id, "department": request.department, "blocker_id": blocker.blocker_id, "state": blocker.state, "escalation_required": blocker.escalation_required})
        return {"coordination_id": coordination_id, "blocked": blocked, "released": released, "escalations": coordination.escalations}

    def write_status(self, coordinations: dict[str, DepartmentCoordination] | None = None) -> dict[str, Any]:
        coordinations = coordinations or self.load_coordinations()
        payload = {"updated_at": utc_now_iso(), "coordinations": []}
        for coordination in coordinations.values():
            departments = sorted({r.department for r in coordination.requests})
            payload["coordinations"].append({"coordination_id": coordination.coordination_id, "campaign_id": coordination.campaign_id, "title": coordination.title, "state": coordination.state, "departments": departments, "requests": [{"request_id": r.request_id, "department": r.department, "state": r.state, "acknowledgement_state": r.acknowledgement_state, "sequence": r.sequence} for r in coordination.requests], "escalation_count": len(coordination.escalations), "boundary": "Operations coordinates sequencing only; departments retain authority and providers execute only through governed seams."})
        _write_json(self.status_path, payload); return payload
