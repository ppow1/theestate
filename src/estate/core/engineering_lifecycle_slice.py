"""Authorized, bounded Engineering lifecycle composition for one image proof.

The adapter deliberately owns no queue or lifecycle store.  Its evidence file is
a correlation receipt; canonical state remains in Grace, Helen, Execution
Dispatch, adapter reconciliation, and repository mail.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from estate.core.alfred_runtime import route_operational_message
from estate.core.execution_adapter_handoff_runtime import prepare_handoff
from estate.core.execution_dispatch import DispatchRequest, enqueue_dispatch_request, inspect_dispatch_item, update_dispatch_state
from estate.core.execution_provider_adapter import ExecutionProviderAdapterResult, utc_now
from estate.core.execution_provider_adapter_runtime import write_adapter_result
from estate.core.execution_result_reconciliation_runtime import reconcile_result
from estate.core.grace_operations_runtime import GraceObjective, GraceOperationsRuntime
from estate.core.helen_workforce import HelenWorkforceStore, WorkforceRequest

CAMPAIGN_ID = "CAMPAIGN-0670"
PACKAGE_ID = "WP-0675"
PROVIDER_ID = "deterministic-image-dry-run"
NOTICE_KINDS = {"steward_authority", "blocker", "significant_milestone", "requested_briefing"}


def _stable(prefix: str, correlation_id: str) -> str:
    return f"{prefix}-{hashlib.sha256(correlation_id.encode()).hexdigest()[:16]}"


def _write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


class EngineeringLifecycleSlice:
    """Compose existing governed surfaces; never grant package acceptance."""

    def __init__(self, root: Path, correlation_id: str) -> None:
        self.root = Path(root)
        self.correlation_id = correlation_id
        self.objective_id = _stable("grace-obj", correlation_id)
        self.request_id = _stable("wfr", correlation_id)
        self.dispatch_id = _stable("dispatch", correlation_id)
        self.evidence_path = self.root / "collaboration/evidence" / f"{_stable('engineering-slice', correlation_id)}.json"

    def intake(self, *, occurred_at: str) -> dict[str, Any]:
        """Persist the Grace objective and correlated Helen capability request."""
        objective = GraceObjective(
            objective_id=self.objective_id, created_at=occurred_at, requested_by="Steward",
            title="Bounded Evelyn image-iteration dry-run proof",
            summary="Prove one image-capable Engineering lifecycle without live provider use.",
            work_package_id=PACKAGE_ID, authority="delegated", owner="Engineering",
            checkpoint="Chief Architect validation and acceptance remain required.",
            evidence=["Temp/engineering-resident-operationalization/implementation_scope.json"],
            metadata={"campaign_id": CAMPAIGN_ID, "correlation_id": self.correlation_id,
                      "engineering_department_required": True, "live_provider_authorized": False},
        )
        objective_path = self.root / "runtime/operations/grace/objectives" / f"{occurred_at[:10]}_{self.objective_id}.json"
        if not objective_path.exists():
            GraceOperationsRuntime(self.root).intake_objective(objective)
        request = WorkforceRequest(
            request_id=self.request_id, request_type="staffing_request",
            subject_id=f"{CAMPAIGN_ID}:{PACKAGE_ID}:image-iteration-worker",
            subject_type="operational_capability_need", requesting_office="Office of Operations",
            summary="Engineering requires the governed image-iteration dry-run capability.",
            requested_outcome="Helen records readiness only; Engineering retains dispatch and acceptance boundaries.",
            classification="Estate Internal", source_artifacts=[str(objective_path.relative_to(self.root))],
            requires_steward_attention=False, requires_boundary_review=False, created_at=occurred_at,
            metadata={"campaign_id": CAMPAIGN_ID, "package_id": PACKAGE_ID,
                      "objective_id": self.objective_id, "correlation_id": self.correlation_id,
                      "required_capabilities": ["image_iteration"], "need_kind": "capability",
                      "engineering_priority_authority_granted": False, "acceptance_authority_granted": False},
        )
        HelenWorkforceStore(self.root).save_request(request)
        return self._record("waiting_for_helen", objective_path=str(objective_path.relative_to(self.root)))

    def advance(self) -> dict[str, Any]:
        """Consume durable Helen readiness and idempotently advance one Dispatch."""
        dispositions = [d for d in HelenWorkforceStore(self.root).list_operational_dispositions()
                        if d.get("request_id") == self.request_id]
        ready = next((d for d in dispositions if d.get("disposition") == "fulfilled"
                      and "image_iteration" in (d.get("fulfilled_capabilities") or [])
                      and d.get("authority_evidence") and not d.get("requires_protected_review")), None)
        if not ready:
            return self._record("blocked", blocker="Helen readiness disposition is required")
        try:
            item = inspect_dispatch_item(self.dispatch_id, self.root)
        except KeyError:
            item = enqueue_dispatch_request(DispatchRequest(
                dispatch_id=self.dispatch_id, work_package_id=PACKAGE_ID,
                title="Evelyn image-iteration deterministic proof", requested_by="Engineering",
                assigned_worker="Engineering dry-run image worker", provider=PROVIDER_ID,
                classification="Estate Internal", state="Ready", prompt_source=str(self.evidence_path.relative_to(self.root)),
                sandbox="read-only", allowed_read_paths=["collaboration/work_packages/pending/WP-0675_Engineering_Department_Operational_Readiness_and_Campaign_Acceptance.md"],
                allowed_providers=[PROVIDER_ID],
                provider_metadata={"provider_type": "dry-run", "authorization_reference": "STEWARD AUTHORIZATION: first vertical slice",
                                   "campaign_id": CAMPAIGN_ID, "objective_id": self.objective_id,
                                   "workforce_request_id": self.request_id, "correlation_id": self.correlation_id,
                                   "validation_required": True, "live_provider_called": False}), self.root)
        handoff = prepare_handoff(self.dispatch_id, self.root, write=not bool(item.handoff_reference))
        return self._record("dispatched", helen_disposition_id=ready["disposition_id"],
                            dispatch_id=self.dispatch_id,
                            adapter_request_id=(handoff.get("adapter_request") or {}).get("adapter_request_id"),
                            handoff_reference=(handoff.get("artifacts") or {}).get("request_path") or item.handoff_reference)

    def reconcile_fixture(self, status: str = "completed") -> dict[str, Any]:
        """Return deterministic fixture evidence through canonical reconciliation."""
        item = inspect_dispatch_item(self.dispatch_id, self.root)
        request_id = Path(item.handoff_reference or "").stem
        artifact = f"fixture://{self.correlation_id}/image-iteration-evidence.json"
        result = ExecutionProviderAdapterResult(
            adapter_request_id=request_id, dispatch_id=self.dispatch_id, provider_id=PROVIDER_ID,
            status=status, started_at=utc_now(), finished_at=utc_now(),
            summary="Deterministic image-worker fixture completed; no image or live provider execution occurred.",
            artifacts=[artifact], validation_status="not_run",
            events=[{"event_type": "fixture_progress", "correlation_id": self.correlation_id}],
            metadata={"live_provider_called": False, "real_image_generated": False},
        )
        path = write_adapter_result(result, self.root)
        reconciled = reconcile_result(self.dispatch_id, path, self.root)
        reaction = "advance_to_validation" if reconciled["dispatch_state"] == "Validation" else "block_and_escalate"
        return self._record("result_reconciled", reconciliation=reconciled, grace_reaction=reaction,
                            retry_authority={"maximum_attempts": 1, "attempts_used": 0},
                            acceptance_granted=False)

    def notify(self, kind: str, *, occurred_at: str) -> dict[str, Any]:
        """Let Alfred route only an authorized Steward-attention class."""
        if kind not in NOTICE_KINDS:
            return {"recorded": False, "suppressed": True, "reason": "routine Engineering event"}
        message_id = _stable(f"msg-{kind}", self.correlation_id)
        return route_operational_message({
            "id": message_id, "version": 1, "created_at": occurred_at, "created_by": "Grace",
            "source": "Grace", "source_employee_id": 12, "destination": "Steward",
            "destination_employee_id": 1, "destination_mailbox_id": 1,
            "classification": "Estate Internal", "message_type": "blocker_escalation" if kind == "blocker" else ("protected_decision_request" if kind == "steward_authority" else "notification"),
            "priority": "high" if kind in {"blocker", "steward_authority"} else "normal", "status": "open",
            "requires_ack": True, "ack_status": "pending", "thread_id": _stable("thread", self.correlation_id),
            "related_work_package": PACKAGE_ID,
            "payload": {"title": kind.replace("_", " ").title(), "summary": "Bounded Engineering lifecycle attention.",
                        "instructions": "Alfred routes only and does not mutate Engineering state.", "artifact_refs": [str(self.evidence_path.relative_to(self.root))]},
            "operational_context": {"campaign_id": CAMPAIGN_ID, "objective_id": self.objective_id,
                                    "dispatch_id": self.dispatch_id, "notification_kind": kind, "authorizes_action": False},
        }, root=self.root, now=occurred_at)

    def momentum(self) -> dict[str, Any]:
        """Continuous Momentum's caller-supplied action invokes this same adapter."""
        before = self.evidence_path.read_text() if self.evidence_path.exists() else None
        result = self.advance()
        return {"adapter": "EngineeringLifecycleSlice.advance", "result": result,
                "deterministic_replay": before == self.evidence_path.read_text() if before else False}

    def _record(self, state: str, **extra: Any) -> dict[str, Any]:
        prior = json.loads(self.evidence_path.read_text()) if self.evidence_path.exists() else {}
        payload = {**prior, "schema_version": "estate.engineering-lifecycle-slice.v1",
                   "correlation_id": self.correlation_id, "campaign_id": CAMPAIGN_ID,
                   "work_package_id": PACKAGE_ID, "objective_id": self.objective_id,
                   "workforce_request_id": self.request_id, "dispatch_id": self.dispatch_id,
                   "state": state, "engineering_association_required": True,
                   "chief_architect_acceptance_required": True, "acceptance_granted": False,
                   "live_provider_called": False, "real_image_generated": False, **extra}
        _write(self.evidence_path, payload)
        return payload
