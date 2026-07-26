"""Deterministic measurements over published WP-4220--WP-4224 records.

The module deliberately has no writers or operational adapters. Callers supply time and
published records; results are new values whose hashes exclude no semantic fields.
"""
from __future__ import annotations

import copy
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from typing import Any

SNAPSHOT_VERSION = "estate.engineering-campaign-analytics/v1"
TREND_VERSION = "estate.engineering-campaign-trend/v1"
COMPARISON_VERSION = "estate.engineering-campaign-comparison/v1"
METRIC_VERSION = "wp4225-metrics/v1"
LEDGER_VERSION = "estate.engineering-recommendation-ledger/v1"
PERIODS = {"daily": 1, "weekly": 7, "monthly": 30, "campaign_lifetime": None}
RATE_STATES = {"acceptance_rate": "accepted_for_future_planning", "deferral_rate": "deferred", "rejection_rate": "rejected"}


class AnalyticsError(ValueError):
    """Published history violates the analytics input contract."""


def _canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _hashed(value: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(value)
    result["deterministic_content_hash"] = digest(result)
    return result


def _without_hash(value: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(value)
    result.pop("deterministic_content_hash", None)
    return result


def _time(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError) as exc:
        raise AnalyticsError(f"invalid timestamp: {value!r}") from exc
    if parsed.tzinfo is None:
        raise AnalyticsError("timestamps require an offset")
    return parsed.astimezone(timezone.utc)


def _validate_observation(row: Any) -> None:
    if not isinstance(row, dict) or not isinstance(row.get("observed_at"), str):
        raise AnalyticsError("each observation requires observed_at")
    _time(row["observed_at"])
    sources = row.get("sources")
    if not isinstance(sources, dict) or set(sources) != {"queue", "dashboard", "integration", "recommendations", "decision_ledger"}:
        raise AnalyticsError("sources must contain exactly WP-4220 through WP-4224 published outputs")
    ledger = sources["decision_ledger"]
    if not isinstance(ledger, dict) or ledger.get("ledger_schema_version") != LEDGER_VERSION:
        raise AnalyticsError("unsupported ledger_schema_version")
    for name, value in sources.items():
        if not isinstance(value, dict) or not isinstance(value.get("deterministic_content_hash"), str):
            raise AnalyticsError(f"{name} requires deterministic_content_hash")


def _records(panel: Any) -> list[dict[str, Any]]:
    return panel.get("records", []) if isinstance(panel, dict) and isinstance(panel.get("records", []), list) else []


def _metrics(row: dict[str, Any]) -> dict[str, Any]:
    sources = row["sources"]
    ledger = sources["decision_ledger"]
    recommendations = ledger.get("recommendations", [])
    latest = {r.get("recommendation_identifier"): "generated" for r in recommendations}
    decision_times: dict[str, datetime] = {}
    for decision in ledger.get("decisions", []):
        identifier = decision.get("linked_recommendation")
        latest[identifier] = decision.get("state")
        if isinstance(decision.get("review_timestamp"), str):
            decision_times[identifier] = _time(decision["review_timestamp"])
    total = len(recommendations)
    observed = _time(row["observed_at"])
    ages = []
    for rec in recommendations:
        created = rec.get("generation_timestamp")
        if isinstance(created, str) and created != "unspecified":
            end = decision_times.get(rec.get("recommendation_identifier"), observed)
            ages.append(max(0.0, (end - _time(created)).total_seconds() / 86400))
    dashboard = sources["dashboard"].get("dashboard_snapshot", sources["dashboard"])
    panels = dashboard.get("panels", {}) if isinstance(dashboard, dict) else {}
    queue = sources["queue"]
    candidates = queue.get("candidates", queue.get("items", []))
    if not isinstance(candidates, list): candidates = []
    completed = _records(panels.get("completed_work"))
    validation = _records(panels.get("validation_status"))
    merge = _records(panels.get("merge_risk"))
    all_items = candidates or _records(panels.get("execution_queue"))
    lane_counts = Counter((i.get("engineering_lane") or {}).get("primary", "unspecified") for i in all_items)
    blockers = sum(bool(i.get("blockers")) for i in all_items) or len(_records(panels.get("blocked_work")))
    deps = sum(len(i.get("dependencies", [])) for i in all_items)
    stale = sum("stale" in i.get("diagnostics", []) or i.get("freshness") == "stale" for i in all_items)
    high_risk = sum(i.get("merge_risk_classification") == "high" for i in (merge or all_items))
    debt = sum(i.get("source_category") == "technical_debt" or "technical_debt" in i.get("diagnostics", []) for i in all_items)
    merges = sum(i.get("current_lifecycle_state") in {"merged", "completed"} for i in completed or all_items)
    validated = sum(i.get("evidence_completeness") == "complete" or i.get("status") in {"complete", "passed"} for i in validation or completed)
    return {
        **{name: round(sum(state == wanted for state in latest.values()) / total, 6) if total else 0.0 for name, wanted in RATE_STATES.items()},
        "recommendation_aging_days": round(sum(ages) / len(ages), 6) if ages else 0.0,
        "engineering_throughput": merges, "merge_cadence": merges,
        "validation_completion_rate": round(validated / len(validation or completed), 6) if (validation or completed) else 0.0,
        "blocker_frequency": round(blockers / len(all_items), 6) if all_items else 0.0,
        "dependency_count": deps, "stale_work_rate": round(stale / len(all_items), 6) if all_items else 0.0,
        "queue_stability": 1.0, "engineering_lane_utilization": dict(sorted(lane_counts.items())),
        "high_merge_risk_rate": round(high_risk / len(merge or all_items), 6) if (merge or all_items) else 0.0,
        "technical_debt_rate": round(debt / len(all_items), 6) if all_items else 0.0,
    }


def generate_snapshot(observation: dict[str, Any], *, generated_at: str) -> dict[str, Any]:
    """Measure one immutable observation without mutating or reinterpreting its sources."""
    _validate_observation(observation); _time(generated_at)
    revisions = {name: value["deterministic_content_hash"] for name, value in sorted(observation["sources"].items())}
    logical = {"analytics_schema_version": SNAPSHOT_VERSION, "snapshot_identifier": "pending",
               "generation_timestamp": generated_at, "source_revisions": revisions,
               "provenance": {"observation_timestamp": observation["observed_at"], "source_names": list(revisions)},
               "metric_versions": {name: METRIC_VERSION for name in sorted(_metrics(observation))},
               "confidence": "high", "freshness": "fresh", "advisory_only": True, "authority": "none",
               "metrics": _metrics(observation)}
    logical["snapshot_identifier"] = digest(logical)[:20]
    return _hashed(logical)


def validate_snapshot(snapshot: Any) -> list[str]:
    if not isinstance(snapshot, dict) or snapshot.get("analytics_schema_version") != SNAPSHOT_VERSION:
        raise AnalyticsError("unsupported analytics_schema_version")
    if snapshot.get("deterministic_content_hash") != digest(_without_hash(snapshot)):
        raise AnalyticsError("analytics deterministic_content_hash mismatch")
    if snapshot.get("authority") != "none" or snapshot.get("advisory_only") is not True:
        raise AnalyticsError("analytics must be advisory and authority-free")
    return []


def trend(snapshots: list[dict[str, Any]], period: str) -> dict[str, Any]:
    if period not in PERIODS: raise AnalyticsError(f"unsupported period: {period}")
    for item in snapshots: validate_snapshot(item)
    ordered = sorted(snapshots, key=lambda x: (x["generation_timestamp"], x["snapshot_identifier"]))
    if ordered and PERIODS[period] is not None:
        cutoff = _time(ordered[-1]["generation_timestamp"]).timestamp() - PERIODS[period] * 86400
        ordered = [x for x in ordered if _time(x["generation_timestamp"]).timestamp() >= cutoff]
    numeric = sorted(k for k, v in (ordered[0]["metrics"] if ordered else {}).items() if isinstance(v, (int, float)) and not isinstance(v, bool))
    values = {k: {"first": ordered[0]["metrics"][k], "last": ordered[-1]["metrics"][k],
                  "change": round(ordered[-1]["metrics"][k] - ordered[0]["metrics"][k], 6)} for k in numeric} if ordered else {}
    return _hashed({"trend_schema_version": TREND_VERSION, "period": period, "sample_count": len(ordered),
                    "snapshot_identifiers": [x["snapshot_identifier"] for x in ordered], "metrics": values,
                    "provenance": [x["deterministic_content_hash"] for x in ordered]})


def compare(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    validate_snapshot(left); validate_snapshot(right)
    keys = sorted(set(left["metrics"]) & set(right["metrics"]))
    changes = {k: round(right["metrics"][k] - left["metrics"][k], 6) for k in keys
               if isinstance(left["metrics"][k], (int, float)) and isinstance(right["metrics"][k], (int, float))}
    return _hashed({"comparison_schema_version": COMPARISON_VERSION, "left_snapshot": left["snapshot_identifier"],
                    "right_snapshot": right["snapshot_identifier"], "metric_changes": changes,
                    "provenance": [left["deterministic_content_hash"], right["deterministic_content_hash"]]})


def history(snapshots: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for item in snapshots: validate_snapshot(item)
    return copy.deepcopy(sorted(snapshots, key=lambda x: (x["generation_timestamp"], x["snapshot_identifier"])))


def explain(snapshot: dict[str, Any], metric: str | None = None) -> dict[str, Any]:
    validate_snapshot(snapshot)
    if metric is not None and metric not in snapshot["metrics"]: raise AnalyticsError(f"unknown metric: {metric}")
    names = [metric] if metric else sorted(snapshot["metrics"])
    return {"snapshot_identifier": snapshot["snapshot_identifier"], "metrics": {n: {"value": snapshot["metrics"][n],
            "metric_version": snapshot["metric_versions"][n], "source_revisions": snapshot["source_revisions"]} for n in names}}
