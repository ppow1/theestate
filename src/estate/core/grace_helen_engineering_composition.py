"""Canonical composition of Grace operational ownership with Helen and Engineering.

This is deliberately a record-and-boundary layer.  It reuses the existing
Grace runtime, Helen workforce root, execution Dispatch queue, and execution
result reconciliation; it never invokes a provider itself.
"""
from __future__ import annotations

import json
import hashlib
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from estate.core.execution_dispatch import DispatchRequest, enqueue_dispatch_request, load_dispatch_queue
from estate.core.execution_provider_adapter import ExecutionProviderAdapterResult, utc_now
from estate.core.execution_provider_adapter_runtime import write_adapter_result
from estate.core.execution_result_reconciliation_runtime import reconcile_result
from estate.core.authority_schema_runtime import canonical_record_digest, require_valid
from estate.core.engineering_capability_enablement import CapabilityEnablementLifecycle, CapabilityEvidence
from estate.core.grace_operations_runtime import GraceOperationsRuntime
from estate.core.operations_control_runtime import OperationsControlRuntime
from estate.core.operations_manager import OperationsDecision
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


def _durable_write(path: Path, payload: dict[str, Any]) -> None:
    """Create a new authority record with complete, durable persistence."""
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    try:
        descriptor = os.open(str(path), flags)
    except FileExistsError:
        existing = json.loads(path.read_text(encoding="utf-8"))
        if existing != payload:
            raise ValueError(f"conflicting authority replay at {path}")
        return
    try:
        with os.fdopen(descriptor, "wb") as handle:
            descriptor = -1
            handle.write(encoded); handle.flush(); os.fsync(handle.fileno())
        try:
            directory = os.open(str(path.parent), os.O_RDONLY)
            try: os.fsync(directory)
            finally: os.close(directory)
        except OSError:
            pass
    except Exception:
        if descriptor != -1:
            os.close(descriptor)
        raise


def _record_by_id(root: Path, directory: Path, record_id: str) -> tuple[Path, dict[str, Any]] | None:
    target = root / directory
    for path in target.glob("*.json") if target.exists() else []:
        try:
            record = _load(path)
        except (OSError, ValueError):
            continue
        if record.get("action_id") == record_id or record.get("objective_id") == record_id:
            return path, record
    return None


def _provider_extension(root: Path, determination: dict[str, Any], authority: dict[str, Any], *, provider_id: str, adapter_reference: str) -> dict[str, Any] | None:
    """Build the closed provider extension from canonical Helen/config evidence."""
    if provider_id != "qwen.local.text":
        return None
    config_path = root / "config/providers/qwen_local_text.json"
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        config = {}
    if config.get("provider_id") != provider_id or not config.get("model_identity"):
        fallback = Path(__file__).resolve().parents[3] / "config/providers/qwen_local_text.json"
        config = json.loads(fallback.read_text(encoding="utf-8"))
    if config.get("provider_id") != provider_id or config.get("adapter_id") not in adapter_reference or config.get("adapter_version") not in adapter_reference:
        raise ValueError("Qwen provider configuration and selected adapter do not match")
    capability = str(determination.get("capability_class") or "")
    if capability not in list(config.get("supported_capabilities") or []):
        raise PermissionError("Helen capability is not supported by the selected Qwen provider")
    observed = determination.get("evidence_observed_at") or determination.get("determined_at")
    expires = determination.get("evidence_expires_at")
    if not expires and observed:
        expires = (datetime.fromisoformat(str(observed).replace("Z", "+00:00")) + timedelta(seconds=int(config.get("evidence_freshness_seconds", 3600)))).isoformat(timespec="seconds").replace("+00:00", "Z")
    try:
        observed_dt = datetime.fromisoformat(str(observed).replace("Z", "+00:00"))
        expires_dt = datetime.fromisoformat(str(expires).replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise PermissionError("Helen capability evidence timestamps are required") from exc
    now = datetime.now(timezone.utc)
    if observed_dt.tzinfo is None or expires_dt.tzinfo is None or observed_dt > now or expires_dt <= now or expires_dt <= observed_dt:
        raise PermissionError("Helen capability evidence is stale or malformed")
    outputs = [str(path).replace("\\", "/") for path in list(authority.get("expected_outputs") or [])]
    writes = [str(path).replace("\\", "/") for path in list(authority.get("allowed_write_paths") or [])]
    receipt_paths = [path for path in outputs if path.startswith("runtime/engineering_adapter_receipts/") and path.endswith(".json")]
    artifact_paths = [path for path in outputs if not path.startswith("runtime/")]
    if len(receipt_paths) != 1 or len(artifact_paths) != 1 or set(outputs) != set(writes):
        raise PermissionError("Qwen execution requires exactly one bounded artifact and one provider receipt output")
    determination_path = f"runtime/grace_helen_engineering/helen_determinations/{determination['determination_id']}.json"
    health_evidence = [determination_path] + [str(path).replace("\\", "/") for path in list(determination.get("provider_health_evidence") or [])]
    health_digests = [hashlib.sha256((root / path).read_bytes()).hexdigest() for path in health_evidence]
    return {
        "schema_version": "estate.qwen-local-text.execution-extension.v1",
        "provider_id": provider_id,
        "adapter_id": config["adapter_id"],
        "adapter_version": config["adapter_version"],
        "requested_capability": capability,
        "evidence_observed_at": str(observed).replace("+00:00", "Z"),
        "evidence_expires_at": str(expires).replace("+00:00", "Z"),
        "authorized_model_identity": config["model_identity"],
        "provider_receipt_path": receipt_paths[0],
        "artifact_path": artifact_paths[0],
        "provider_health_evidence": health_evidence,
        "provider_health_evidence_digests": health_digests,
    }


def _canonical_execution_authority(root: Path, objective_id: str, action_id: str, metadata: dict[str, Any] | None) -> dict[str, Any]:
    objective_record = _record_by_id(root, Path("runtime/operations/grace/objectives"), objective_id)
    action_record = _record_by_id(root, Path("runtime/operations/grace/actions"), action_id)
    if not action_record:
        return {}
    action_data = action_record[1]
    objective_authority = ((objective_record[1].get("metadata") or {}).get("execution_authority") if objective_record else None)
    action_authority = (action_data.get("metadata") or {}).get("execution_authority")
    if not isinstance(action_authority, dict):
        action_authority = action_data.get("execution_metadata") if isinstance(action_data.get("execution_metadata"), dict) else None
    if not isinstance(action_authority, dict):
        action_authority = objective_authority if isinstance(objective_authority, dict) else None
    if not isinstance(action_authority, dict):
        return {}
    if isinstance(objective_authority, dict) and objective_authority != action_authority:
        raise ValueError("Grace objective and action execution authority conflict")
    if isinstance(metadata, dict) and metadata and metadata != action_authority:
        raise ValueError("caller execution metadata is not the canonical Grace authority")
    source_path = action_record[0]
    prompt_source = str(source_path.relative_to(root)).replace("\\", "/")
    read_paths = list(action_authority.get("allowed_read_paths") or [])
    write_paths = list(action_authority.get("allowed_write_paths") or [])
    outputs = list(action_authority.get("expected_outputs") or write_paths)
    authority = {
        "prompt_source": prompt_source,
        "prompt_source_type": "estate.grace.action.v1",
        "allowed_read_paths": read_paths,
        "allowed_write_paths": write_paths,
        "expected_outputs": outputs,
        "grace_objective_id": objective_id,
        "grace_action_id": action_id,
        "prompt_source_record": prompt_source,
    }
    authority["prompt_source_digest"] = hashlib.sha256(source_path.read_bytes()).hexdigest()
    return authority


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

    def determine_capability(self, capability_request_id: str, *, disposition: str, worker_profile_id: str | None = None, qualification_evidence: list[str] | None = None, availability_evidence: list[str] | None = None, capacity_evidence: list[str] | None = None, authorization_evidence: list[str] | None = None, provider_health_evidence: list[str] | None = None, evidence_observed_at: str | None = None, evidence_expires_at: str | None = None, reason: str = "", idempotency_key: str | None = None) -> dict[str, Any]:
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
        determined_at = utc_now()
        observed_at = evidence_observed_at or determined_at
        expires_at = evidence_expires_at
        if not expires_at:
            expires_at = (datetime.fromisoformat(observed_at.replace("Z", "+00:00")) + timedelta(hours=1)).isoformat(timespec="seconds").replace("+00:00", "Z")
        det = {"determination_id": f"heldet-{uuid4().hex[:12]}", "capability_request_id": capability_request_id, "grace_objective_id": request["grace_objective_id"], "capability_class": request["requested_capability"], "disposition": disposition, "worker_profile_id": worker_profile_id, "qualification_evidence": qualification_evidence or [], "availability_evidence": availability_evidence or [], "capacity_evidence": capacity_evidence or [], "authorization_evidence": authorization_evidence or [], "provider_health_evidence": provider_health_evidence or [], "evidence_observed_at": observed_at, "evidence_expires_at": expires_at, "reason": reason, "determined_by": "Helen", "determined_at": determined_at, "idempotency_key": key}
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

    def commission_engineering(self, grace_objective_id: str, helen_determination_id: str, *, grace_action_id: str, operations_decision_id: str, bounded_objective: str, acceptance_criteria: list[str], ptm_source_high_watermark: str | None = None, ptm_task_or_package_id: str | None = None, enabling_project_id: str | None = None, execution_metadata: dict[str, Any] | None = None, provider_id: str | None = None, adapter_reference: str | None = None, idempotency_key: str | None = None) -> dict[str, Any]:
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
        authority = _canonical_execution_authority(self.root, grace_objective_id, grace_action_id, execution_metadata)
        if provider_id and provider_id == "qwen.local.text":
            extension = _provider_extension(self.root, det, authority, provider_id=provider_id, adapter_reference=adapter_reference or "")
            authority = {**authority, "provider_extension": extension}
        action_record = _record_by_id(self.root, Path("runtime/operations/grace/actions"), grace_action_id)
        canonical_decision_id = ((action_record[1].get("metadata") or {}).get("operations_decision_id") if action_record else None)
        if canonical_decision_id and operations_decision_id and canonical_decision_id != operations_decision_id:
            raise ValueError("caller operations decision does not match canonical Grace decision")
        operations_decision_id = canonical_decision_id or operations_decision_id
        directory = self.root / COMMISSIONS
        for p in directory.glob("*.json") if directory.exists() else []:
            existing = _load(p)
            if existing.get("idempotency_key") == key:
                if (existing.get("execution_authority") or {}) != authority:
                    raise ValueError("conflicting execution authority replay")
                return existing
        commission = {"commission_id": f"engcom-{uuid4().hex[:12]}", "grace_objective_id": grace_objective_id, "grace_action_id": grace_action_id, "operations_decision_id": operations_decision_id, "helen_determination_id": helen_determination_id, "required_capability": det["capability_class"], "bounded_objective": bounded_objective, "acceptance_criteria": acceptance_criteria, "status": "proposed", "created_at": utc_now(), "idempotency_key": key, "requesting_office": "Grace", "technical_owner": "Engineering", "readiness_resolution_id": binding.readiness_resolution_id, "readiness_projection_path": binding.readiness_projection_path, "readiness_projection_digest": binding.readiness_projection_digest, "readiness_state": binding.readiness_state, "source_high_watermark": binding.source_high_watermark, "freshness_policy_id": binding.freshness_policy_id, "freshness_policy_version": binding.freshness_policy_version, "freshness_policy_digest": binding.freshness_policy_digest, "waiver_registry_id": binding.waiver_registry_id, "waiver_registry_version": binding.waiver_registry_version, "waiver_registry_digest": binding.waiver_registry_digest, "evaluated_at": binding.evaluated_at, "expires_at": binding.expires_at, "dependency_evidence_references": list(binding.dependency_evidence_references), "waiver_references": [dict(item) for item in binding.waiver_references], "ptm_readiness": binding.to_dict()}
        if authority:
            commission["execution_authority"] = authority
        _write(self._path(COMMISSIONS, commission["commission_id"]), commission)
        self._state(grace_objective_id, "awaiting_engineering_acceptance", engineering_commission_id=commission["commission_id"])
        return commission

    def accept_commission(self, commission_id: str) -> dict[str, Any]:
        p = self._path(COMMISSIONS, commission_id); rec = _load(p)
        if rec["status"] == "accepted": return rec
        if rec["status"] != "proposed": raise ValueError("commission cannot be accepted from current state")
        rec["status"] = "accepted"; rec["accepted_at"] = utc_now(); _write_replace(p, rec); self._state(rec["grace_objective_id"], "engineering_in_progress", engineering_commission_id=commission_id); return rec

    def governed_commission_and_dispatch(self, grace_objective_id: str, helen_determination_id: str, *, grace_action_id: str, operations_decision_id: str, bounded_objective: str, acceptance_criteria: list[str], ptm_source_high_watermark: str, ptm_task_or_package_id: str, enabling_project_id: str | None, provider_id: str, provider_type: str, adapter_reference: str, execution_metadata: dict[str, Any] | None = None, idempotency_key: str | None = None) -> dict[str, Any]:
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
            execution_metadata=execution_metadata,
            provider_id=provider_id,
            adapter_reference=adapter_reference,
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
        authority = commission.get("execution_authority") or {}
        if provider_id in {"qwen.local.text", "codex.execution.cli"}:
            required = ("prompt_source", "allowed_read_paths", "allowed_write_paths", "expected_outputs", "prompt_source_digest")
            if not authority or any(not authority.get(key) for key in required):
                raise PermissionError("technical provider execution authority is incomplete")
            decision_dir = self.root / "runtime/operations/control/decisions"
            decision_found = False
            for decision_path in decision_dir.glob("*.json") if decision_dir.exists() else []:
                try:
                    if _load(decision_path).get("decision_id") == commission.get("operations_decision_id"):
                        decision_found = True; break
                except (OSError, ValueError):
                    continue
            if not decision_found:
                raise PermissionError("canonical Operations decision is required for technical provider execution")
        key = idempotency_key or f"{commission_id}:{provider_id}:authorization"
        technical_provider = provider_id in {"qwen.local.text", "codex.execution.cli"}
        stable_token = hashlib.sha256(key.encode("utf-8")).hexdigest()
        authorization_id = f"engauth-{stable_token[:12]}"
        dispatch_id = f"dispatch-{stable_token[12:24]}"
        auth_path = self._path(AUTHORIZATIONS, authorization_id)
        existing_auth = _load(auth_path) if auth_path.exists() else None
        if existing_auth and existing_auth.get("idempotency_key") != key:
            raise ValueError("conflicting authorization replay")
        auth = existing_auth or {"authorization_id": authorization_id, "engineering_commission_id": commission_id, "engineering_work_item_id": f"engwork-{commission_id}", "selected_capability_profile": det["worker_profile_id"], "provider_selection_id": f"engsel-{stable_token[:12]}", "provider_id": provider_id, "adapter_reference": adapter_reference, "operations_decision_id": commission.get("operations_decision_id"), "created_at": utc_now(), "idempotency_key": key}
        if existing_auth and existing_auth.get("dispatch_id"):
            existing_item = next((candidate for candidate in load_dispatch_queue(self.root) if candidate.dispatch_id == existing_auth["dispatch_id"]), None)
            if existing_item is not None:
                if existing_item.provider != provider_id or existing_item.provider_metadata.get("engineering_commission_id") != commission_id:
                    raise ValueError("conflicting Dispatch replay")
                return existing_auth, existing_item.to_dict()
        if existing_auth and not existing_auth.get("dispatch_id"):
            raise ValueError("incomplete existing authorization cannot be reused")
        authority = commission.get("execution_authority") or {}
        decision_id = f"opdec-{stable_token[:24]}"
        decision_reference = f"operations-control/{decision_id}"
        decision_path = self.root / "runtime/operations/control/decisions"
        existing_decision = next((candidate for candidate in decision_path.glob("*.json") if candidate.exists() and _load(candidate).get("decision_id") == decision_id), None) if decision_path.exists() else None
        if technical_provider and existing_decision is None:
            execution_decision = OperationsDecision(
                decision_id=decision_id,
                created_at=utc_now(),
                decided_by="Engineering",
                decision_type="authorize_dispatch",
                target_type="dispatch",
                target_id=dispatch_id,
                classification="Estate Internal",
                reason=f"Authorize bounded technical Dispatch {dispatch_id} from accepted Engineering commission {commission_id}.",
                priority="normal",
                requires_boundary_review=False,
                requires_steward_attention=False,
                summary_safe=True,
                metadata={"parent_operations_decision_id": commission["operations_decision_id"]},
                decision_state="authorized_for_dispatch",
                technical_execution=True,
                grace_objective_id=commission["grace_objective_id"],
                grace_action_id=commission["grace_action_id"],
                helen_determination_id=det["determination_id"],
                ptm_readiness=binding.to_dict(),
                engineering_commission_id=commission_id,
                engineering_authorization_id=authorization_id,
                dispatch_id=dispatch_id,
                selected_provider_id=provider_id,
                selected_adapter_reference=adapter_reference,
                authorization_reference=f"runtime/grace_helen_engineering/engineering_authorizations/{authorization_id}.json",
                decision_reference=decision_reference,
                prompt_source=authority.get("prompt_source"),
                prompt_source_digest=authority.get("prompt_source_digest"),
                allowed_read_paths=list(authority.get("allowed_read_paths") or []),
                allowed_write_paths=list(authority.get("allowed_write_paths") or []),
                expected_outputs=list(authority.get("expected_outputs") or []),
                provider_extension=authority.get("provider_extension"),
                authorized_at=utc_now(),
                expires_at=binding.expires_at,
                idempotency_key=key,
                parent_operations_decision_id=commission["operations_decision_id"],
            )
            OperationsControlRuntime(self.root).record_decision(execution_decision)
        elif technical_provider:
            execution_decision = OperationsDecision.from_dict(_load(existing_decision))
            if not execution_decision.technical_execution or execution_decision.engineering_commission_id != commission_id or execution_decision.dispatch_id != dispatch_id:
                raise ValueError("conflicting Operations decision replay")
        technical_metadata = {"technical_execution": True, "grace_objective_id": commission["grace_objective_id"], "grace_action_id": commission["grace_action_id"], "operations_decision_id": commission["operations_decision_id"], "engineering_commission_id": commission_id, "engineering_authorization_id": auth["authorization_id"], "helen_determination_id": det["determination_id"], "capability_inquiry_reference": det.get("capability_request_id"), "capability_disposition": det["disposition"], "provider_id": provider_id, "provider_type": provider_type, "adapter_reference": adapter_reference, "validation_required": True, "institutional_acceptance_state": "not_granted", "ptm_readiness": binding.to_dict(), "ptm_revalidated_at": utc_now(), "ptm_revalidation_result": "passed", "authorization_reference": f"runtime/grace_helen_engineering/engineering_authorizations/{auth['authorization_id']}.json", "decision_reference": decision_reference if technical_provider else f"operations-control/{commission['operations_decision_id']}"}
        if authority:
            technical_metadata.update({"prompt_source_digest": authority.get("prompt_source_digest"), "prompt_source_type": authority.get("prompt_source_type"), "execution_authority": authority})
        if technical_provider and authority.get("provider_extension"):
            technical_metadata["provider_extension"] = dict(authority["provider_extension"])
        if existing_auth:
            for field_name, expected in (("engineering_commission_id", commission_id), ("provider_id", provider_id), ("adapter_reference", adapter_reference), ("operations_decision_id", commission["operations_decision_id"]), ("execution_authority", authority)):
                if auth.get(field_name) != expected:
                    raise ValueError("conflicting authorization replay")
        request = DispatchRequest(dispatch_id=dispatch_id, work_package_id=commission["grace_objective_id"], title=commission["bounded_objective"], requested_by="Engineering", assigned_worker=det["worker_profile_id"], provider=provider_id, profile_label=det["worker_profile_id"], classification="Estate Internal", priority="Normal", state="Ready", prompt_source=authority.get("prompt_source"), allowed_read_paths=list(authority.get("allowed_read_paths") or []), allowed_write_paths=list(authority.get("allowed_write_paths") or []), expected_outputs=list(authority.get("expected_outputs") or []), allowed_providers=[provider_id], provider_metadata=technical_metadata)
        auth.update({"dispatch_id": request.dispatch_id, "dispatch_record_path": "runtime/execution_dispatch/queue.json", "ptm_readiness": binding.to_dict(), "ptm_revalidated_at": request.provider_metadata["ptm_revalidated_at"], "ptm_revalidation_result": "passed", "grace_objective_id": commission["grace_objective_id"], "grace_action_id": commission["grace_action_id"], "helen_determination_id": det["determination_id"], "provider_type": provider_type, "execution_authority": authority, "authorization_reference": technical_metadata["authorization_reference"], "decision_reference": technical_metadata["decision_reference"]})
        if technical_provider:
            auth.update({"schema_version": "estate.engineering.authorization.v1", "engineering_authorization_id": auth["authorization_id"], "prompt_source": authority.get("prompt_source"), "prompt_source_type": authority.get("prompt_source_type"), "prompt_source_digest": authority.get("prompt_source_digest"), "allowed_read_paths": list(authority.get("allowed_read_paths") or []), "allowed_write_paths": list(authority.get("allowed_write_paths") or []), "expected_outputs": list(authority.get("expected_outputs") or []), "provider_extension": dict(authority.get("provider_extension") or {}), "authorization_state": "authorized_for_dispatch", "authorized_at": request.provider_metadata["ptm_revalidated_at"], "expires_at": binding.expires_at, "institutional_acceptance_state": "not_granted", "idempotency_key": key, "operations_decision_id": commission["operations_decision_id"]})
        auth["record_digest"] = hashlib.sha256(json.dumps({key: value for key, value in auth.items() if key != "record_digest"}, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        if technical_provider:
            require_valid(auth, "estate.engineering.authorization.v1", self.root)
        technical_metadata["authorization_record_digest"] = auth["record_digest"]
        if not existing_auth:
            _durable_write(auth_path, auth)
        try:
            item = enqueue_dispatch_request(request, self.root)
        except ValueError as exc:
            existing_item = next((candidate for candidate in load_dispatch_queue(self.root) if candidate.dispatch_id == request.dispatch_id), None)
            if existing_item is None or existing_item.to_dict() != request.to_dict():
                raise ValueError("conflicting Dispatch replay") from exc
            item = existing_item
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
