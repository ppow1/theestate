"""Pure recommendation policy over WP-4220/4221/4222 published evidence."""
from __future__ import annotations

import hashlib
import json
from typing import Any

ENGINE_VERSION = "estate.engineering-campaign-recommendations/v1"
INTEGRATION_VERSION = "estate.engineering-dashboard-integration/v1"
SNAPSHOT_VERSION = "estate.engineering-campaign-dashboard/v1"
CATEGORIES = (
    "highest_value_next_work", "quick_wins", "parallel_work_groups",
    "merge_risk_reductions", "dependency_unblock_opportunities", "validation_priority",
    "technical_debt_opportunities", "stale_work_requiring_review", "superseded_work",
    "parking_lot_promotion_candidates",
)
WEIGHTS = {
    "queue_priority": 1, "dependent_unblock": 12, "ready": 25, "validation": 20,
    "short_duration": 15, "low_merge_risk": 8, "high_merge_risk": -15,
    "blocker": -10, "stale": -30, "superseded": -100, "missing_git": -5,
    "low_confidence": -5,
}


class RecommendationError(ValueError):
    """Input does not satisfy the published provider contracts."""


def _canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def validate_inputs(integration: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(integration, dict):
        return ["integration must be an object"]
    if integration.get("integration_schema_version") != INTEGRATION_VERSION:
        errors.append("unsupported integration_schema_version")
    snapshot = integration.get("dashboard_snapshot")
    if not isinstance(snapshot, dict):
        return errors + ["dashboard_snapshot must be an object"]
    if snapshot.get("snapshot_schema_version") != SNAPSHOT_VERSION:
        errors.append("unsupported snapshot_schema_version")
    panel = snapshot.get("panels", {}).get("execution_queue") if isinstance(snapshot.get("panels"), dict) else None
    if not isinstance(panel, dict) or not isinstance(panel.get("records"), list):
        errors.append("execution_queue records are required")
    else:
        seen: set[str] = set()
        for index, row in enumerate(panel["records"]):
            if not isinstance(row, dict) or not isinstance(row.get("item_identifier"), str):
                errors.append(f"execution_queue record {index} lacks item_identifier")
            elif row["item_identifier"] in seen:
                errors.append(f"duplicate item_identifier: {row['item_identifier']}")
            else:
                seen.add(row["item_identifier"])
    return errors


def _duration(row: dict[str, Any], providers: dict[str, Any]) -> tuple[float | None, str]:
    ref = row.get("duration_estimate_reference")
    values = providers.get("wp4214_duration", {})
    records = values.get("records", []) if isinstance(values, dict) else []
    for record in records:
        if record.get("item_identifier") == row["item_identifier"] or (ref and record.get("estimate_id") == ref):
            value = record.get("estimated_hours")
            return (float(value), "WP-4214") if isinstance(value, (int, float)) else (None, "missing")
    return None, "missing"


def _score(row: dict[str, Any], dependents: int, providers: dict[str, Any]) -> tuple[int, list[dict[str, Any]]]:
    parts: list[dict[str, Any]] = []
    def add(rule: str, value: int, evidence: Any) -> None:
        parts.append({"rule": rule, "value": value, "evidence": evidence})
    priority = row.get("priority", {}).get("score", 0)
    add("queue_priority", int(priority) * WEIGHTS["queue_priority"], priority)
    add("dependent_unblock", dependents * WEIGHTS["dependent_unblock"], dependents)
    readiness = row.get("readiness_classification")
    if readiness in ("ready", "ready_with_coordination"): add("ready", WEIGHTS["ready"], readiness)
    if readiness == "validation": add("validation", WEIGHTS["validation"], readiness)
    duration, source = _duration(row, providers)
    if duration is not None and duration <= 8: add("short_duration", WEIGHTS["short_duration"], {"hours": duration, "provider": source})
    risk = row.get("merge_risk_classification")
    if risk == "low": add("low_merge_risk", WEIGHTS["low_merge_risk"], risk)
    if risk == "high": add("high_merge_risk", WEIGHTS["high_merge_risk"], risk)
    blockers = len(row.get("blockers", [])); add("blocker", blockers * WEIGHTS["blocker"], blockers)
    classification = row.get("reconciliation_classification")
    if classification == "stale" or "stale_source" in row.get("diagnostics", []): add("stale", WEIGHTS["stale"], classification)
    if classification == "superseded": add("superseded", WEIGHTS["superseded"], classification)
    if not row.get("git_readiness_reference"): add("missing_git", WEIGHTS["missing_git"], None)
    if row.get("evidence_completeness") == "missing": add("low_confidence", WEIGHTS["low_confidence"], "missing")
    return sum(p["value"] for p in parts), parts


def recommend(integration: dict[str, Any], *, limit: int = 10) -> dict[str, Any]:
    """Return advice without mutating input or provider artifacts."""
    errors = validate_inputs(integration)
    if errors: raise RecommendationError("; ".join(errors))
    snapshot = integration["dashboard_snapshot"]
    rows = snapshot["panels"]["execution_queue"]["records"]
    providers = integration.get("provider_payloads", {})
    reverse = {r["item_identifier"]: 0 for r in rows}
    for row in rows:
        for dep in row.get("dependencies", []):
            if dep in reverse: reverse[dep] += 1
    source_hash = integration.get("deterministic_content_hash") or _digest(integration)
    entries: list[dict[str, Any]] = []
    for row in rows:
        identifier = row["item_identifier"]
        score, parts = _score(row, reverse[identifier], providers)
        duration, duration_source = _duration(row, providers)
        provenance = {
            "integration_hash": source_hash,
            "snapshot_identifier": snapshot.get("snapshot_identifier"),
            "queue_generation_identifier": snapshot.get("source_queue_generation_identifier"),
            "item_identifier": identifier,
            "source_evidence_references": sorted(row.get("source_evidence_references", [])),
            "provider_status": {d.get("provider_id"): d.get("status") for d in integration.get("provider_diagnostics", [])},
        }
        categories: list[str] = []
        ready = row.get("readiness_classification") in ("ready", "ready_with_coordination")
        classification = row.get("reconciliation_classification")
        if ready and classification not in ("stale", "superseded"): categories.append("highest_value_next_work")
        if ready and duration is not None and duration <= 8 and row.get("merge_risk_classification") == "low": categories.append("quick_wins")
        if ready and row.get("parallel_safety_classification") == "safe" and row.get("parallel_group"): categories.append("parallel_work_groups")
        if row.get("merge_risk_classification") == "high": categories.append("merge_risk_reductions")
        if reverse[identifier] > 0: categories.append("dependency_unblock_opportunities")
        if row.get("readiness_classification") == "validation" or classification == "implemented_but_not_validated": categories.append("validation_priority")
        if classification in ("partially_implemented", "duplicate", "ambiguous_requires_review"): categories.append("technical_debt_opportunities")
        if classification == "stale" or "stale_source" in row.get("diagnostics", []): categories.append("stale_work_requiring_review")
        if classification == "superseded": categories.append("superseded_work")
        if identifier.startswith("PL-") and classification == "captured" and ready: categories.append("parking_lot_promotion_candidates")
        for category in categories:
            entries.append({"recommendation_id": f"{category}:{identifier}", "category": category,
                "item_identifiers": [identifier], "score": score, "score_components": parts,
                "reason": f"{identifier} matches deterministic {category} policy",
                "duration_hours": duration, "duration_evidence": duration_source, "provenance": provenance})
    grouped: list[dict[str, Any]] = []
    parallel = [e for e in entries if e["category"] == "parallel_work_groups"]
    groups: dict[str, list[dict[str, Any]]] = {}
    by_id = {r["item_identifier"]: r for r in rows}
    for entry in parallel:
        group = str(by_id[entry["item_identifiers"][0]]["parallel_group"])
        groups.setdefault(group, []).append(entry)
    entries = [e for e in entries if e["category"] != "parallel_work_groups"]
    for group, members in sorted(groups.items()):
        ids = sorted(m["item_identifiers"][0] for m in members)
        grouped.append({"recommendation_id": f"parallel_work_groups:{group}", "category": "parallel_work_groups",
            "item_identifiers": ids, "score": sum(m["score"] for m in members),
            "score_components": [{"rule": "member_scores", "value": sum(m["score"] for m in members), "evidence": ids}],
            "reason": f"WP-4215/queue parallel group {group} is marked safe", "duration_hours": None,
            "duration_evidence": "member estimates", "provenance": members[0]["provenance"]})
    entries.extend(grouped)
    sets = {category: sorted((e for e in entries if e["category"] == category), key=lambda e: (-e["score"], e["item_identifiers"], e["recommendation_id"]))[:limit] for category in CATEGORIES}
    logical = {"recommendation_schema_version": ENGINE_VERSION, "policy_version": "wp4223-deterministic-policy/v1",
        "advisory_only": True, "authority": "none", "source_integration_hash": source_hash,
        "provider_health": integration.get("health", "unknown"), "recommendation_sets": sets,
        "diagnostics": sorted(integration.get("degradation_reasons", [])), "weights": WEIGHTS}
    logical["deterministic_content_hash"] = _digest(logical)
    return logical


def explain(result: dict[str, Any], recommendation_id: str) -> dict[str, Any]:
    for entries in result.get("recommendation_sets", {}).values():
        for entry in entries:
            if entry["recommendation_id"] == recommendation_id:
                return entry
    raise RecommendationError(f"unknown recommendation_id: {recommendation_id}")


def compare(result: dict[str, Any], left: str, right: str) -> dict[str, Any]:
    a, b = explain(result, left), explain(result, right)
    winner = left if (-a["score"], a["recommendation_id"]) < (-b["score"], b["recommendation_id"]) else right
    return {"left": a, "right": b, "higher_ranked": winner,
            "score_delta_left_minus_right": a["score"] - b["score"], "tie_breaker": "recommendation_id ascending"}
