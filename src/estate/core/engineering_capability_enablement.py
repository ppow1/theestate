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
from typing import Any, Callable, Mapping
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
CanonicalDependencyResolver = Callable[[str], Mapping[str, Any] | None]


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

    def __init__(self, root: str | Path | None = None,
                 canonical_dependency_resolver: CanonicalDependencyResolver | None = None) -> None:
        self.root = _root(root)
        if canonical_dependency_resolver is None:
            from estate.core.ptm_readiness_integration import PtmCapabilityDependencyResolver
            canonical_dependency_resolver = PtmCapabilityDependencyResolver(self.root)
        self.canonical_dependency_resolver = canonical_dependency_resolver

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
        dependency_evidence = _list(canonical_dependency_evidence, "canonical_dependency_evidence")
        reasons: list[str] = []
        proposal = _find(self.root, "creation_proposals", dependency["proposal_id"])
        gap = _find(self.root, "gaps", proposal["gap_id"])
        inquiry = _find(self.root, "inquiries", gap["inquiry_id"])
        required = sorted(set(inquiry.get("required_capabilities") or []))
        claims = _list(registration.get("capability_claims"), "registration.capability_claims")
        if registration.get("dependency_id") != dependency_id:
            reasons.append("registration_dependency_mismatch")
        if registration.get("status") != "registered":
            reasons.append("registration_not_registered")
        if not registration.get("provider_id"):
            reasons.append("registration_provider_missing")
        if not registration.get("adapter_id"):
            reasons.append("registration_adapter_missing")
        if not claims:
            reasons.append("registration_capability_claims_missing")
        if proposal.get("objective_id") != dependency.get("original_objective_id"):
            reasons.append("proposal_objective_mismatch")
        if gap.get("objective_id") != dependency.get("original_objective_id"):
            reasons.append("gap_objective_mismatch")
        if gap.get("inquiry_id") != inquiry.get("record_id"):
            reasons.append("gap_inquiry_mismatch")
        if inquiry.get("objective_id") != dependency.get("original_objective_id"):
            reasons.append("inquiry_objective_mismatch")
        if not required or gap.get("capability_id") not in required:
            reasons.append("required_capability_chain_invalid")
        missing_claims = sorted(set(required) - set(claims))
        if missing_claims:
            reasons.append("registration_missing_required_capability")

        normalized: list[dict[str, Any]] = []
        for item in evidence:
            fact = item if isinstance(item, CapabilityEvidence) else CapabilityEvidence(**item)
            normalized.append(fact.to_dict())
        evidence_capabilities = [item["capability_id"] for item in normalized]
        duplicates = sorted({capability for capability in evidence_capabilities if evidence_capabilities.count(capability) > 1})
        if duplicates:
            reasons.append("duplicate_capability_evidence")
        unexpected = sorted(set(evidence_capabilities) - set(required))
        if unexpected:
            reasons.append("unrelated_capability_evidence")
        missing_evidence = sorted(set(required) - set(evidence_capabilities))
        if missing_evidence:
            reasons.append("missing_required_capability_evidence")

        now = datetime.now(timezone.utc)
        dispositions: list[dict[str, Any]] = []
        for fact in normalized:
            available = True
            if fact["capability_id"] not in claims:
                reasons.append("evidence_capability_not_claimed")
                available = False
            if fact.get("provider_id") != registration.get("provider_id"):
                reasons.append("evidence_provider_mismatch")
                available = False
            if fact.get("adapter_id") != registration.get("adapter_id"):
                reasons.append("evidence_adapter_mismatch")
                available = False
            if fact.get("declaration") not in {"declared", "qualified"}:
                reasons.append("evidence_declaration_not_affirmative")
                available = False
            if fact.get("qualification") != "qualified":
                reasons.append("evidence_not_qualified")
                available = False
            if fact.get("health") != "healthy":
                reasons.append("evidence_not_healthy")
                available = False
            if fact.get("availability") != "available":
                reasons.append("evidence_not_available")
                available = False
            if fact.get("authorization") != "authorized":
                reasons.append("evidence_not_authorized")
                available = False
            if not fact.get("observed_at") or not fact.get("expires_at") or not fact.get("evidence_references"):
                reasons.append("evidence_freshness_or_reference_missing")
                available = False
            else:
                try:
                    observed_at = datetime.fromisoformat(fact["observed_at"].replace("Z", "+00:00"))
                    expires_at = datetime.fromisoformat(fact["expires_at"].replace("Z", "+00:00"))
                    if observed_at > now or expires_at <= now or expires_at <= observed_at:
                        reasons.append("evidence_stale_or_invalid_window")
                        available = False
                except (TypeError, ValueError):
                    reasons.append("evidence_timestamp_invalid")
                    available = False
            if any(fact.get(field) == "conflicting" for field in ("declaration", "qualification", "health", "availability", "authorization")):
                reasons.append("conflicting_capability_evidence")
                available = False
            dispositions.append({**fact, "available": available})

        canonical = None
        if self.canonical_dependency_resolver is None:
            reasons.append("canonical_dependency_resolver_unavailable")
        elif not dependency.get("canonical_ptm_dependency_id"):
            reasons.append("canonical_dependency_id_missing")
        else:
            canonical = self.canonical_dependency_resolver(dependency["canonical_ptm_dependency_id"])
            if not canonical:
                reasons.append("canonical_dependency_unresolved")
            else:
                if canonical.get("record_id") != dependency.get("canonical_ptm_dependency_id"):
                    reasons.append("canonical_dependency_identity_mismatch")
                if canonical.get("original_objective_id") != dependency.get("original_objective_id"):
                    reasons.append("canonical_dependency_objective_mismatch")
                if canonical.get("enabling_project_id") != dependency.get("enabling_project_id"):
                    reasons.append("canonical_dependency_project_mismatch")
                if canonical.get("status") not in {"satisfied", "completed"}:
                    reasons.append("canonical_dependency_not_satisfied")
                if not canonical.get("evidence_references"):
                    reasons.append("canonical_dependency_evidence_missing")
                try:
                    canonical_observed = datetime.fromisoformat(str(canonical["observed_at"]).replace("Z", "+00:00"))
                    canonical_expires = datetime.fromisoformat(str(canonical["expires_at"]).replace("Z", "+00:00"))
                    if canonical_observed > now or canonical_expires <= now or canonical_expires <= canonical_observed:
                        reasons.append("canonical_dependency_evidence_stale")
                except (KeyError, TypeError, ValueError):
                    reasons.append("canonical_dependency_freshness_missing")
                if any(reference not in canonical.get("evidence_references", []) for reference in dependency_evidence):
                    reasons.append("canonical_dependency_evidence_reference_unverified")
        if not dependency_evidence:
            reasons.append("canonical_dependency_evidence_reference_missing")

        reasons = sorted(set(reasons))
        passed = not reasons and bool(required) and len(dispositions) == len(required) and all(item["available"] for item in dispositions)
        result = self._record("reevaluations", "capreval", {
            "dependency_id": dependency_id, "registration_id": registration_id,
            "original_objective_id": dependency["original_objective_id"], "required_capabilities": required,
            "evidence": dispositions, "blocking_reasons": reasons,
            "disposition": "capability_available" if passed else "blocked",
            "blocking_reason": reasons[0] if reasons else None,
            "canonical_dependency_evidence": dependency_evidence, "canonical_dependency_record": dict(canonical) if canonical else None,
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
