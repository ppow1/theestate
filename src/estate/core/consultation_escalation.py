"""Bounded terminal handoff from autonomous reasoning to Grace/Steward."""

from __future__ import annotations

from typing import Any

from estate.core.consultation_store import ConsultationRecord, ConsultationStore


MAX_TEXT = 1200
MAX_ITEMS = 8


def _text(value: Any, limit: int = MAX_TEXT) -> str:
    if value is None:
        return ""
    if isinstance(value, dict):
        value = value.get("content") or value.get("reasoning") or str(value)
    return str(value)[:limit]


def _decision(record: ConsultationRecord) -> dict[str, Any]:
    response = record.response if isinstance(record.response, dict) else {}
    decision = response.get("structured_decision")
    return decision if isinstance(decision, dict) else {}


def build_escalation_package(
    store: ConsultationStore,
    logical_consultation_id: str,
    *,
    decision_needed: str | None = None,
) -> dict[str, Any]:
    """Build and persist a compact, truthful Steward package.

    This operation is idempotent in content and never creates a request,
    continuation, or provider attempt.
    """
    current = store.get(logical_consultation_id)
    root = store.get_root(current.root_logical_id)
    turns = store.get_turn_range(root.root_logical_id)
    summary = store.compact_summary(root.root_logical_id)["summary"][:4000]

    recommendations = []
    executions = []
    acquisitions = []
    for turn in turns:
        if turn.recommendation:
            recommendations.append({
                "turn": turn.logical_consultation_id,
                "recommendation": _text(turn.recommendation),
            })
        for execution in store.execution_requests(turn.logical_consultation_id):
            attempts = store.execution_attempts(execution.execution_request_id)
            item = {
                "turn": turn.logical_consultation_id,
                "execution_request_id": execution.execution_request_id,
                "purpose": (execution.result_json or {}).get("purpose") if isinstance(execution.result_json, dict) else None,
                "capability": execution.required_capability,
                "provider": execution.provider_id,
                "status": execution.status,
                "attempts": [{"id": a.execution_attempt_id, "status": a.status, "provider": a.provider_id} for a in attempts[:3]],
                "result_reference": execution.result_reference,
            }
            executions.append(item)
            if execution.required_capability in {
                "repository_read", "filesystem_read", "test_inspection",
                "configuration_inspection", "software_engineering_readonly",
            }:
                acquisitions.append(item)

    latest_decision = _decision(current)
    evidence_request = latest_decision.get("evidence_request")
    if not isinstance(evidence_request, dict):
        evidence_request = {}
    unknowns = {
        "current_question": _text(current.question),
        "latest_reasoning": _text(current.response),
        "remaining_evidence_request": {
            key: evidence_request.get(key)
            for key in ("objective", "evidence_type", "target", "required_capability", "evidence_requirements", "validation_criteria")
            if evidence_request.get(key) is not None
        },
        "observed_result": current.observed_result,
    }
    package = {
        "type": "STEWARD_ESCALATION",
        "status": "STEWARD_DECISION_REQUIRED",
        "root_consultation_id": root.root_logical_id,
        "current_turn": current.logical_consultation_id,
        "objective": _text(root.objective),
        "current_understanding": summary,
        "recommendations_considered": recommendations[-MAX_ITEMS:],
        "execution": executions[-MAX_ITEMS:],
        "evidence_acquisitions": acquisitions[-3:],
        "acquisition_count": len(acquisitions),
        "what_remains_unknown": unknowns,
        "why_no_autonomous_conclusion": "The permitted autonomous evidence budget is exhausted and ChatGPT still cannot reach a defensible conclusion.",
        "decision_or_evidence_needed": decision_needed or "Steward direction on the remaining bounded evidence/decision, or authorization to reframe this objective as a new consultation.",
        "ptm": {"project_id": root.ptm_project_id, "work_item_id": root.ptm_work_item_id},
        "durable_references": {
            "consultation_root": root.root_logical_id,
            "current_turn": current.logical_consultation_id,
        },
        "reframe": {
            "status": "PROPOSE_ONLY",
            "predecessor_root": root.root_logical_id,
            "summary": "A materially different objective may be opened as a new root after explicit authority; no root was created by this escalation.",
        },
    }
    store.set_escalation_package(current.logical_consultation_id, package)
    return package


def instrument_escalation(
    store: ConsultationStore,
    logical_consultation_id: str,
    *,
    decision_needed: str | None = None,
) -> dict[str, Any]:
    """Create the immutable decision-time learning snapshot for an escalation."""
    current = store.get(logical_consultation_id)
    existing = [item for item in store.escalations() if item.current_logical_id == logical_consultation_id]
    if existing:
        snapshot = dict(existing[0].snapshot)
        snapshot["escalation_id"] = existing[0].escalation_id
        return snapshot

    package = build_escalation_package(store, logical_consultation_id, decision_needed=decision_needed)
    root = store.get_root(current.root_logical_id)
    turns = store.get_turn_range(root.root_logical_id)
    executions = [e for turn in turns for e in store.execution_requests(turn.logical_consultation_id)]
    acquisition_count = len([e for e in executions if e.required_capability in {
        "repository_read", "filesystem_read", "test_inspection",
        "configuration_inspection", "software_engineering_readonly",
    }])
    execution_refs = [e.execution_request_id for e in executions]
    latest = current.response if isinstance(current.response, dict) else {}
    latest_decision = latest.get("structured_decision", {}) if isinstance(latest, dict) else {}
    evidence_request = latest_decision.get("evidence_request", {}) if isinstance(latest_decision, dict) else {}
    unknown_statement = _text(current.question) or _text(evidence_request.get("objective")) or "The remaining engineering conclusion is not defensible from the bounded evidence gathered."

    snapshot = {
        **package,
        "snapshot_version": 1,
        "overall_confidence": 0.93,
        "overall_confidence_basis": "Operational confidence in the escalation state, based on authoritative structured responses, the fixed acquisition count, and durable execution records; not confidence in an engineering conclusion.",
        "known_facts": [
            {"statement": f"Exactly {acquisition_count} bounded provider evidence acquisitions are recorded for this root.", "confidence": 0.99, "confidence_class": "FACT", "basis": "authoritative SQLite execution-request records", "evidence_references": execution_refs[-3:], "classification": "observed"},
            {"statement": "The autonomous evidence budget is exhausted.", "confidence": 0.99, "confidence_class": "FACT", "basis": "structured MORE_REASONING_REQUIRED response and Estate budget guard", "evidence_references": [current.logical_consultation_id], "classification": "observed"},
            {"statement": "No defensible final conclusion is currently available.", "confidence": 0.96, "confidence_class": "FACT", "basis": "authoritative latest structured reasoning response", "evidence_references": [current.ec8_request_id] if current.ec8_request_id else [], "classification": "observed"},
        ],
        "working_interpretations": [
            {"statement": "Further autonomous evidence gathering should stop at this boundary.", "confidence": 0.97, "confidence_class": "CONCLUSION", "supporting_evidence": ["fixed acquisition budget", "repeated bounded evidence requests"], "conflicting_evidence": [], "reason_for_uncertainty": "The unresolved engineering question may change if the Steward supplies authority or new facts."},
        ],
        "unknowns": [
            {"statement": unknown_statement, "impact": "high", "why_it_matters": "It prevents a responsible final recommendation or closure.", "evidence_attempts": acquisition_count, "unresolved_confidence": 0.97, "what_would_reduce_uncertainty": [evidence_request.get("objective") or "Steward-supplied evidence or policy direction"]},
        ],
        "options": [
            {"option_id": "steward_direction", "description": "Provide the missing authority or bounded evidence needed to resume the same consultation.", "expected_outcome": "The Estate can resume without inventing evidence.", "action_confidence": None, "action_confidence_basis": "No engineering outcome is asserted; this is a decision-boundary option.", "risk_level": "low", "reversibility": "reversible", "authority_required": "Steward", "known_advantages": ["preserves lineage"], "known_disadvantages": ["requires Steward time"], "key_uncertainty": unknown_statement, "evidence_references": []},
            {"option_id": "reframe", "description": "Explicitly reframe the materially different question as a new consultation.", "expected_outcome": "A new root can start with this handoff as predecessor context.", "action_confidence": None, "action_confidence_basis": "No engineering outcome is asserted; creation requires explicit authority.", "risk_level": "medium", "reversibility": "reversible", "authority_required": "Steward", "known_advantages": ["avoids misleading context"], "known_disadvantages": ["starts a new lineage root"], "key_uncertainty": "Whether the objective is materially different.", "evidence_references": []},
        ],
        "system_recommendation": None,
        "recommendation_confidence": None,
        "recommendation_confidence_basis": "No engineering recommendation is asserted because the evidence is insufficient.",
        "what_would_increase_confidence": [evidence_request.get("objective") or "Steward decision or bounded evidence addressing the remaining unknown"],
        "decision_requested": decision_needed or package["decision_or_evidence_needed"],
    }
    record = store.create_escalation_record(current.logical_consultation_id, snapshot)
    snapshot["escalation_id"] = record.escalation_id
    package_with_id = {**package, "escalation_id": record.escalation_id, "instrumented_snapshot": snapshot}
    store.set_escalation_package(current.logical_consultation_id, package_with_id)
    return snapshot


def grace_decision_packet(store: ConsultationStore, escalation_id: str) -> dict[str, Any]:
    record = store.escalation(escalation_id)
    snapshot = record.snapshot
    packet = {key: snapshot.get(key) for key in (
        "escalation_id", "root_consultation_id", "current_turn", "status",
        "objective", "overall_confidence", "known_facts", "working_interpretations",
        "unknowns", "options", "system_recommendation", "recommendation_confidence",
        "what_would_increase_confidence", "decision_requested",
    )}
    packet["escalation_id"] = record.escalation_id
    return packet


def propose_reframe(store: ConsultationStore, logical_consultation_id: str) -> dict[str, Any]:
    current = store.get(logical_consultation_id)
    return {
        "status": "REFRAME_AS_NEW_CONSULTATION",
        "predecessor_root": current.root_logical_id,
        "handoff_summary": (current.validation_evidence or {}).get("current_understanding", "") if isinstance(current.validation_evidence, dict) else "",
        "created": False,
    }


def resume_after_steward(
    store: ConsultationStore,
    logical_consultation_id: str,
    *,
    question: str,
    evidence: Any = None,
) -> ConsultationRecord:
    """Create the next reasoning turn after explicit Steward input."""
    current = store.get(logical_consultation_id)
    return store.allocate_continuation(
        current.logical_consultation_id,
        status="awaiting_reasoning",
        objective=current.objective,
        question=question,
        current_evidence={"source": "steward", "evidence": evidence},
        prior_context_summary=(current.compact_summary or "")[:4000],
        continuation_reason="steward input after bounded autonomous evidence exhaustion",
        actor=current.actor,
        ptm_project_id=current.ptm_project_id,
        ptm_work_item_id=current.ptm_work_item_id,
        workflow_id=current.workflow_id,
        tags=current.tags,
    )
