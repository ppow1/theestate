"""Governed capability discovery, enablement, registration, and resumption.

This module composes existing Grace, Helen, PTM, provider-catalog, and Dispatch
records.  It does not execute providers and it does not create a second queue,
registry, scheduler, or acceptance authority.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from estate.core.grace_operations_runtime import GraceOperationsRuntime
from estate.core.paths import ESTATE_ROOT

ROOT = Path("runtime/grace_helen_engineering/capability_enablement")
KINDS = {
    "inquiries", "assessments", "gaps", "worker_specifications", "selections",
    "creation_proposals", "dependencies", "registrations", "reevaluations",
    "resumptions",
}
DISPOSITIONS = {
    "available", "unavailable", "uncertain", "declared_but_unqualified",
    "qualified_but_unhealthy", "healthy_but_unavailable", "available_but_unauthorized",
    "stale_evidence", "conflicting_evidence",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _root(root: str | Path | None) -> Path:
    return Path(root) if root is not None else ESTATE_ROOT


def _required(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} is required")
    return value


def _list(value: Any, name: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        raise ValueError(f"{name} must be a list of non-empty strings")
    return list(value)


def _write(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if existing != payload:
            raise ValueError(f"immutable record conflict at {path}")
    else:
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def _find(root: Path, kind: str, record_id: str) -> dict[str, Any]:
    path = root / ROOT / kind / f"{record_id}.json"
    if not path.exists():
        raise ValueError(f"{kind} record not found: {record_id}")
    return json.loads(path.read_text(encoding="utf-8"))


@dataclass(frozen=True)
class CapabilityEvidence:
    capability_id: str
    worker_id: str | None = None
    provider_id: str | None = None
    adapter_id: str | None = None
    declaration: str = "unknown"
    qualification: str = "unknown"
    health: str = "unknown"
    availability: str = "unknown"
    authorization: str = "unknown"
    evidence_references: list[str] = field(default_factory=list)
    observed_at: str | None = None
    expires_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class CapabilityEnablementLifecycle:
    """Append-only lifecycle records with explicit authority boundaries."""

    def __init__(self, root: str | Path | None = None) -> None:
        self.root = _root(root)

    def _record(self, kind: str, prefix: str, payload: dict[str, Any]) -> dict[str, Any]:
        if kind not in KINDS:
            raise ValueError(f"unknown capability enablement record kind: {kind}")
        record = {"schema_version": f"estate.{kind}.v1", "created_at": utc_now(), **payload}
        record.setdefault("record_id", f"{prefix}-{uuid4().hex[:12]}")
        return _write(self.root / ROOT / kind / f"{record['record_id']}.json", record)

    def create_inquiry(self, *, objective_id: str, campaign_id: str, package_id: str,
                       requested_outcome: str, required_capabilities: list[str],
                       constraints: list[str] | None = None,
                       freshness_requirements: dict[str, Any] | None = None,
                       authorization_context: dict[str, Any] | None = None,
                       checkpoint: str | None = None) -> dict[str, Any]:
        _required(objective_id, "objective_id"); _required(campaign_id, "campaign_id")
        _required(package_id, "package_id"); _required(requested_outcome, "requested_outcome")
        capabilities = _list(required_capabilities, "required_capabilities")
        if not capabilities:
            raise ValueError("required_capabilities must not be empty")
        record = self._record("inquiries", "capinq", {
            "objective_id": objective_id, "campaign_id": campaign_id, "package_id": package_id,
            "requested_outcome": requested_outcome, "required_capabilities": sorted(set(capabilities)),
            "constraints": _list(constraints, "constraints"),
            "freshness_requirements": freshness_requirements or {},
            "authorization_context": authorization_context or {},
            "checkpoint": checkpoint, "status": "assessment_pending", "owner": "Grace",
        })
        GraceOperationsRuntime(self.root).record_objective_transition(
            objective_id, "awaiting_capability_verification", capability_inquiry_id=record["record_id"])
        return record

    def assess(self, inquiry_id: str, evidence: list[CapabilityEvidence | dict[str, Any]]) -> dict[str, Any]:
        inquiry = _find(self.root, "inquiries", inquiry_id)
        normalized: list[dict[str, Any]] = []
        for item in evidence:
            fact = item if isinstance(item, CapabilityEvidence) else CapabilityEvidence(**item)
            if fact.capability_id not in inquiry["required_capabilities"]:
                raise ValueError(f"assessment contains unrequested capability: {fact.capability_id}")
            normalized.append(fact.to_dict())
        by_capability = {item["capability_id"]: item for item in normalized}
        dispositions: dict[str, str] = {}
        for capability in inquiry["required_capabilities"]:
            item = by_capability.get(capability)
            if item is None:
                dispositions[capability] = "uncertain"
                continue
            if item["declaration"] == "conflicting" or item["qualification"] == "conflicting":
                dispositions[capability] = "conflicting_evidence"
            elif item["declaration"] not in {"declared", "qualified"}:
                dispositions[capability] = "uncertain"
            elif item["qualification"] != "qualified":
                dispositions[capability] = "declared_but_unqualified"
            elif item["health"] != "healthy":
                dispositions[capability] = "qualified_but_unhealthy"
            elif item["availability"] != "available":
                dispositions[capability] = "healthy_but_unavailable"
            elif item["authorization"] != "authorized":
                dispositions[capability] = "available_but_unauthorized"
            elif not item.get("provider_id") or not item.get("adapter_id"):
                dispositions[capability] = "conflicting_evidence"
            elif item.get("expires_at") and item["expires_at"] < utc_now():
                dispositions[capability] = "stale_evidence"
            else:
                dispositions[capability] = "available"
        overall = "available" if all(value == "available" for value in dispositions.values()) else "gap_found"
        assessment = self._record("assessments", "capassess", {
            "inquiry_id": inquiry_id, "objective_id": inquiry["objective_id"],
            "assessed_by": "Helen", "observed_at": utc_now(), "evidence": normalized,
            "capability_dispositions": dispositions, "overall_disposition": overall,
            "status": "complete", "authority_boundary": "assessment_only_no_execution",
        })
        if overall != "available":
            for capability, disposition in dispositions.items():
                if disposition != "available":
                    self.create_gap(inquiry_id=inquiry_id, assessment_id=assessment["record_id"],
                                    capability_id=capability, disposition=disposition,
                                    supporting_evidence=by_capability.get(capability, {}).get("evidence_references", []))
            GraceOperationsRuntime(self.root).record_objective_transition(
                inquiry["objective_id"], "blocked_pending_capability", capability_assessment_id=assessment["record_id"])
        else:
            GraceOperationsRuntime(self.root).record_objective_transition(
                inquiry["objective_id"], "awaiting_engineering_acceptance", capability_assessment_id=assessment["record_id"])
        return assessment

    def select_provider(self, assessment_id: str, capability_id: str) -> dict[str, Any]:
        """Engineering selection from Helen-qualified evidence and catalog truth."""
        from estate.core.provider_catalog import load_provider_catalog

        assessment = _find(self.root, "assessments", assessment_id)
        if assessment["capability_dispositions"].get(capability_id) != "available":
            raise PermissionError("provider selection requires an available capability assessment")
        fact = next(item for item in assessment["evidence"] if item["capability_id"] == capability_id)
        provider_id = _required(fact.get("provider_id"), "provider_id")
        adapter_id = _required(fact.get("adapter_id"), "adapter_id")
        provider = load_provider_catalog(self.root / "config" / "providers" / "catalog.json").get_provider(provider_id)
        if provider.status not in {"implemented", "operationally_validated", "institutionalized"}:
            raise PermissionError(f"provider '{provider_id}' is not registered for selection")
        return self._record("selections", "capselect", {
            "assessment_id": assessment_id, "objective_id": assessment["objective_id"],
            "capability_id": capability_id, "provider_id": provider_id, "adapter_id": adapter_id,
            "selection_rationale": "Helen evidence is fresh and affirmative; canonical catalog descriptor is registered.",
            "selected_by": "Engineering", "status": "selected", "authorization_required": True,
        })

    def create_gap(self, *, inquiry_id: str, assessment_id: str, capability_id: str,
                    disposition: str, supporting_evidence: list[str] | None = None,
                    urgency: str = "normal", proposed_next_action: str = "define_worker_specification") -> dict[str, Any]:
        if disposition not in DISPOSITIONS or disposition == "available":
            raise ValueError("invalid capability-gap disposition")
        inquiry = _find(self.root, "inquiries", inquiry_id)
        return self._record("gaps", "capgap", {
            "inquiry_id": inquiry_id, "assessment_id": assessment_id, "objective_id": inquiry["objective_id"],
            "capability_id": capability_id, "disposition": disposition,
            "supporting_evidence": _list(supporting_evidence, "supporting_evidence"),
            "business_need": inquiry["requested_outcome"], "urgency": urgency,
            "proposed_next_action": proposed_next_action, "status": "open", "owner": "Helen",
        })

    def create_worker_specification(self, *, gap_id: str, role: str, required_capabilities: list[str],
                                    qualifications: list[str], technical_expectations: list[str],
                                    authorization_scope: list[str], health_requirements: list[str],
                                    input_contract: dict[str, Any], output_contract: dict[str, Any],
                                    artifact_contract: dict[str, Any], receipt_contract: dict[str, Any],
                                    timeout_seconds: int, cancellation: str, retry_semantics: str,
                                    validation_requirements: list[str], sandbox_boundaries: list[str],
                                    consultation_id: str | None = None) -> dict[str, Any]:
        gap = _find(self.root, "gaps", gap_id)
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        return self._record("worker_specifications", "workerspec", {
            "gap_id": gap_id, "objective_id": gap["objective_id"], "role": _required(role, "role"),
            "required_capabilities": _list(required_capabilities, "required_capabilities"),
            "qualifications": _list(qualifications, "qualifications"),
            "technical_expectations": _list(technical_expectations, "technical_expectations"),
            "authorization_scope": _list(authorization_scope, "authorization_scope"),
            "health_requirements": _list(health_requirements, "health_requirements"),
            "input_contract": input_contract, "output_contract": output_contract,
            "artifact_contract": artifact_contract, "receipt_contract": receipt_contract,
            "timeout_seconds": timeout_seconds, "cancellation": cancellation,
            "retry_semantics": retry_semantics, "validation_requirements": _list(validation_requirements, "validation_requirements"),
            "sandbox_boundaries": _list(sandbox_boundaries, "sandbox_boundaries"),
            "consultation_id": consultation_id, "produced_by": "Engineering_advisory_consultation",
            "status": "proposed", "implementation_authorized": False,
        })

    def create_capability_creation_proposal(self, *, gap_id: str, worker_specification_id: str,
                                            proposed_by: str = "Helen", authority_context: dict[str, Any] | None = None) -> dict[str, Any]:
        gap = _find(self.root, "gaps", gap_id)
        return self._record("creation_proposals", "capprop", {
            "gap_id": gap_id, "objective_id": gap["objective_id"], "worker_specification_id": worker_specification_id,
            "proposed_by": proposed_by, "authority_context": authority_context or {},
            "status": "proposed", "implementation_authorized": False, "execution_authorized": False,
        })

    def link_enabling_project(self, *, proposal_id: str, enabling_project_id: str, original_objective_id: str,
                              dependency_type: str = "capability_enablement",
                              canonical_ptm_dependency_id: str | None = None) -> dict[str, Any]:
        proposal = _find(self.root, "creation_proposals", proposal_id)
        if proposal["objective_id"] != original_objective_id:
            raise ValueError("enabling proposal does not belong to original objective")
        dependency = self._record("dependencies", "capdep", {
            "proposal_id": proposal_id, "original_objective_id": original_objective_id,
            "enabling_project_id": _required(enabling_project_id, "enabling_project_id"),
            "dependency_type": dependency_type, "status": "waiting_on_enabling_project",
            "canonical_ptm_dependency_id": canonical_ptm_dependency_id,
            "canonical_dependency_confirmed": bool(canonical_ptm_dependency_id),
            "scheduler_owner": "PTM_orchestrator", "resumption_owner": "Grace",
        })
        GraceOperationsRuntime(self.root).record_objective_transition(
            original_objective_id, "blocked_pending_capability", enabling_project_id=enabling_project_id,
            capability_dependency_id=dependency["record_id"])
        return dependency

    def record_registration(self, *, dependency_id: str, provider_id: str, adapter_id: str,
                            adapter_version: str, capability_claims: list[str], qualification_evidence: list[str],
                            health_evidence: list[str], authorization_evidence: list[str],
                            receipt_contract: dict[str, Any], artifact_contract: dict[str, Any],
                            status: str = "registered") -> dict[str, Any]:
        dependency = _find(self.root, "dependencies", dependency_id)
        if status not in {"registered", "failed", "blocked"}:
            raise ValueError("invalid registration status")
        registration = self._record("registrations", "capreg", {
            "dependency_id": dependency_id, "provider_id": provider_id, "adapter_id": adapter_id,
            "adapter_version": adapter_version, "capability_claims": _list(capability_claims, "capability_claims"),
            "qualification_evidence": _list(qualification_evidence, "qualification_evidence"),
            "health_evidence": _list(health_evidence, "health_evidence"),
            "authorization_evidence": _list(authorization_evidence, "authorization_evidence"),
            "receipt_contract": receipt_contract, "artifact_contract": artifact_contract,
            "status": status, "registered_by": "Engineering", "institutional_acceptance": False,
        })
        return registration

    def reevaluate(self, *, dependency_id: str, registration_id: str, evidence: list[CapabilityEvidence | dict[str, Any]],
                   canonical_dependency_evidence: list[str] | None = None) -> dict[str, Any]:
        dependency = _find(self.root, "dependencies", dependency_id)
        registration = _find(self.root, "registrations", registration_id)
        if registration["status"] != "registered":
            raise ValueError("only registered capability may be re-evaluated")
        dispositions = []
        for item in evidence:
            fact = item if isinstance(item, CapabilityEvidence) else CapabilityEvidence(**item)
            dispositions.append({**fact.to_dict(), "available": all([
                fact.qualification == "qualified", fact.health == "healthy",
                fact.availability == "available", fact.authorization == "authorized",
            ])})
        dependency_evidence = _list(canonical_dependency_evidence, "canonical_dependency_evidence")
        dependency_confirmed = bool(dependency.get("canonical_dependency_confirmed")) and bool(dependency_evidence)
        passed = dependency_confirmed and bool(dispositions) and all(item["available"] for item in dispositions)
        result = self._record("reevaluations", "capreval", {
            "dependency_id": dependency_id, "registration_id": registration_id,
            "original_objective_id": dependency["original_objective_id"], "evidence": dispositions,
            "disposition": "capability_available" if passed else ("dependency_not_confirmed" if not dependency_confirmed else "capability_gap_remains"),
            "canonical_dependency_evidence": dependency_evidence,
            "status": "passed" if passed else "blocked", "assessed_by": "Helen", "observed_at": utc_now(),
        })
        if passed:
            self._record("resumptions", "graceresume", {
                "dependency_id": dependency_id, "reevaluation_id": result["record_id"],
                "original_objective_id": dependency["original_objective_id"], "status": "resumable",
                "resumed_by": "Grace", "institutional_acceptance": False,
            })
            GraceOperationsRuntime(self.root).record_objective_transition(
                dependency["original_objective_id"], "original_project_resumed",
                capability_reevaluation_id=result["record_id"], resumed_from_dependency=dependency_id)
        else:
            GraceOperationsRuntime(self.root).record_objective_transition(
                dependency["original_objective_id"], "blocked_pending_capability",
                capability_reevaluation_id=result["record_id"])
        return result
