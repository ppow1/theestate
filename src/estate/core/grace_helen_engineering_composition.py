"""Canonical composition of Grace operational ownership with Helen and Engineering.

This is deliberately a record-and-boundary layer.  It reuses the existing
Grace runtime, Helen workforce root, execution Dispatch queue, and execution
result reconciliation; it never invokes a provider itself.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4

from estate.core.execution_dispatch import DispatchRequest, enqueue_dispatch_request
from estate.core.execution_provider_adapter import ExecutionProviderAdapterResult, utc_now
from estate.core.execution_provider_adapter_runtime import write_adapter_result
from estate.core.execution_result_reconciliation_runtime import reconcile_result
from estate.core.engineering_capability_enablement import CapabilityEnablementLifecycle, CapabilityEvidence
from estate.core.grace_operations_runtime import GraceOperationsRuntime
from estate.core.ptm_readiness_integration import PtmReadinessGateError, PtmProductionReadinessResolver, revalidate_readiness, resolve_and_bind
from estate.core.paths import ESTATE_ROOT

ROOT = Path("runtime/grace_helen_engineering")
CAPABILITY_REQUESTS = ROOT / "capability_requests"
DETERMINATIONS = ROOT / "helen_determinations"
DEVELOPMENT = ROOT / "capability_development"
COMMISSIONS = ROOT / "engineering_commissions"
AUTHORIZATIONS = ROOT / "engineering_authorizations"
VALIDATIONS = ROOT / "engineering_validations"
COMPLETIONS = ROOT / "engineering_completions"
RECEIPTS = ROOT / "grace_receipts"
DISPATCH_REJECTIONS = ROOT / "dispatch_rejections"
COMPLETION_REJECTIONS = ROOT / "completion_rejections"

DETERMINATIONS_ALLOWED = {"qualified_and_available", "qualified_but_unavailable", "capability_absent", "capability_unknown", "capability_suspended"}
COMMISSION_STATES = {"proposed", "accepted", "blocked", "rejected", "authorized_for_dispatch", "executing", "validating", "completed", "failed", "cancelled"}


def _root(root: str | Path | None) -> Path:
    return Path(root) if root is not None else ESTATE_ROOT


def _write(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if existing != payload:
            raise ValueError(f"idempotency conflict at {path}")
    else:
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _load(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValueError(f"record not found: {path.name}")
    return json.loads(path.read_text(encoding="utf-8"))


def _write_immutable(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if existing != payload:
            raise ValueError(f"immutable record conflict at {path}")
        return existing
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


@dataclass
class CapabilityVerificationRequest:
    capability_request_id: str
    grace_objective_id: str
    requested_capability: str
    created_at: str
    idempotency_key: str
    constraints: list[str] = field(default_factory=list)
    status: str = "requested"

    @classmethod
    def create(cls, grace_objective_id: str, requested_capability: str, *, constraints: list[str] | None = None, idempotency_key: str | None = None):
        return cls(f"capreq-{uuid4().hex[:12]}", grace_objective_id, requested_capability, utc_now(), idempotency_key or f"{grace_objective_id}:{requested_capability}", constraints or [])


class GraceHelenEngineeringComposition:
    """Durable, correlation-first lifecycle composed from existing runtime seams."""
    def __init__(self, root: str | Path | None = None, *, ptm_resolver: PtmProductionReadinessResolver | None = None) -> None:
        self.root = _root(root)
        self.ptm_resolver = ptm_resolver or PtmProductionReadinessResolver(self.root)
        self.capability_enablement = CapabilityEnablementLifecycle(self.root)

    def create_capability_inquiry(self, **kwargs: Any) -> dict[str, Any]:
        """Grace-owned inquiry entry point; provider selection remains outside Grace."""
        return self.capability_enablement.create_inquiry(**kwargs)

    def assess_required_capabilities(self, inquiry_id: str, evidence: list[CapabilityEvidence | dict[str, Any]]) -> dict[str, Any]:
        """Helen-owned evidence assessment composed through the existing boundary."""
        return self.capability_enablement.assess(inquiry_id, evidence)

    def record_capability_registration(self, **kwargs: Any) -> dict[str, Any]:
        return self.capability_enablement.record_registration(**kwargs)

    def reevaluate_capability_and_resume(self, **kwargs: Any) -> dict[str, Any]:
        return self.capability_enablement.reevaluate(**kwargs)

    def _path(self, directory: Path, record_id: str) -> Path:
        return self.root / directory / f"{record_id}.json"

    def _state(self, objective_id: str, state: str, **extra: Any) -> dict[str, Any]:
        return GraceOperationsRuntime(self.root).record_objective_transition(objective_id, state, **extra)

    def request_capability(self, grace_objective_id: str, capability: str, *, constraints: list[str] | None = None, idempotency_key: str | None = None) -> dict[str, Any]:
        req = CapabilityVerificationRequest.create(grace_objective_id, capability, constraints=constraints, idempotency_key=idempotency_key)
        # stable idempotency lookup avoids a latest-record inference.
        directory = self.root / CAPABILITY_REQUESTS
        for p in directory.glob("*.json") if directory.exists() else []:
            existing = _load(p)
            if existing.get("idempotency_key") == req.idempotency_key:
                return existing
        payload = asdict(req)
        _write(self._path(CAPABILITY_REQUESTS, req.capability_request_id), payload)
        self._state(grace_objective_id, "awaiting_capability_verification", capability_request_id=req.capability_request_id)
        return payload

    def determine_capability(self, capability_request_id: str, *, disposition: str, worker_profile_id: str | None = None, qualification_evidence: list[str] | None = None, availability_evidence: list[str] | None = None, reason: str = "", idempotency_key: str | None = None) -> dict[str, Any]:
        if disposition not in DETERMINATIONS_ALLOWED:
            raise ValueError("unknown Helen capability disposition")
        request = _load(self._path(CAPABILITY_REQUESTS, capability_request_id))
        key = idempotency_key or f"{capability_request_id}:{disposition}"
        directory = self.root / DETERMINATIONS
        for p in directory.glob("*.json") if directory.exists() else []:
            existing = _load(p)
            if existing.get("idempotency_key") == key:
                return existing
        if disposition == "qualified_and_available" and (not worker_profile_id or not qualification_evidence or not availability_evidence):
            raise ValueError("qualified_and_available requires worker profile, qualification, and availability evidence")
        det = {"determination_id": f"heldet-{uuid4().hex[:12]}", "capability_request_id": capability_request_id, "grace_objective_id": request["grace_objective_id"], "capability_class": request["requested_capability"], "disposition": disposition, "worker_profile_id": worker_profile_id, "qualification_evidence": qualification_evidence or [], "availability_evidence": availability_evidence or [], "reason": reason, "determined_by": "Helen", "determined_at": utc_now(), "idempotency_key": key}
        _write(self._path(DETERMINATIONS, det["determination_id"]), det)
        if disposition in {"capability_absent", "capability_unknown"}:
            dev = {"capability_development_id": f"capdev-{uuid4().hex[:12]}", "grace_objective_id": request["grace_objective_id"], "helen_determination_id": det["determination_id"], "capability_class": request["requested_capability"], "readiness_owner": "Helen", "technical_definition_owner": "Engineering", "state": "requirements_definition", "created_at": utc_now(), "idempotency_key": f"{det['determination_id']}:development"}
            _write(self._path(DEVELOPMENT, dev["capability_development_id"]), dev)
            self._state(request["grace_objective_id"], "blocked_pending_capability", helen_determination_id=det["determination_id"], capability_development_id=dev["capability_development_id"])
        elif disposition == "qualified_but_unavailable":
            self._state(request["grace_objective_id"], "blocked_pending_capability", helen_determination_id=det["determination_id"], blocker="qualified capability unavailable")
        elif disposition == "capability_suspended":
            self._state(request["grace_objective_id"], "blocked_pending_capability", helen_determination_id=det["determination_id"], blocker="capability suspended")
        return det

    def commission_engineering(self, grace_objective_id: str, helen_determination_id: str, *, grace_action_id: str, operations_decision_id: str, bounded_objective: str, acceptance_criteria: list[str], ptm_source_high_watermark: str | None = None, ptm_task_or_package_id: str | None = None, enabling_project_id: str | None = None, idempotency_key: str | None = None) -> dict[str, Any]:
        det = _load(self._path(DETERMINATIONS, helen_determination_id))
        if det["grace_objective_id"] != grace_objective_id:
            raise ValueError("Helen determination does not belong to Grace objective")
        if det["disposition"] != "qualified_and_available":
            raise PermissionError("Engineering commission requires qualified_and_available Helen determination")
        if not ptm_source_high_watermark or not ptm_task_or_package_id:
            raise PermissionError("PTM readiness resolution is required before Engineering commission creation")
        try:
            binding = resolve_and_bind(
                self.root,
                objective_id=grace_objective_id,
                enabling_project_id=enabling_project_id,
                task_or_package_id=ptm_task_or_package_id,
                source_high_watermark=ptm_source_high_watermark,
                observed_at=utc_now(),
                resolver=self.ptm_resolver,
            )
        except PtmReadinessGateError as exc:
            self._state(grace_objective_id, "awaiting_ptm_readiness", blocker=str(exc))
            raise PermissionError(str(exc)) from exc
        key = idempotency_key or f"{grace_objective_id}:{helen_determination_id}:commission"
        directory = self.root / COMMISSIONS
        for p in directory.glob("*.json") if directory.exists() else []:
            existing = _load(p)
            if existing.get("idempotency_key") == key:
                return existing
        commission = {"commission_id": f"engcom-{uuid4().hex[:12]}", "grace_objective_id": grace_objective_id, "grace_action_id": grace_action_id, "operations_decision_id": operations_decision_id, "helen_determination_id": helen_determination_id, "required_capability": det["capability_class"], "bounded_objective": bounded_objective, "acceptance_criteria": acceptance_criteria, "status": "proposed", "created_at": utc_now(), "idempotency_key": key, "requesting_office": "Grace", "technical_owner": "Engineering", "readiness_resolution_id": binding.readiness_resolution_id, "readiness_projection_path": binding.readiness_projection_path, "readiness_projection_digest": binding.readiness_projection_digest, "readiness_state": binding.readiness_state, "source_high_watermark": binding.source_high_watermark, "freshness_policy_id": binding.freshness_policy_id, "freshness_policy_version": binding.freshness_policy_version, "freshness_policy_digest": binding.freshness_policy_digest, "waiver_registry_id": binding.waiver_registry_id, "waiver_registry_version": binding.waiver_registry_version, "waiver_registry_digest": binding.waiver_registry_digest, "evaluated_at": binding.evaluated_at, "expires_at": binding.expires_at, "dependency_evidence_references": list(binding.dependency_evidence_references), "waiver_references": [dict(item) for item in binding.waiver_references], "ptm_readiness": binding.to_dict()}
        _write(self._path(COMMISSIONS, commission["commission_id"]), commission)
        self._state(grace_objective_id, "awaiting_engineering_acceptance", engineering_commission_id=commission["commission_id"])
        return commission

    def accept_commission(self, commission_id: str) -> dict[str, Any]:
        p = self._path(COMMISSIONS, commission_id); rec = _load(p)
        if rec["status"] == "accepted": return rec
        if rec["status"] != "proposed": raise ValueError("commission cannot be accepted from current state")
        rec["status"] = "accepted"; rec["accepted_at"] = utc_now(); _write_replace(p, rec); self._state(rec["grace_objective_id"], "engineering_in_progress", engineering_commission_id=commission_id); return rec

    def governed_commission_and_dispatch(self, grace_objective_id: str, helen_determination_id: str, *, grace_action_id: str, operations_decision_id: str, bounded_objective: str, acceptance_criteria: list[str], ptm_source_high_watermark: str, ptm_task_or_package_id: str, enabling_project_id: str | None, provider_id: str, provider_type: str, adapter_reference: str, idempotency_key: str | None = None) -> dict[str, Any]:
        """Bounded public entry point through commission and Dispatch gates.

        Provider execution remains downstream of the canonical Dispatch queue;
        this method never invokes a provider or grants acceptance.
        """
        commission = self.commission_engineering(
            grace_objective_id,
            helen_determination_id,
            grace_action_id=grace_action_id,
            operations_decision_id=operations_decision_id,
            bounded_objective=bounded_objective,
            acceptance_criteria=acceptance_criteria,
            ptm_source_high_watermark=ptm_source_high_watermark,
            ptm_task_or_package_id=ptm_task_or_package_id,
            enabling_project_id=enabling_project_id,
            idempotency_key=idempotency_key,
        )
        accepted = self.accept_commission(commission["commission_id"])
        authorization, dispatch = self.authorize_dispatch(
            accepted["commission_id"],
            provider_id=provider_id,
            provider_type=provider_type,
            adapter_reference=adapter_reference,
            idempotency_key=f"{idempotency_key or commission['idempotency_key']}:dispatch",
        )
        return {"commission": accepted, "authorization": authorization, "dispatch": dispatch, "provider_execution": "pending_dispatch_consumer", "institutional_acceptance_state": "not_granted"}

    def authorize_dispatch(self, commission_id: str, *, provider_id: str, provider_type: str, adapter_reference: str, idempotency_key: str | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
        commission = _load(self._path(COMMISSIONS, commission_id))
        if commission["status"] not in {"accepted", "authorized_for_dispatch"}: raise PermissionError("Engineering must accept commission before Dispatch")
        det = _load(self._path(DETERMINATIONS, commission["helen_determination_id"]))
        if det["disposition"] != "qualified_and_available": raise PermissionError("Helen determination no longer qualifies capability")
        try:
            binding = revalidate_readiness(self.root, commission["ptm_readiness"], commission_id=commission_id)
        except PtmReadinessGateError as exc:
            reason = str(exc)
            rejection_key = f"{commission_id}:{commission['readiness_resolution_id']}:{reason}"
            rejection = {"rejection_id": f"dispatch-rejection-{uuid4().hex[:12]}", "engineering_commission_id": commission_id, "readiness_resolution_id": commission.get("readiness_resolution_id"), "rejection_state": "blocked", "reason": reason, "rejected_at": utc_now(), "idempotency_key": rejection_key, "institutional_acceptance_state": "not_granted"}
            rejection_dir = self.root / DISPATCH_REJECTIONS
            existing = next((json.loads(path.read_text(encoding="utf-8")) for path in rejection_dir.glob("*.json") if path.exists() and json.loads(path.read_text(encoding="utf-8")).get("idempotency_key") == rejection_key), None) if rejection_dir.exists() else None
            if existing is None:
                _write_immutable(self._path(DISPATCH_REJECTIONS, rejection["rejection_id"]), rejection)
            self._state(commission["grace_objective_id"], "dispatch_rejected_ptm_stale", engineering_commission_id=commission_id, blocker=reason, dispatch_rejection_id=(existing or rejection)["rejection_id"])
            raise PermissionError(str(exc)) from exc
        key = idempotency_key or f"{commission_id}:{provider_id}:authorization"
        directory = self.root / AUTHORIZATIONS
        for p in directory.glob("*.json") if directory.exists() else []:
            existing = _load(p)
            if existing.get("idempotency_key") == key: return existing, _load(Path(existing["dispatch_record_path"]))
        auth = {"authorization_id": f"engauth-{uuid4().hex[:12]}", "engineering_commission_id": commission_id, "engineering_work_item_id": f"engwork-{commission_id}", "selected_capability_profile": det["worker_profile_id"], "provider_selection_id": f"engsel-{uuid4().hex[:12]}", "provider_id": provider_id, "adapter_reference": adapter_reference, "created_at": utc_now(), "idempotency_key": key}
        request = DispatchRequest(work_package_id=commission["grace_objective_id"], title=commission["bounded_objective"], requested_by="Engineering", assigned_worker=det["worker_profile_id"], provider=provider_id, profile_label=det["worker_profile_id"], classification="Estate Internal", priority="Normal", state="Ready", allowed_providers=[provider_id], provider_metadata={"technical_execution": True, "grace_objective_id": commission["grace_objective_id"], "engineering_commission_id": commission_id, "engineering_authorization_id": auth["authorization_id"], "helen_determination_id": det["determination_id"], "capability_disposition": det["disposition"], "provider_type": provider_type, "validation_required": True, "institutional_acceptance_state": "not_granted", "ptm_readiness": binding.to_dict(), "ptm_revalidated_at": utc_now(), "ptm_revalidation_result": "passed"})
        item = enqueue_dispatch_request(request, self.root)
        auth["dispatch_id"] = item.dispatch_id; auth["dispatch_record_path"] = str(self.root / "runtime/execution_dispatch/queue.json"); auth["ptm_readiness"] = binding.to_dict(); auth["ptm_revalidated_at"] = request.provider_metadata["ptm_revalidated_at"]; auth["ptm_revalidation_result"] = "passed"
        _write(self._path(AUTHORIZATIONS, auth["authorization_id"]), auth)
        commission["status"] = "authorized_for_dispatch"; _write_replace(self._path(COMMISSIONS, commission_id), commission); self._state(commission["grace_objective_id"], "awaiting_dispatch", engineering_commission_id=commission_id, dispatch_id=item.dispatch_id)
        return auth, item.to_dict()

    def reconcile_validate_complete(self, authorization_id: str, result: ExecutionProviderAdapterResult, *, validation_passed: bool) -> dict[str, Any]:
        auth = _load(self._path(AUTHORIZATIONS, authorization_id)); commission = _load(self._path(COMMISSIONS, auth["engineering_commission_id"]))
        def reject(reason: str) -> None:
            rejection = {"rejection_id": f"completion-rejection-{uuid4().hex[:12]}", "engineering_commission_id": commission["commission_id"], "dispatch_id": auth.get("dispatch_id"), "ptm_readiness_resolution_id": auth.get("ptm_readiness", {}).get("readiness_resolution_id"), "rejection_state": "blocked", "reason": reason, "rejected_at": utc_now(), "idempotency_key": f"{authorization_id}:{reason}", "institutional_acceptance_state": "not_granted"}
            _write_immutable(self._path(COMPLETION_REJECTIONS, rejection["rejection_id"]), rejection)
            self._state(commission["grace_objective_id"], "completion_rejected", engineering_commission_id=commission["commission_id"], completion_rejection_id=rejection["rejection_id"], blocker=reason)
            raise ValueError(reason)
        if result.dispatch_id != auth["dispatch_id"]: reject("unrelated raw result cannot satisfy authorization")
        try:
            result_path = write_adapter_result(result, self.root); reconciliation = reconcile_result(auth["dispatch_id"], result_path, self.root)
        except (ValueError, OSError) as exc:
            reject(f"completion reconciliation failed: {exc}")
        if not validation_passed or result.status not in {"completed", "dry_run_completed"}: reject("Engineering validation failed; no successful completion created")
        if result.validation_status != "passed": reject("commission-specific validation receipt is required before completion")
        if not result.artifacts: reject("at least one produced artifact or work-product reference is required before completion")
        if not (result.metadata.get("provider_receipt") or result.metadata.get("receipt_reference")):
            reject("provider invocation receipt is required before completion")
        self._state(commission["grace_objective_id"], "engineering_completion_pending", engineering_commission_id=commission["commission_id"], dispatch_id=auth["dispatch_id"])
        validation = {"validation_id": f"engval-{uuid4().hex[:12]}", "engineering_commission_id": commission["commission_id"], "dispatch_id": auth["dispatch_id"], "reconciliation_reference": reconciliation["reconciliation_path"], "artifact_references": result.artifacts, "disposition": "pass", "validated_by": "Engineering", "created_at": utc_now(), "idempotency_key": f"{authorization_id}:{reconciliation['result_content_hash']}", "ptm_readiness_resolution_id": auth["ptm_readiness"]["readiness_resolution_id"], "ptm_readiness_projection_digest": auth["ptm_readiness"]["readiness_projection_digest"], "ptm_source_high_watermark": auth["ptm_readiness"]["source_high_watermark"], "provider_receipt_reference": result.metadata.get("provider_receipt") or result.metadata.get("receipt_reference")}
        _write(self._path(VALIDATIONS, validation["validation_id"]), validation)
        completion = {"completion_id": f"engcomp-{uuid4().hex[:12]}", "grace_objective_id": commission["grace_objective_id"], "engineering_commission_id": commission["commission_id"], "engineering_work_item_id": auth["engineering_work_item_id"], "disposition": "completed_successfully", "validation_record_id": validation["validation_id"], "dispatch_id": auth["dispatch_id"], "reconciliation_reference": reconciliation["reconciliation_path"], "artifact_references": result.artifacts, "completed_at": utc_now(), "idempotency_key": validation["idempotency_key"], "ptm_readiness_resolution_id": auth["ptm_readiness"]["readiness_resolution_id"], "ptm_readiness_projection_path": auth["ptm_readiness"]["readiness_projection_path"], "ptm_readiness_projection_digest": auth["ptm_readiness"]["readiness_projection_digest"], "ptm_readiness_state": auth["ptm_readiness"]["readiness_state"], "ptm_source_high_watermark": auth["ptm_readiness"]["source_high_watermark"], "ptm_freshness_policy_id": auth["ptm_readiness"]["freshness_policy_id"], "ptm_freshness_policy_version": auth["ptm_readiness"]["freshness_policy_version"], "ptm_freshness_policy_digest": auth["ptm_readiness"]["freshness_policy_digest"], "ptm_waiver_registry_id": auth["ptm_readiness"]["waiver_registry_id"], "ptm_waiver_registry_version": auth["ptm_readiness"]["waiver_registry_version"], "ptm_waiver_registry_digest": auth["ptm_readiness"]["waiver_registry_digest"], "provider_execution_receipt": result.metadata.get("provider_receipt") or result.metadata.get("receipt_reference"), "validation_evidence": validation["validation_id"], "reconciliation_outcome": reconciliation["status"]}
        _write(self._path(COMPLETIONS, completion["completion_id"]), completion); commission["status"] = "completed"; _write_replace(self._path(COMMISSIONS, commission["commission_id"]), commission); self._state(commission["grace_objective_id"], "awaiting_operational_receipt", engineering_completion_id=completion["completion_id"]); return completion

    def receive_completion(self, completion_id: str, grace_objective_id: str) -> dict[str, Any]:
        completion = _load(self._path(COMPLETIONS, completion_id))
        if completion["grace_objective_id"] != grace_objective_id: raise ValueError("completion does not belong to Grace objective")
        key = f"{completion_id}:{grace_objective_id}"
        directory = self.root / RECEIPTS
        for p in directory.glob("*.json") if directory.exists() else []:
            existing = _load(p)
            if existing.get("idempotency_key") == key: return existing
        receipt = {"receipt_id": f"gracereceipt-{uuid4().hex[:12]}", "completion_id": completion_id, "commission_id": completion["engineering_commission_id"], "grace_objective_id": grace_objective_id, "validation_result": "matched_validated_completion", "acknowledgement_state": "acknowledged", "objective_transition_applied": "completed", "acknowledged_at": utc_now(), "idempotency_key": key, "ptm_readiness_resolution_id": completion["ptm_readiness_resolution_id"], "ptm_readiness_projection_digest": completion["ptm_readiness_projection_digest"], "institutional_acceptance_state": "not_granted"}
        _write(self._path(RECEIPTS, receipt["receipt_id"]), receipt); self._state(grace_objective_id, "completed", grace_receipt_id=receipt["receipt_id"]); return receipt

    def objective_state(self, objective_id: str) -> dict[str, Any]:
        return _load(self.root / "runtime/operations/grace/objective_states" / f"{objective_id}.json")


def _write_replace(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
