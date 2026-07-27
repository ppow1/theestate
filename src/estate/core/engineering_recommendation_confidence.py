"""Deterministic, advisory evidence assessment for published recommendations."""
from __future__ import annotations

import copy
import hashlib
import json
from typing import Any, Mapping

REPORT_VERSION = "estate.engineering-recommendation-confidence/v1"
EVIDENCE_VERSION = "estate.engineering-recommendation-evidence/v1"
SUMMARY_VERSION = "estate.engineering-evidence-summary/v1"
METADATA_VERSION = "estate.engineering-confidence-metadata/v1"
SUPPORTED = {
    "engineering_queue": "estate.engineering-queue/v1",
    "dashboard": "estate.engineering-campaign-dashboard/v1",
    "integration": "estate.engineering-dashboard-integration/v1",
    "recommendations": "estate.engineering-campaign-recommendations/v1",
    "decision_ledger": "estate.engineering-recommendation-ledger/v1",
    "analytics": "estate.engineering-campaign-analytics/v1",
}
VERSION_KEYS = {
    "engineering_queue": "queue_schema_version", "dashboard": "snapshot_schema_version",
    "integration": "integration_schema_version", "recommendations": "recommendation_schema_version",
    "decision_ledger": "ledger_schema_version", "analytics": "analytics_schema_version",
}
CHECKS = ("provenance", "dependencies", "validation", "merge_risk", "freshness", "providers", "data", "schema")


class ConfidenceError(ValueError):
    """Published evidence cannot be assessed safely."""


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def content_hash(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def validate_sources(sources: Any) -> list[str]:
    if not isinstance(sources, dict):
        return ["sources must be an object"]
    errors = []
    if set(sources) != set(SUPPORTED):
        errors.append("sources must contain exactly: " + ", ".join(SUPPORTED))
    for name, version in SUPPORTED.items():
        value = sources.get(name)
        if not isinstance(value, dict):
            errors.append(f"{name} must be an object")
        elif value.get(VERSION_KEYS[name]) != version:
            errors.append(f"unsupported schema: {name}")
    recommendations = sources.get("recommendations", {})
    sets = recommendations.get("recommendation_sets") if isinstance(recommendations, dict) else None
    if not isinstance(sets, dict):
        errors.append("recommendation_sets must be an object")
    elif any(not isinstance(rows, list) for rows in sets.values()):
        errors.append("every recommendation set must be an array")
    return errors


def _recommendations(sources: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for category in sorted(sources["recommendations"]["recommendation_sets"]):
        for row in sources["recommendations"]["recommendation_sets"][category]:
            if not isinstance(row, dict) or not isinstance(row.get("recommendation_id"), str):
                raise ConfidenceError(f"malformed recommendation in {category}")
            rows.append(row)
    identifiers = [row["recommendation_id"] for row in rows]
    if len(identifiers) != len(set(identifiers)):
        raise ConfidenceError("duplicate recommendation_id")
    return sorted(rows, key=lambda row: row["recommendation_id"])


def _queue_rows(sources: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    queue = sources["engineering_queue"]
    records = queue.get("candidates", queue.get("items", []))
    return {str(r.get("item_identifier", r.get("id"))): r for r in records if isinstance(r, dict)}


def _level(covered: int, total: int, conflicts: list[str]) -> str:
    if total == 0 or covered < 3:
        return "insufficient_evidence"
    ratio = covered / total
    if conflicts or ratio < .625:
        return "low"
    if ratio < .75:
        return "moderate"
    if ratio < 1:
        return "high"
    return "very_high"


def assess(sources: Mapping[str, Any], *, assessed_at: str) -> dict[str, Any]:
    """Assess supplied published outputs without recomputing or mutating them."""
    errors = validate_sources(sources)
    if errors:
        raise ConfidenceError("; ".join(errors))
    if not isinstance(assessed_at, str) or not assessed_at:
        raise ConfidenceError("assessed_at is required")
    frozen = copy.deepcopy(dict(sources))
    queue = _queue_rows(frozen)
    integration = frozen["integration"]
    diagnostics = integration.get("provider_diagnostics", [])
    degraded = sorted(str(d.get("provider_id")) for d in diagnostics if isinstance(d, dict) and d.get("status") not in ("healthy", "available"))
    freshness = integration.get("freshness", frozen["dashboard"].get("freshness", "unknown"))
    dependency_graph = frozen["dashboard"].get("panels", {}).get("dependency_graph", {})
    merge_risk = frozen["dashboard"].get("panels", {}).get("merge_risk", {})
    entries = []
    for recommendation in _recommendations(frozen):
        item_ids = recommendation.get("item_identifiers", [])
        related = [queue[x] for x in item_ids if x in queue]
        source_refs = sorted({str(ref) for row in related for ref in row.get("source_evidence_references", [])})
        provenance = recommendation.get("provenance", {})
        status = {
            "provenance": bool(provenance and (provenance.get("integration_hash") or source_refs)),
            "dependencies": bool(dependency_graph) or all("dependencies" in row for row in related),
            "validation": bool(related) and all(row.get("validation_state") in ("validated", "passed") or row.get("readiness_classification") == "validation" for row in related),
            "merge_risk": bool(merge_risk) or (bool(related) and all("merge_risk_classification" in row for row in related)),
            "freshness": freshness in ("fresh", "current", "healthy"),
            "providers": not degraded and bool(diagnostics),
            "data": bool(item_ids) and len(related) == len(item_ids),
            "schema": True,
        }
        conflicts = []
        edges = dependency_graph.get("edges", []) if isinstance(dependency_graph, dict) else []
        for edge in edges:
            if isinstance(edge, dict) and edge.get("conflict") is True:
                conflicts.append(f"dependency:{edge.get('from')}->{edge.get('to')}")
        conflicts.extend(sorted(str(x) for x in integration.get("conflicting_evidence", [])))
        missing = [name for name in CHECKS if not status[name]]
        covered = len(CHECKS) - len(missing)
        summary = {"evidence_summary_schema_version": SUMMARY_VERSION, "checks_total": len(CHECKS),
                   "checks_covered": covered, "coverage_ratio": covered / len(CHECKS), "check_results": status}
        bundle = {"evidence_bundle_schema_version": EVIDENCE_VERSION, "recommendation_id": recommendation["recommendation_id"],
                  "source_hashes": {name: content_hash(frozen[name]) for name in sorted(frozen)},
                  "source_references": source_refs, "item_identifiers": copy.deepcopy(item_ids)}
        entry = {"recommendation_id": recommendation["recommendation_id"], "confidence_level": _level(covered, len(CHECKS), conflicts),
                 "evidence_summary": summary, "evidence_sources": sorted(name for name in SUPPORTED),
                 "missing_evidence": missing, "conflicting_evidence": sorted(set(conflicts)),
                 "degraded_providers": degraded, "freshness": freshness, "provenance_bundle": bundle}
        entry["deterministic_confidence_hash"] = content_hash(entry)
        entries.append(entry)
    report = {"confidence_report_schema_version": REPORT_VERSION, "advisory_only": True, "authority": "none",
              "read_only": True, "assessed_at": assessed_at, "metadata": {"confidence_metadata_schema_version": METADATA_VERSION,
              "policy_version": "wp4227-evidence-policy/v1", "classification_thresholds": {"very_high": "8/8 and no conflicts", "high": "6-7/8 and no conflicts", "moderate": "5/8 and no conflicts", "low": "3-4/8 or conflicts", "insufficient_evidence": "0-2/8"}},
              "assessments": entries}
    report["deterministic_content_hash"] = content_hash(report)
    return report


def validate_report(report: Any) -> list[str]:
    if not isinstance(report, dict): raise ConfidenceError("report must be an object")
    if report.get("confidence_report_schema_version") != REPORT_VERSION: raise ConfidenceError("unsupported confidence report schema")
    if report.get("advisory_only") is not True or report.get("authority") != "none" or report.get("read_only") is not True: raise ConfidenceError("authority boundary violated")
    copy_report = copy.deepcopy(report); actual = copy_report.pop("deterministic_content_hash", None)
    if actual != content_hash(copy_report): raise ConfidenceError("deterministic_content_hash mismatch")
    for entry in report.get("assessments", []):
        check = copy.deepcopy(entry); digest = check.pop("deterministic_confidence_hash", None)
        if digest != content_hash(check): raise ConfidenceError("deterministic_confidence_hash mismatch")
    return []


def explain(report: dict[str, Any], recommendation_id: str) -> dict[str, Any]:
    validate_report(report)
    for entry in report["assessments"]:
        if entry["recommendation_id"] == recommendation_id: return copy.deepcopy(entry)
    raise ConfidenceError(f"unknown recommendation_id: {recommendation_id}")


def compare(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    validate_report(left); validate_report(right)
    a = {x["recommendation_id"]: x for x in left["assessments"]}; b = {x["recommendation_id"]: x for x in right["assessments"]}
    return {"read_only": True, "added": sorted(set(b)-set(a)), "removed": sorted(set(a)-set(b)),
            "changed": sorted(k for k in set(a)&set(b) if a[k] != b[k])}


def history(reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for report in reports: validate_report(report)
    return sorted(({"assessed_at": r["assessed_at"], "deterministic_content_hash": r["deterministic_content_hash"], "assessment_count": len(r["assessments"])} for r in reports), key=lambda x:(x["assessed_at"], x["deterministic_content_hash"]))
