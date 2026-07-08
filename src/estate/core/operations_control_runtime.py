from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from estate.core.operational_events import OperationalEvent
from estate.core.operational_status import record_operational_event
from estate.core.operations_manager import OperationsDecision
from estate.core.paths import ESTATE_ROOT
from estate.core.traffic_controller import OperationsReview, RecommendedAction, redact_summary

CONTROL_ROOT = Path("runtime/operations/control")
REVIEWS_DIR = CONTROL_ROOT / "reviews"
DECISIONS_DIR = CONTROL_ROOT / "decisions"
STATUS_DIR = CONTROL_ROOT / "status"


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


class OperationsControlRuntime:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or ESTATE_ROOT

    def _rel(self, path: Path) -> str:
        try: return str(path.relative_to(self.root))
        except ValueError: return str(path)

    def generate_review(self, *, classification: str = "Estate Internal", write: bool = True) -> tuple[OperationsReview, dict[str, str]]:
        review = OperationsReview.create(classification=classification)
        self._inspect_intake(review)
        self._inspect_schedule(review)
        self._inspect_dispatch(review)
        self._inspect_assignments(review)
        self._inspect_providers(review)
        if review.blocked_intake_count or review.assignment_blocked_count or review.provider_blocked_count:
            review.requires_steward_attention = True
        if review.provider_blocked_count or review.provider_saturated_count:
            review.recommended_actions.append(RecommendedAction.create(action_type="escalate", target_type="system", priority="high", reason="Provider capacity or availability is blocking work movement.", safe_summary="Review provider capacity and reassign or hold affected work.", requires_steward_approval=False))
        elif not review.recommended_actions:
            review.recommended_actions.append(RecommendedAction.create(action_type="no_action", target_type="system", reason="No immediate operations control action is required from available artifacts.", safe_summary="No action recommended."))
        review.validate()
        paths = self._write_review_outputs(review) if write else {}
        return review, paths

    def record_decision(self, decision: OperationsDecision) -> dict[str, str]:
        decision.validate()
        path = self.root / DECISIONS_DIR / f"{decision.created_at[:10]}_{decision.decision_id}.json"
        _write_json(path, decision.to_dict())
        self._emit_decision_event(decision, path)
        self._write_summary(decision=decision)
        return {"decision": str(path), "summary_json": str(self.root / STATUS_DIR / "summary.json"), "summary_md": str(self.root / STATUS_DIR / "summary.md")}

    def list_decisions(self) -> list[OperationsDecision]:
        base = self.root / DECISIONS_DIR
        if not base.exists(): return []
        return [OperationsDecision.from_dict(_load_json(p)) for p in sorted(base.glob("*.json"))]

    def _write_review_outputs(self, review: OperationsReview) -> dict[str, str]:
        review_path = self.root / REVIEWS_DIR / f"{review.created_at[:10]}_{review.review_id}.json"
        _write_json(review_path, review.to_dict())
        _write_json(self.root / STATUS_DIR / "latest.json", review.to_dict())
        self._write_summary(review=review)
        return {"review": str(review_path), "latest": str(self.root / STATUS_DIR / "latest.json"), "summary_json": str(self.root / STATUS_DIR / "summary.json"), "summary_md": str(self.root / STATUS_DIR / "summary.md")}

    def _write_summary(self, *, review: OperationsReview | None = None, decision: OperationsDecision | None = None) -> None:
        if review is None:
            latest = self.root / STATUS_DIR / "latest.json"
            review = OperationsReview.from_dict(_load_json(latest)) if latest.exists() else OperationsReview.create(classification="Estate Internal", warnings=["No operations review has been generated yet."])
        decisions = [d.to_dict() for d in self.list_decisions()[-10:]]
        posture = "attention_required" if review.requires_steward_attention or review.requires_boundary_review else "normal"
        payload = {"generated_at": review.created_at, "current_operational_posture": posture, "items_requiring_attention": review.blocked_intake_count + review.assignment_blocked_count + review.provider_blocked_count, "blocked_items": {"intake": review.blocked_intake_count, "assignments": review.assignment_blocked_count, "providers": review.provider_blocked_count}, "provider_capacity_warnings": review.provider_saturated_count, "assignment_gaps": max(0, review.scheduled_count - review.assignment_active_count), "recommended_next_actions": [a.to_dict() for a in review.recommended_actions], "source_artifacts_inspected": review.source_artifacts, "warnings": review.warnings, "recent_decisions": decisions}
        _write_json(self.root / STATUS_DIR / "summary.json", payload)
        lines = ["# Operations Control Summary", "", f"Generated: {payload['generated_at']}", f"Posture: {posture}", f"Items requiring attention: {payload['items_requiring_attention']}", f"Blocked intake: {review.blocked_intake_count}", f"Blocked assignments: {review.assignment_blocked_count}", f"Blocked providers: {review.provider_blocked_count}", f"Provider saturated: {review.provider_saturated_count}", "", "## Recommended Next Actions"]
        for action in review.recommended_actions:
            lines.append(f"- {action.action_type}: {action.safe_summary}")
        lines += ["", "## Recent Decisions"]
        for dec in decisions:
            lines.append(f"- {dec['decision_id']} {dec['decision_type']} {dec.get('target_type')}:{dec.get('target_id') or ''} - {redact_summary(dec['classification'], dec['reason'], {'summary_safe': dec.get('summary_safe')})}")
        (self.root / STATUS_DIR / "summary.md").parent.mkdir(parents=True, exist_ok=True)
        (self.root / STATUS_DIR / "summary.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    def _inspect_path(self, review: OperationsReview, rel: str) -> Path | None:
        path = self.root / rel
        if path.exists():
            review.source_artifacts.append(rel); return path
        review.warnings.append(f"Missing upstream artifact: {rel}"); return None

    def _inspect_intake(self, review: OperationsReview) -> None:
        path = self._inspect_path(review, "runtime/orchestrator/intake/status/queue.json")
        if path:
            data = _load_json(path); items = data.get("items") or data.get("queue") or data.get("requests") or []
            review.pending_intake_count = sum(1 for x in items if x.get("state") in {"pending", "accepted", "awaiting_decision"})
            review.blocked_intake_count = sum(1 for x in items if x.get("state") == "blocked")

    def _inspect_schedule(self, review: OperationsReview) -> None:
        path = self._inspect_path(review, "runtime/orchestrator/schedule/status/queue.json")
        if path:
            data = _load_json(path); review.scheduled_count = len(data.get("scheduled") or data.get("items") or data.get("queue") or [])

    def _inspect_dispatch(self, review: OperationsReview) -> None:
        path = self._inspect_path(review, "runtime/orchestrator/dispatch/status/queue.json")
        if path:
            data = _load_json(path); items = data.get("pending") or data.get("dispatches") or data.get("items") or []
            review.dispatch_pending_count = sum(1 for x in items if x.get("state") == "pending_dispatch") or len(items)

    def _inspect_assignments(self, review: OperationsReview) -> None:
        path = self._inspect_path(review, "runtime/workers/assignments/status/board.json")
        if path:
            data = _load_json(path); review.assignment_active_count = int(data.get("active_count", 0)); review.assignment_blocked_count = int(data.get("blocked_count", 0))

    def _inspect_providers(self, review: OperationsReview) -> None:
        path = self._inspect_path(review, "runtime/providers/health/status/summary.json")
        if path:
            data = _load_json(path); review.provider_available_count = int(data.get("available_count", 0)); review.provider_blocked_count = int(data.get("blocked_count", 0)) + int(data.get("out_of_quota_count", 0)); review.provider_saturated_count = int(data.get("saturated_count", 0))

    def _emit_decision_event(self, decision: OperationsDecision, path: Path) -> None:
        event_type = {"request_boundary_review": "Boundary Review Required", "escalate": "Waiting for Approval", "request_validation": "Checkpoint Reached"}.get(decision.decision_type, "Checkpoint Reached")
        state = "Awaiting Approval" if decision.requires_steward_attention or decision.decision_type == "escalate" else ("Blocked" if decision.decision_type in {"hold", "request_boundary_review"} else "Waiting")
        event = OperationalEvent.create(event_type=event_type, state=state, classification=decision.classification, message=redact_summary(decision.classification, decision.reason, {"summary_safe": decision.summary_safe}), provider_id=decision.provider_id, worker_id=decision.worker_id, work_package_id=decision.target_id if decision.target_type == "work_package" else None, requires_attention=decision.requires_steward_attention or decision.requires_boundary_review, artifact_paths=[self._rel(path)], metadata={"operations_decision_id": decision.decision_id, "decision_type": decision.decision_type, "target_type": decision.target_type, "target_id": decision.target_id, "summary_safe": decision.summary_safe})
        try: record_operational_event(event, root=self.root)
        except Exception: pass


def format_operations_review(review: OperationsReview, paths: dict[str, str] | None = None) -> str:
    lines = ["Operations review generated", f"Review: {review.review_id}", f"Posture attention: {review.requires_steward_attention}", f"Pending intake: {review.pending_intake_count}", f"Scheduled: {review.scheduled_count}", f"Dispatch pending: {review.dispatch_pending_count}", f"Active assignments: {review.assignment_active_count}", f"Blocked assignments: {review.assignment_blocked_count}", f"Providers available/blocked/saturated: {review.provider_available_count}/{review.provider_blocked_count}/{review.provider_saturated_count}"]
    for warning in review.warnings: lines.append(f"Warning: {warning}")
    if paths:
        for label, path in paths.items(): lines.append(f"{label}: {path}")
    return "\n".join(lines)


def format_operations_decisions(decisions: list[OperationsDecision]) -> str:
    if not decisions: return "No operations decisions recorded."
    return "\n".join(f"{d.decision_id} | {d.decision_type} | {d.target_type} | {d.target_id or ''} | {d.priority} | {d.assignment_label or ''}" for d in decisions)
