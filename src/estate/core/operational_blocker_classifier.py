"""Deterministic, observation-only blocker and escalation classification.

The classifier consumes facts already produced by canonical Estate systems.  It
does not persist a blocker, send a message, or perform the recommended action.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Iterable

SCHEMA_VERSION = "estate.operational-blocker-classification.v1"

BLOCKER_CLASSES = {
    "dependency_blocker", "readiness_blocker", "resident_health_blocker",
    "service_health_blocker", "staffing_or_capability_blocker",
    "provider_or_environment_blocker", "evidence_or_validation_blocker",
    "communication_or_acknowledgement_blocker", "architectural_blocker",
    "acceptance_blocker", "protected_steward_decision",
    "transient_operational_failure", "recoverable_execution_failure",
    "contradictory_state_blocker", "stale_evidence_blocker",
    "unknown_authority_blocker",
}

# More safety-significant rules win regardless of input order.
PRIORITY = {
    "unknown_authority_blocker": 160, "contradictory_state_blocker": 150,
    "protected_steward_decision": 140, "stale_evidence_blocker": 130,
    "acceptance_blocker": 120, "architectural_blocker": 115,
    "evidence_or_validation_blocker": 110, "resident_health_blocker": 105,
    "service_health_blocker": 100, "provider_or_environment_blocker": 95,
    "staffing_or_capability_blocker": 90, "readiness_blocker": 85,
    "dependency_blocker": 80, "communication_or_acknowledgement_blocker": 75,
    "recoverable_execution_failure": 70, "transient_operational_failure": 60,
}

ROUTES = {
    "dependency_blocker": ("package owner", "canonical dependency owner"),
    "readiness_blocker": ("readiness authority", "readiness authority"),
    "resident_health_blocker": ("Helen / resident lifecycle lane", "Helen"),
    "service_health_blocker": ("service owner", "service owner"),
    "staffing_or_capability_blocker": ("Helen workforce lane", "Helen"),
    "provider_or_environment_blocker": ("Engineering provider operations", "Engineering"),
    "evidence_or_validation_blocker": ("validation authority", "validation authority"),
    "communication_or_acknowledgement_blocker": ("canonical mailbox owner", "destination office mailbox"),
    "architectural_blocker": ("Chief Architect", "Chief Architect"),
    "acceptance_blocker": ("applicable acceptance authority", "applicable acceptance authority"),
    "protected_steward_decision": ("Steward", "Steward"),
    "transient_operational_failure": ("operational owner", "operational owner"),
    "recoverable_execution_failure": ("Engineering execution lane", "Engineering"),
    "contradictory_state_blocker": ("canonical evidence owners", "Chief Architect"),
    "stale_evidence_blocker": ("canonical evidence owner", "canonical evidence owner"),
    "unknown_authority_blocker": ("authority record owner", "Chief Architect"),
}

SEVERITY = {
    "protected_steward_decision": "critical", "unknown_authority_blocker": "critical",
    "contradictory_state_blocker": "critical", "architectural_blocker": "critical",
    "resident_health_blocker": "critical", "acceptance_blocker": "error",
    "evidence_or_validation_blocker": "error", "service_health_blocker": "error",
    "provider_or_environment_blocker": "error", "staffing_or_capability_blocker": "error",
    "readiness_blocker": "error", "dependency_blocker": "error",
    "stale_evidence_blocker": "error", "communication_or_acknowledgement_blocker": "warning",
    "recoverable_execution_failure": "warning", "transient_operational_failure": "warning",
}


def classify_blockers(
    affected: str, facts: Iterable[dict[str, Any]], *,
    canonical_dependencies_allow_parallel: bool = False,
    collision_check_clear: bool = False,
) -> dict[str, Any]:
    """Classify supplied canonical facts, failing closed on evidence/authority gaps."""
    copied = [deepcopy(f) for f in facts]
    if not affected.strip():
        raise ValueError("affected campaign or work package is required")
    if not copied:
        copied = [{"condition": "unknown_authority", "state": "unknown",
                   "summary": "No canonical facts were supplied.", "evidence_references": []}]

    classes: set[str] = set()
    missing_refs = False
    ambiguous_authority = False
    for fact in copied:
        condition = str(fact.get("condition") or "").strip().lower().replace("-", "_")
        state = str(fact.get("state") or "unknown").strip().lower()
        refs = fact.get("evidence_references") or fact.get("canonical_evidence_references") or []
        if isinstance(refs, str):
            refs = [refs]
        fact["canonical_evidence_references"] = sorted({str(x) for x in refs if x})
        missing_refs |= not bool(fact["canonical_evidence_references"])
        ambiguous_authority |= bool(fact.get("authority_ambiguous")) or condition == "unknown_authority"
        explicit = str(fact.get("blocker_class") or "")
        if explicit in BLOCKER_CLASSES:
            classes.add(explicit)
        elif condition in {"contradictory_state", "contradiction"} or state == "contradictory":
            classes.add("contradictory_state_blocker")
        elif condition in {"stale_evidence", "stale"} or state == "stale":
            classes.add("stale_evidence_blocker")
        elif condition == "protected_steward_decision":
            classes.add("protected_steward_decision")
        elif condition:
            candidate = condition if condition in BLOCKER_CLASSES else f"{condition}_blocker"
            classes.add(candidate if candidate in BLOCKER_CLASSES else "unknown_authority_blocker")
    if ambiguous_authority:
        classes.add("unknown_authority_blocker")
    if missing_refs:
        classes.add("evidence_or_validation_blocker")

    ordered = sorted(classes, key=lambda x: (-PRIORITY[x], x))
    primary = ordered[0]
    lane, destination = ROUTES[primary]
    protected = primary in {"protected_steward_decision", "architectural_blocker", "acceptance_blocker", "unknown_authority_blocker"}
    uncertain = ambiguous_authority or missing_refs or primary in {"contradictory_state_blocker", "stale_evidence_blocker", "unknown_authority_blocker"}
    may_continue = bool(canonical_dependencies_allow_parallel and collision_check_clear and not protected)
    next_action = {
        "transient_operational_failure": "Use the canonical bounded retry policy, then reevaluate.",
        "recoverable_execution_failure": "Resume or retry only through the canonical execution/Dispatch recovery seam.",
        "communication_or_acknowledgement_blocker": "Send or acknowledge through the canonical repository-message/mailbox mechanism.",
    }.get(primary, "Obtain current canonical evidence or a decision from the named authority, then reevaluate.")
    return {
        "schema_version": SCHEMA_VERSION,
        "affected_campaign_or_work_package": affected,
        "observed_facts": copied,
        "canonical_evidence_references": sorted({r for f in copied for r in f["canonical_evidence_references"]}),
        "blocker_class": primary,
        "additional_blocker_classes": ordered[1:],
        "severity": SEVERITY[primary],
        "work_may_continue_in_unaffected_lanes": may_continue,
        "continuation_basis": "canonical dependencies permit parallel work and collision check is clear" if may_continue else "affected lane stops; unaffected work lacks both canonical parallel-dependency and collision clearance",
        "responsible_office_or_authority_lane": lane,
        "recommended_next_action": next_action,
        "escalation_destination": destination,
        "acknowledgement_requirement": f"Acknowledgement by {destination} must be recorded through the canonical mailbox/repository-message mechanism.",
        "reevaluation_trigger": "new current canonical evidence, recorded acknowledgement, recovered execution result, or protected decision",
        "fail_closed_reason": ("Authority or evidence is missing, stale, or contradictory; uncertainty is not permission." if uncertain else None),
        "protected_decision": protected,
        "classification_is_observation_and_recommendation_only": True,
        "authorizes_action": False,
        "mutated_canonical_state": False,
    }


def declassification_ready(classification: dict[str, Any], replacement_facts: Iterable[dict[str, Any]]) -> bool:
    """Return readiness to reevaluate, never permission or automatic declassification."""
    facts = list(replacement_facts)
    return bool(facts) and all(
        (f.get("evidence_references") or f.get("canonical_evidence_references"))
        and str(f.get("state") or "").lower() in {"clear", "cleared", "healthy", "passed", "accepted", "acknowledged", "recovered"}
        and bool(f.get("clears_references"))
        for f in facts
    ) and not classification.get("authorizes_action", False)
