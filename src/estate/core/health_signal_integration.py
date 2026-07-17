"""Canonical health evidence normalization for CAMPAIGN-0681.

This module is a read-only adapter over resident, service, worker, provider and
validation evidence.  It deliberately owns neither health state nor authority:
callers supply records read from the canonical systems and receive a rebuildable
projection suitable for observation and blocker classification.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable

SCHEMA_VERSION = "estate.health-signal.v1"
HEALTH_DOMAINS = {"resident", "service", "runtime", "provider_environment", "validation"}
STATES = {"healthy", "degraded", "unavailable", "failed", "unknown", "stale", "contradictory"}

STATE_SEVERITY = {
    "healthy": "info", "unknown": "warning", "stale": "warning",
    "degraded": "warning", "unavailable": "error", "failed": "critical",
    "contradictory": "critical",
}
STATE_RANK = {"healthy": 0, "unknown": 1, "stale": 2, "degraded": 3,
              "unavailable": 4, "failed": 5, "contradictory": 6}
NEGATIVE_STATES = {"degraded", "unavailable", "failed"}
FAIL_CLOSED_STATES = {"unknown", "stale", "contradictory", "unavailable", "failed"}

# Durable repository evidence wins over runtime/UI summaries.  Equal-ranked,
# current, authoritative evidence that disagrees is surfaced as contradictory.
SOURCE_PRECEDENCE = {
    "canonical_registry": 50,
    "schema_valid_receipt": 50,
    "repository_authoritative": 45,
    "direct_observation": 35,
    "runtime_heartbeat": 30,
    "status_board": 20,
    "dashboard": 10,
    "inference": 0,
}

STATE_ALIASES = {
    "active": "healthy", "ready": "healthy", "ready_for_service": "healthy",
    "operational": "healthy", "running": "healthy", "passed": "healthy",
    "idle": "healthy", "validated": "healthy", "available": "healthy",
    "partial": "degraded", "warning": "degraded", "blocked": "degraded",
    "paused": "unavailable", "stand_down": "unavailable", "offline": "unavailable",
    "shutdown": "unavailable", "refused": "unavailable", "down": "unavailable",
    "error": "failed", "failure": "failed", "invalid": "failed",
}


def _utc(value: str | datetime | None) -> datetime | None:
    if isinstance(value, datetime):
        parsed = value
    elif value:
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return None
    else:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _state(value: Any) -> str:
    raw = str(value or "unknown").strip().lower()
    normalized = STATE_ALIASES.get(raw, raw)
    return normalized if normalized in STATES else "unknown"


def normalize_health_evidence(
    evidence: dict[str, Any], *, observed_at: str | datetime | None = None,
    default_ttl_seconds: int = 3600,
) -> dict[str, Any]:
    """Normalize one canonical evidence record without changing the input."""
    item = deepcopy(evidence)
    now = _utc(observed_at) or datetime.now(timezone.utc)
    domain = str(item.get("health_domain") or item.get("domain") or "").lower()
    if domain not in HEALTH_DOMAINS:
        raise ValueError(f"health_domain must be one of {sorted(HEALTH_DOMAINS)}")
    subject_type = str(item.get("subject_type") or domain).strip()
    subject_id = str(item.get("subject_id") or item.get("resident_id") or item.get("service_id") or item.get("worker_id") or "").strip()
    if not subject_id:
        raise ValueError("a stable subject_id is required")

    source_time = _utc(item.get("source_timestamp") or item.get("updated_at") or item.get("last_heartbeat"))
    ttl = int(item.get("ttl_seconds", default_ttl_seconds))
    expires = _utc(item.get("expires_at")) or (source_time + timedelta(seconds=ttl) if source_time else None)
    freshness = "unknown" if source_time is None else ("stale" if expires and now > expires else "current")
    raw_state = _state(item.get("state") or item.get("health_status") or item.get("status") or item.get("board_state"))
    state = "stale" if freshness == "stale" else raw_state
    source_kind = str(item.get("source_kind") or "inference")
    refs = item.get("evidence_references") or item.get("canonical_evidence_references") or []
    if isinstance(refs, str):
        refs = [refs]
    refs = sorted({str(ref) for ref in refs if ref})
    warnings = list(item.get("warnings") or [])
    if source_time is None:
        warnings.append("source timestamp is missing; freshness is unknown")
    if not refs:
        warnings.append("canonical evidence reference is missing")
    if freshness == "stale":
        warnings.append(f"evidence expired at {_iso(expires)}")

    required = bool(item.get("required_dependency", False))
    protected = bool(item.get("protected_review", False))
    effect = "requires_protected_review" if protected else (
        "blocks_progression" if (required and state in FAIL_CLOSED_STATES) or state in {"failed", "contradictory"} else "observation_only"
    )
    lane = str(item.get("responsible_lane") or {
        "resident": "resident lifecycle owner", "service": "service owner",
        "runtime": "Engineering operations", "provider_environment": "Engineering provider operations",
        "validation": "validation authority",
    }[domain])
    explanation = str(item.get("explanation") or f"{subject_type} {subject_id} is {state} based on {source_kind} evidence.")
    if freshness == "stale":
        explanation = f"{subject_type} {subject_id} evidence is stale; last reported state was {raw_state}."
    return {
        "schema_version": SCHEMA_VERSION,
        "subject_type": subject_type,
        "subject_id": subject_id,
        "health_domain": domain,
        "normalized_state": state,
        "reported_state": raw_state,
        "severity": STATE_SEVERITY[state],
        "observed_timestamp": _iso(now),
        "source_timestamp": _iso(source_time) if source_time else None,
        "expires_at": _iso(expires) if expires else None,
        "freshness": freshness,
        "canonical_evidence_references": refs,
        "source_kind": source_kind,
        "source_precedence": SOURCE_PRECEDENCE.get(source_kind, 0),
        "dependency_or_campaign_impact": deepcopy(item.get("campaign_impact") or {}),
        "required_dependency": required,
        "explanation": explanation,
        "uncertainty_or_contradiction_warnings": sorted(set(warnings)),
        "responsible_lane": lane,
        "reevaluation_trigger": str(item.get("reevaluation_trigger") or "new canonical evidence or evidence expiry"),
        "progression_effect": effect,
        "authorizes_action": False,
        "recovery_clears": sorted(set(item.get("recovery_clears") or [])),
        "derivation_rule": "normalize-explicit-evidence-v1",
    }


def unknown_signal(subject_type: str, subject_id: str, health_domain: str, *,
                   observed_at: str | datetime | None = None,
                   evidence_reference: str | None = None,
                   required_dependency: bool = False) -> dict[str, Any]:
    return normalize_health_evidence({
        "subject_type": subject_type, "subject_id": subject_id,
        "health_domain": health_domain, "state": "unknown",
        "source_kind": "repository_authoritative",
        "source_timestamp": observed_at,
        "evidence_references": [evidence_reference] if evidence_reference else [],
        "required_dependency": required_dependency,
        "explanation": f"No current health evidence exists for {subject_type} {subject_id}.",
        "warnings": ["health evidence is missing; health was not assumed"],
    }, observed_at=observed_at)


def reconcile_health_signals(signals: Iterable[dict[str, Any]], *,
                             observed_at: str | datetime | None = None) -> dict[str, Any]:
    """Reconcile signals for one subject using deterministic, fail-closed rules."""
    normalized = [s if s.get("schema_version") == SCHEMA_VERSION else normalize_health_evidence(s, observed_at=observed_at) for s in signals]
    if not normalized:
        raise ValueError("reconciliation requires at least one signal")
    identities = {(s["subject_type"], s["subject_id"], s["health_domain"]) for s in normalized}
    if len(identities) != 1:
        raise ValueError("all reconciled signals must describe the same subject and health domain")
    normalized.sort(key=lambda s: (-s["source_precedence"], s["source_timestamp"] or "", tuple(s["canonical_evidence_references"])))
    max_precedence = normalized[0]["source_precedence"]
    contenders = [s for s in normalized if s["source_precedence"] == max_precedence and s["freshness"] != "stale"]
    states = {s["normalized_state"] for s in contenders}
    contradictory = len(states) > 1 and bool(states & {"healthy"}) and bool(states & NEGATIVE_STATES)
    selected = normalized[0]
    rule = "highest-precedence-current-evidence"
    warnings = [w for s in normalized for w in s["uncertainty_or_contradiction_warnings"]]
    if contradictory:
        state = "contradictory"
        rule = "equal-precedence-opposing-current-evidence-fail-closed"
        warnings.append("equally authoritative current evidence reports opposing health states")
    elif contenders:
        # Explicit negative evidence wins within the selected evidence class.
        selected = max(contenders, key=lambda s: (STATE_RANK[s["normalized_state"]], s["source_timestamp"] or ""))
        state = selected["normalized_state"]
        rule = "explicit-negative-outranks-optimistic-evidence" if len(states) > 1 else rule
    else:
        state = "stale"
        rule = "no-current-evidence-stale-fail-closed"

    # A recovery claim only clears a prior negative condition when it names its evidence.
    if state == "healthy":
        prior_negative_refs = {r for s in normalized if s["reported_state"] in NEGATIVE_STATES for r in s["canonical_evidence_references"]}
        cleared = {r for s in contenders if s["normalized_state"] == "healthy" for r in s.get("recovery_clears", [])}
        uncleared = prior_negative_refs - cleared
        if uncleared:
            state = "degraded"
            rule = "recovery-requires-explicit-clearance"
            warnings.append("healthy evidence does not explicitly clear prior negative evidence: " + ", ".join(sorted(uncleared)))

    result = deepcopy(selected)
    result.update({
        "normalized_state": state,
        "severity": STATE_SEVERITY[state],
        "canonical_evidence_references": sorted({r for s in normalized for r in s["canonical_evidence_references"]}),
        "uncertainty_or_contradiction_warnings": sorted(set(warnings)),
        "derivation_rule": rule,
        "contributing_signal_count": len(normalized),
        "progression_effect": "requires_protected_review" if any(s["progression_effect"] == "requires_protected_review" for s in normalized) else (
            "blocks_progression" if state in {"failed", "contradictory"} or (any(s["required_dependency"] for s in normalized) and state in FAIL_CLOSED_STATES) else "observation_only"
        ),
        "authorizes_action": False,
    })
    result["explanation"] = f"{result['subject_type']} {result['subject_id']} reconciled as {state} by rule {rule}."
    return result


def adapt_resident_health(record: dict[str, Any], *, source_path: str,
                          observed_at: str | datetime | None = None,
                          interaction: dict[str, Any] | None = None) -> dict[str, Any]:
    """Adapt lifecycle truth; interaction responsiveness is context, not readiness."""
    status = record.get("status")
    state = {"active": "healthy", "ready_for_service": "healthy", "reflection_due": "degraded",
             "in_reflection": "degraded", "stand_down": "unavailable", "retired": "unavailable",
             "archived": "unavailable"}.get(str(status), "unknown")
    warnings = []
    if interaction:
        warnings.append("interaction evidence supplements lifecycle evidence and does not prove readiness")
    return normalize_health_evidence({
        "subject_type": "resident", "subject_id": record.get("resident_id"), "health_domain": "resident",
        "state": state, "source_timestamp": record.get("updated_at"), "source_kind": "repository_authoritative",
        "evidence_references": [source_path], "responsible_lane": record.get("responsible_lane") or "resident lifecycle owner",
        "warnings": warnings, "explanation": f"Resident lifecycle state {status!r} maps to {state}; profile or responsiveness is not readiness.",
        "protected_review": state in {"unavailable", "failed"},
    }, observed_at=observed_at)


def adapt_service_health(entry: dict[str, Any], *, source_path: str,
                         observed_at: str | datetime | None = None,
                         required_dependency: bool = False) -> dict[str, Any]:
    state = entry.get("health_status") or entry.get("board_state") or "unknown"
    dep = str((entry.get("dependency_health") or {}).get("summary") or entry.get("dependency_summary") or "unknown")
    if _state(dep) in NEGATIVE_STATES and STATE_RANK[_state(dep)] > STATE_RANK[_state(state)]:
        state = _state(dep)
    refs = [source_path] + [x.get("path") for x in entry.get("authoritative_sources", []) if x.get("path")]
    return normalize_health_evidence({
        "subject_type": "service", "subject_id": entry.get("service_id"), "health_domain": "service",
        "state": state, "source_timestamp": entry.get("last_known_update") or entry.get("updated_at"),
        "source_kind": "canonical_registry", "evidence_references": refs,
        "required_dependency": required_dependency, "responsible_lane": entry.get("owner") or "service owner",
        "campaign_impact": {"dependency_summary": dep},
        "explanation": f"Canonical service health is {_state(state)}; dependency summary is {dep}.",
    }, observed_at=observed_at)


def adapt_worker_heartbeat(record: dict[str, Any], *, source_path: str,
                           observed_at: str | datetime | None = None,
                           required_dependency: bool = False) -> dict[str, Any]:
    return normalize_health_evidence({
        "subject_type": "worker", "subject_id": record.get("worker_id"), "health_domain": "runtime",
        "state": record.get("status"), "source_timestamp": record.get("last_heartbeat"),
        "source_kind": "runtime_heartbeat", "evidence_references": [source_path],
        "ttl_seconds": record.get("stale_after_seconds", 3600), "required_dependency": required_dependency,
        "responsible_lane": "Engineering operations",
        "explanation": "Worker-reported heartbeat describes runtime availability, not authority or functional service readiness.",
    }, observed_at=observed_at)


def adapt_operations_runtime(record: dict[str, Any], *, source_path: str,
                             observed_at: str | datetime | None = None,
                             required_dependency: bool = False) -> dict[str, Any]:
    """Adapt operations-cycle evidence without equating a PID with readiness."""
    cycle_state = record.get("cycle_status") or record.get("status") or "unknown"
    functional = record.get("functional_readiness")
    state = cycle_state
    warnings = []
    if functional is False and _state(cycle_state) == "healthy":
        state = "degraded"
        warnings.append("process existence or heartbeat does not establish functional readiness")
    return normalize_health_evidence({
        "subject_type": "operations_runtime", "subject_id": record.get("runtime_id") or record.get("service_id") or "estate-operations-runtime",
        "health_domain": "runtime", "state": state,
        "source_timestamp": record.get("last_completed_cycle_at") or record.get("heartbeat_at") or record.get("updated_at"),
        "source_kind": "direct_observation", "evidence_references": [source_path],
        "required_dependency": required_dependency, "warnings": warnings,
        "responsible_lane": "Engineering operations",
        "explanation": "Operations-runtime cycle evidence is distinct from process existence, service ownership, and action authority.",
    }, observed_at=observed_at)


def adapt_provider_environment_health(record: dict[str, Any], *, source_path: str,
                                      observed_at: str | datetime | None = None,
                                      required_dependency: bool = False) -> dict[str, Any]:
    """Adapt the existing provider-health output; this is not a provider registry."""
    return normalize_health_evidence({
        "subject_type": "provider_environment", "subject_id": record.get("provider_id") or record.get("environment_id") or record.get("id"),
        "health_domain": "provider_environment",
        "state": record.get("health_state") or record.get("availability") or record.get("status"),
        "source_timestamp": record.get("observed_at") or record.get("updated_at"),
        "source_kind": "direct_observation", "evidence_references": [source_path],
        "required_dependency": required_dependency,
        "responsible_lane": record.get("responsible_lane") or "Engineering provider operations",
        "explanation": "Provider or environment evidence reports availability only; it grants no dispatch, spending, or execution authority.",
    }, observed_at=observed_at)


def adapt_validation_health(record: dict[str, Any], *, source_path: str,
                            observed_at: str | datetime | None = None,
                            required_dependency: bool = True) -> dict[str, Any]:
    return normalize_health_evidence({
        "subject_type": "validation_run", "subject_id": record.get("work_package_id") or record.get("validation_id") or record.get("id"),
        "health_domain": "validation", "state": record.get("verdict") or record.get("status"),
        "source_timestamp": record.get("completed_at") or record.get("updated_at") or record.get("generated_at"),
        "source_kind": "schema_valid_receipt", "evidence_references": [source_path],
        "required_dependency": required_dependency, "responsible_lane": "validation authority",
        "explanation": "Validation evidence is observed independently from execution completion and institutional acceptance.",
    }, observed_at=observed_at)


def aggregate_health(signals: Iterable[dict[str, Any]], *, campaign_id: str | None = None,
                     work_package_id: str | None = None) -> dict[str, Any]:
    """Return deterministic campaign-impact and blocker facts without mutation."""
    items = [deepcopy(s) for s in signals]
    items.sort(key=lambda s: (s["health_domain"], s["subject_type"], s["subject_id"]))
    counts = {state: sum(s["normalized_state"] == state for s in items) for state in sorted(STATES)}
    required = [s for s in items if s.get("required_dependency")]
    blockers = [s for s in required if s["normalized_state"] in FAIL_CLOSED_STATES]
    critical = [s for s in items if s["normalized_state"] in {"failed", "contradictory"}]
    relevant = blockers + [s for s in critical if s not in blockers]
    overall = max((s["normalized_state"] for s in items), key=lambda st: STATE_RANK[st], default="unknown")
    progression = "blocks_progression" if relevant else "observation_only"
    return {
        "schema_version": SCHEMA_VERSION,
        "campaign_id": campaign_id, "work_package_id": work_package_id,
        "overall_state": overall, "progression_effect": progression,
        "counts": counts, "signals": items,
        "blocker_facts": [{
            "subject_type": s["subject_type"], "subject_id": s["subject_id"],
            "health_domain": s["health_domain"], "state": s["normalized_state"],
            "severity": s["severity"], "evidence_references": s["canonical_evidence_references"],
            "responsible_lane": s["responsible_lane"], "recommended_destination": s["responsible_lane"],
            "explanation": s["explanation"], "authorizes_action": False,
        } for s in relevant],
        "explanation": f"{overall} aggregate from {len(items)} signals; {len(relevant)} blocker-ready facts. Healthy signals do not conceal degraded required dependencies.",
        "observation_only": True, "authorizes_action": False,
        "derivation_rule": "worst-visible-state-and-required-dependency-fail-closed-v1",
    }
