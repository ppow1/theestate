"""Pure projection of a WP-4220 queue; never discovers or mutates source authority."""
from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any

QUEUE_VERSION = "estate.engineering-queue/v1"
SNAPSHOT_VERSION = "estate.engineering-campaign-dashboard/v1"
PANEL_VERSION = "estate.engineering-campaign-panel/v1"
POLICY_VERSION = "wp4219-projection/v1"
PANEL_NAMES = (
    "executive_summary", "execution_queue", "ready_work", "blocked_work",
    "parallel_opportunities", "merge_risk", "repository_health", "parking_lot",
    "work_in_progress", "completed_work", "dependency_graph", "engineering_metrics",
    "validation_status", "recent_activity", "audit_history",
)

class DashboardError(ValueError):
    """The primary queue or generated snapshot violates the consumer contract."""

def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()

def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()

def validate_queue(queue: dict[str, Any]) -> None:
    required = {"queue_schema_version", "generation_identifier", "generation_timestamp", "source_revision", "rows", "deterministic_content_hash", "advisory_only"}
    if not isinstance(queue, dict) or required - queue.keys():
        raise DashboardError("invalid primary queue: required fields are missing")
    if queue["queue_schema_version"] != QUEUE_VERSION:
        raise DashboardError(f"unsupported queue schema version: {queue['queue_schema_version']}")
    if queue["advisory_only"] is not True or not isinstance(queue["rows"], list):
        raise DashboardError("invalid primary queue authority or rows")
    ids = [r.get("item_identifier") for r in queue["rows"]]
    if None in ids or len(ids) != len(set(ids)):
        raise DashboardError("duplicate or missing source identifiers")
    for row in queue["rows"]:
        for field in ("provenance", "readiness_classification", "reconciliation_classification", "priority", "dependencies", "blockers"):
            if field not in row:
                raise DashboardError(f"invalid queue row {row.get('item_identifier')}: missing {field}")

def _freshness(queue: dict[str, Any], as_of: str) -> str:
    try:
        generated = datetime.fromisoformat(queue["generation_timestamp"].replace("Z", "+00:00"))
        observed = datetime.fromisoformat(as_of.replace("Z", "+00:00"))
        age = (observed - generated).total_seconds()
    except (TypeError, ValueError):
        return "unavailable"
    if age < 0: return "source_mismatch"
    if age <= 86400: return "fresh"
    if age <= 259200: return "aging"
    return "stale"

def _provider_state(rows: list[dict[str, Any]]) -> dict[str, dict[str, str]]:
    checks = {
        "wp4214_duration": any(r.get("duration_estimate_reference") for r in rows),
        "wp4215_parallel": any(r.get("parallel_group") for r in rows),
        "wp4217_git": any(r.get("git_readiness_reference") for r in rows),
    }
    result = {"wp4220_queue": {"status": "available", "reason": "compatible_primary_queue"}}
    result.update({k: {"status": "available" if v else "unavailable", "reason": "referenced_by_queue" if v else "no_provider_reference"} for k, v in checks.items()})
    result["governed_activity"] = {"status": "unavailable", "reason": "not_published_by_wp4220_v1"}
    result["governed_audit"] = {"status": "unavailable", "reason": "no_predecessor_or_audit_provider"}
    return result

def _cycles(rows: list[dict[str, Any]]) -> list[list[str]]:
    graph = {r["item_identifier"]: sorted(r["dependencies"]) for r in rows}
    found: set[tuple[str, ...]] = set()
    def walk(node: str, trail: list[str]) -> None:
        if node in trail:
            cycle = trail[trail.index(node):]
            rotations = [tuple(cycle[i:] + cycle[:i]) for i in range(len(cycle))]
            found.add(min(rotations)); return
        for nxt in graph.get(node, []): walk(nxt, trail + [node])
    for node in sorted(graph): walk(node, [])
    return [list(x) for x in sorted(found)]

def _panel(name: str, records: list[Any], source_ids: list[str], freshness: str, degradation: str = "none", reason: str | None = None) -> dict[str, Any]:
    state = "unavailable" if degradation == "unavailable" else "empty" if not records else "populated"
    return {"panel_schema_version": PANEL_VERSION, "panel_id": name, "state": state, "freshness": freshness, "degradation": degradation, "degradation_reason": reason, "source_record_ids": sorted(set(source_ids)), "provenance": {"provider": "WP-4220", "renderer_rule": f"{POLICY_VERSION}:{name}"}, "records": records}

def _metric(metric_id: str, value: Any, source_ids: list[str], unavailable: str | None = None, denominator: int | None = None) -> dict[str, Any]:
    return {"metric_id": metric_id, "calculation_version": "wp4219-metrics/v1", "calculation_window": None, "value": value if unavailable is None else None, "unit": "count", "denominator": denominator, "source": "WP-4220 queue" if unavailable is None else None, "source_record_ids": sorted(source_ids), "status": "known" if unavailable is None else "unavailable", "unavailable_reason": unavailable, "evidence_completeness": "complete" if unavailable is None else "missing"}

def build_snapshot(queue: dict[str, Any], generated_at: str = "1970-01-01T00:00:00Z", as_of: str | None = None) -> dict[str, Any]:
    """Build an immutable logical view. ``generated_at`` is envelope-only and unhashed."""
    validate_queue(queue)
    rows = sorted(queue["rows"], key=lambda r: (-r["priority"]["score"], r["item_identifier"]))
    ids = [r["item_identifier"] for r in rows]
    by_id = {r["item_identifier"]: r for r in rows}
    freshness = _freshness(queue, as_of or queue["generation_timestamp"])
    providers = _provider_state(rows)
    ready = [r for r in rows if r["readiness_classification"] in {"ready", "ready_with_coordination"}]
    blocked = [r for r in rows if r["readiness_classification"] == "blocked"]
    completed = [r for r in rows if r["reconciliation_classification"] == "implemented_and_complete"]
    wip = [r for r in rows if r["readiness_classification"] in {"in_progress", "validation"}]
    parking = [r for r in rows if r["source_category"] == "parking_lot"]
    risks = [r for r in rows if r["merge_risk_classification"] in {"high", "critical"}]
    cycles = _cycles(rows)
    parallel_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        if r.get("parallel_group"): parallel_groups[r["parallel_group"]].append(r)
    parallel = [{"grouping_identifier": group, "included_work_items": sorted(x["item_identifier"] for x in members), "engineering_lanes": sorted(set(x["engineering_lane"]["primary"] for x in members)), "repository_touch_points": sorted(set(p for x in members for p in x["repository_touch_points"])), "shared_file_exposure": sorted(p for p, count in Counter(p for x in members for p in x["repository_touch_points"]).items() if count > 1), "merge_risk": max((x["merge_risk_classification"] for x in members), default="unknown"), "dependency_constraints": sorted(set(d for x in members for d in x["dependencies"])), "confidence": "provider_asserted", "exclusion_reasons": [], "advisory_only": True} for group, members in sorted(parallel_groups.items())]
    graph = {"nodes": [{"id": r["item_identifier"], "classification": r["reconciliation_classification"], "completed": r in completed, "superseded": r["reconciliation_classification"] == "superseded"} for r in sorted(rows, key=lambda x:x["item_identifier"])], "directed_edges": sorted([{"from": r["item_identifier"], "to": dep} for r in rows for dep in r["dependencies"]], key=lambda x:(x["from"],x["to"])), "missing_dependencies": sorted(set(dep for r in rows for dep in r["dependencies"] if dep not in by_id)), "blocked_dependencies": sorted(set(dep for r in blocked for dep in r["dependencies"])), "dependency_cycles": cycles, "critical_path_hints": None, "critical_path_reason": "not supplied by WP-4220 v1"}
    validation_missing = [r for r in rows if r["evidence_completeness"] != "complete" and r["readiness_classification"] == "validation"]
    summary = {"total_queued_work": len(rows), "ready_work": len(ready), "blocked_work": len(blocked), "active_or_assigned_work": len(wip), "stale_work": sum(r["reconciliation_classification"] == "stale" for r in rows), "high_merge_risk_work": len(risks), "parallel_safe_opportunities": len(parallel), "missing_validation": len(validation_missing), "dependency_cycles": len(cycles), "queue_freshness": freshness, "reconciliation_warnings": sum(bool(r["diagnostics"]) for r in rows), "provider_degradation": sorted(k for k,v in providers.items() if v["status"] != "available"), "highest_priority_next_ready_items": [r["item_identifier"] for r in ready[:5]], "advisory_only": True}
    metrics = [
        _metric("work_packages_authored", sum(r["source_category"] == "work_package" for r in rows), ids),
        _metric("work_packages_merged", len(completed), [r["item_identifier"] for r in completed]),
        _metric("validation_progress", len(completed), ids, denominator=len(rows)),
        _metric("average_implementation_duration", None, [], "WP-4214 actual duration values are references only"),
        _metric("estimated_completion", None, [], "no compatible campaign estimate range"),
        _metric("queue_age", None, [], "WP-4220 v1 does not publish promotion timestamps"),
        _metric("stale_work", summary["stale_work"], ids), _metric("blocked_work", len(blocked), [r["item_identifier"] for r in blocked]),
        _metric("lane_utilization", None, [], "WP-4215 capacity is not published in queue v1"),
        _metric("merge_conflict_exposure", len(risks), [r["item_identifier"] for r in risks]),
    ]
    panels = {
        "executive_summary": _panel("executive_summary", [summary], ids, freshness),
        "execution_queue": _panel("execution_queue", rows, ids, freshness),
        "ready_work": _panel("ready_work", ready, [r["item_identifier"] for r in ready], freshness),
        "blocked_work": _panel("blocked_work", blocked, [r["item_identifier"] for r in blocked], freshness),
        "parallel_opportunities": _panel("parallel_opportunities", parallel, [x for g in parallel for x in g["included_work_items"]], freshness, "none" if providers["wp4215_parallel"]["status"] == "available" else "unavailable", providers["wp4215_parallel"]["reason"]),
        "merge_risk": _panel("merge_risk", risks, [r["item_identifier"] for r in risks], freshness, "partial" if providers["wp4217_git"]["status"] != "available" else "none", "Git enrichment unavailable" if providers["wp4217_git"]["status"] != "available" else None),
        "repository_health": _panel("repository_health", [], [], freshness, "unavailable", providers["wp4217_git"]["reason"]),
        "parking_lot": _panel("parking_lot", parking, [r["item_identifier"] for r in parking], freshness),
        "work_in_progress": _panel("work_in_progress", wip, [r["item_identifier"] for r in wip], freshness),
        "completed_work": _panel("completed_work", completed, [r["item_identifier"] for r in completed], freshness),
        "dependency_graph": _panel("dependency_graph", [graph], ids, freshness),
        "engineering_metrics": _panel("engineering_metrics", metrics, ids, freshness, "partial", "provider-limited metrics preserve unavailable values"),
        "validation_status": _panel("validation_status", [{"item_identifier": r["item_identifier"], "evidence_completeness": r["evidence_completeness"], "acceptance_inferred": False} for r in rows], ids, freshness),
        "recent_activity": _panel("recent_activity", [], [], freshness, "unavailable", providers["governed_activity"]["reason"]),
        "audit_history": _panel("audit_history", [], [], freshness, "unavailable", providers["governed_audit"]["reason"]),
    }
    degradation = "stale" if freshness == "stale" else "degraded" if any(v["status"] != "available" for v in providers.values()) else "none"
    logical = {"snapshot_schema_version": SNAPSHOT_VERSION, "source_queue_generation_identifier": queue["generation_identifier"], "source_revision": queue["source_revision"], "freshness_status": freshness, "degradation_status": degradation, "provider_availability": providers, "executive_summary": summary, "panel_index": list(PANEL_NAMES), "panels": panels, "campaign_health": "critical" if cycles else "attention" if blocked or risks else "healthy", "queue_health": "attention" if freshness != "fresh" else "healthy", "reconciliation_health": "attention" if summary["reconciliation_warnings"] else "healthy", "validation_health": "attention" if validation_missing else "unknown", "source_provenance": {"provider": "WP-4220", "generation_identifier": queue["generation_identifier"], "content_hash": queue["deterministic_content_hash"]}, "diagnostics": sorted(set(d for r in rows for d in r["diagnostics"])), "advisory_only": True}
    content_hash = digest(logical)
    snapshot = {**logical, "snapshot_identifier": content_hash[:20], "generation_time": generated_at, "deterministic_content_hash": content_hash}
    validate_snapshot(snapshot)
    return snapshot

def validate_snapshot(snapshot: dict[str, Any]) -> None:
    if snapshot.get("snapshot_schema_version") != SNAPSHOT_VERSION or snapshot.get("advisory_only") is not True:
        raise DashboardError("invalid dashboard snapshot")
    if tuple(snapshot.get("panel_index", ())) != PANEL_NAMES or set(snapshot.get("panels", {})) != set(PANEL_NAMES):
        raise DashboardError("dashboard panel set is incomplete")
    for name, panel in snapshot["panels"].items():
        if panel.get("panel_schema_version") != PANEL_VERSION or panel.get("panel_id") != name or not panel.get("provenance"):
            raise DashboardError(f"invalid panel: {name}")
    logical = {k:v for k,v in snapshot.items() if k not in {"snapshot_identifier", "generation_time", "deterministic_content_hash"}}
    expected = digest(logical)
    if snapshot.get("deterministic_content_hash") != expected or snapshot.get("snapshot_identifier") != expected[:20]:
        raise DashboardError("dashboard deterministic hash mismatch")

def operator_summary(snapshot: dict[str, Any]) -> str:
    validate_snapshot(snapshot); s = snapshot["executive_summary"]
    lines = ["# Engineering Campaign Operator Summary", "", f"Campaign health: **{snapshot['campaign_health']}**", f"Queue freshness: **{s['queue_freshness']}**", f"Next-ready work: {', '.join(s['highest_priority_next_ready_items']) or 'none'}", f"Blocked work: {s['blocked_work']}", f"Parallel opportunities: {s['parallel_safe_opportunities']}", f"High merge-risk warnings: {s['high_merge_risk_work']}", f"Validation gaps: {s['missing_validation']}", f"Provider degradations: {', '.join(s['provider_degradation']) or 'none'}", f"Required operator attention: {'review source diagnostics and provider gaps' if snapshot['degradation_status'] != 'none' else 'none'}", "", "> Advisory read-only projection; no assignment, acceptance, merge, or completion is inferred.", ""]
    return "\n".join(lines)
