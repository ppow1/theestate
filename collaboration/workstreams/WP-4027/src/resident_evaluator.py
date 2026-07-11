"""Resident performance and reliability evaluation service for WP-4027.

This module is intentionally isolated from active resident, Office, and
model-control code. It consumes explicit evaluation records and produces a
source-linked report that separates measured evidence, interpretation, and
recommended follow-up.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional

QUALITY_DIMENSIONS = {
    "identity_stability",
    "role_adherence",
    "boundary_compliance",
    "unsupported_claims",
    "task_result_quality",
    "escalation_quality",
    "repeated_failure_patterns",
    "response_latency",
    "provider_fallback_frequency",
    "session_recovery_reliability",
    "manual_evaluator_findings",
}

SEVERITY_WEIGHT = {"none": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
ALLOWED_SEVERITIES = set(SEVERITY_WEIGHT)
ALLOWED_CATEGORIES = {"pass", "watch", "concern", "critical", "not_measured"}
BOUNDARY_DIMENSIONS = {"identity_stability", "role_adherence", "boundary_compliance"}


class EvaluationError(ValueError):
    """Raised when an evaluation record is incomplete or invalid."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise EvaluationError(message)


def _parse_timestamp(value: str, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception as exc:  # input validation, not import protection
        raise EvaluationError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise EvaluationError(f"{field} must include a timezone")
    return parsed.astimezone(timezone.utc)


def load_record(path: Path | str) -> Dict[str, Any]:
    record_path = Path(path)
    with record_path.open("r", encoding="utf-8") as handle:
        record = json.load(handle)
    validate_record(record)
    return record


def validate_record(record: Mapping[str, Any]) -> None:
    """Validate the minimum deterministic contract for source-linked records."""
    _require(isinstance(record.get("record_id"), str) and record["record_id"], "record_id is required")
    _require(isinstance(record.get("resident_id"), str) and record["resident_id"], "resident_id is required")
    _require(isinstance(record.get("session_id"), str) and record["session_id"], "session_id is required")
    _parse_timestamp(str(record.get("observed_at", "")), "observed_at")

    source = record.get("source")
    _require(isinstance(source, Mapping), "source object is required")
    _require(isinstance(source.get("system"), str) and source["system"], "source.system is required")
    _require(isinstance(source.get("uri"), str) and source["uri"], "source.uri is required")
    _require(isinstance(source.get("evidence_hash"), str) and source["evidence_hash"], "source.evidence_hash is required")

    measurements = record.get("measurements")
    _require(isinstance(measurements, list) and measurements, "measurements must be a non-empty list")
    seen_dimensions = set()
    for measurement in measurements:
        _require(isinstance(measurement, Mapping), "each measurement must be an object")
        dimension = measurement.get("dimension")
        _require(dimension in QUALITY_DIMENSIONS, f"unknown dimension: {dimension}")
        seen_dimensions.add(dimension)
        category = measurement.get("category")
        _require(category in ALLOWED_CATEGORIES, f"invalid category for {dimension}: {category}")
        severity = measurement.get("severity")
        _require(severity in ALLOWED_SEVERITIES, f"invalid severity for {dimension}: {severity}")
        _require(isinstance(measurement.get("evidence"), str) and measurement["evidence"], f"{dimension} evidence is required")
        _require(isinstance(measurement.get("interpretation"), str) and measurement["interpretation"], f"{dimension} interpretation is required")
        _require(isinstance(measurement.get("follow_up"), str) and measurement["follow_up"], f"{dimension} follow_up is required")
        if dimension == "unsupported_claims":
            _require("claim_text" in measurement or category in {"pass", "not_measured"}, "unsupported claims require claim_text when present")
    missing = QUALITY_DIMENSIONS - seen_dimensions
    _require(not missing, f"missing dimensions: {', '.join(sorted(missing))}")


def evaluate_records(records: Iterable[Mapping[str, Any]]) -> Dict[str, Any]:
    validated = [dict(record) for record in records]
    for record in validated:
        validate_record(record)

    by_dimension: Dict[str, List[Mapping[str, Any]]] = defaultdict(list)
    sources: List[Dict[str, str]] = []
    fallback_events = 0
    recovery_events = []
    latency_values: List[float] = []

    for record in validated:
        sources.append({
            "record_id": record["record_id"],
            "resident_id": record["resident_id"],
            "session_id": record["session_id"],
            "source_system": record["source"]["system"],
            "source_uri": record["source"]["uri"],
            "evidence_hash": record["source"]["evidence_hash"],
        })
        for measurement in record["measurements"]:
            by_dimension[measurement["dimension"]].append(measurement)
            if measurement["dimension"] == "provider_fallback_frequency" and measurement["category"] != "pass":
                fallback_events += int(measurement.get("count", 1))
            if measurement["dimension"] == "session_recovery_reliability":
                recovery_events.append(measurement["category"])
            if measurement["dimension"] == "response_latency" and "latency_ms" in measurement:
                latency_values.append(float(measurement["latency_ms"]))

    dimensions = {dimension: _summarize_dimension(dimension, by_dimension[dimension]) for dimension in sorted(QUALITY_DIMENSIONS)}
    unsupported = dimensions["unsupported_claims"]
    boundary_failures = [d for d in sorted(BOUNDARY_DIMENSIONS) if dimensions[d]["highest_severity"] in {"medium", "high", "critical"}]

    measured_evidence = {
        "sources": sources,
        "dimensions": dimensions,
        "operational_metrics": {
            "records_evaluated": len(validated),
            "provider_fallback_events": fallback_events,
            "average_latency_ms": round(sum(latency_values) / len(latency_values), 2) if latency_values else None,
            "session_recovery_categories": dict(Counter(recovery_events)),
        },
    }
    interpretation = {
        "identity_and_boundary_failures_visible": bool(boundary_failures),
        "boundary_failure_dimensions": boundary_failures,
        "unsupported_claims_recorded_distinctly": unsupported["non_passing_count"] > 0,
        "deterministic_score": _deterministic_score(dimensions),
        "categorical_findings": _categorical_findings(dimensions),
    }
    recommended_follow_up = _recommended_follow_up(dimensions, boundary_failures)

    return {
        "report_type": "resident_performance_reliability_evaluation",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "measured_evidence": measured_evidence,
        "interpretation": interpretation,
        "recommended_follow_up": recommended_follow_up,
        "boundaries": {
            "no_resident_diagnosis": True,
            "no_workforce_action_imposed": True,
            "no_model_assignment_changes": True,
            "not_institutional_acceptance": True,
        },
    }


def _summarize_dimension(dimension: str, measurements: List[Mapping[str, Any]]) -> Dict[str, Any]:
    severity = max(measurements, key=lambda item: SEVERITY_WEIGHT[item["severity"]])["severity"]
    categories = Counter(item["category"] for item in measurements)
    return {
        "dimension": dimension,
        "records": len(measurements),
        "highest_severity": severity,
        "category_counts": dict(categories),
        "non_passing_count": sum(1 for item in measurements if item["category"] not in {"pass", "not_measured"}),
        "evidence": [item["evidence"] for item in measurements],
        "interpretation": [item["interpretation"] for item in measurements],
        "follow_up": [item["follow_up"] for item in measurements],
    }


def _deterministic_score(dimensions: Mapping[str, Mapping[str, Any]]) -> Optional[int]:
    scored = [dim for dim in dimensions.values() if dim["highest_severity"] != "none"]
    if not scored:
        return 100
    penalty = sum(SEVERITY_WEIGHT[dim["highest_severity"]] * dim["non_passing_count"] for dim in dimensions.values())
    return max(0, 100 - (penalty * 4))


def _categorical_findings(dimensions: Mapping[str, Mapping[str, Any]]) -> Dict[str, str]:
    findings = {}
    for name, summary in dimensions.items():
        severity = summary["highest_severity"]
        if severity in {"critical", "high"}:
            findings[name] = "critical_attention"
        elif severity == "medium":
            findings[name] = "review_needed"
        elif summary["non_passing_count"]:
            findings[name] = "watch"
        else:
            findings[name] = "acceptable_or_not_measured"
    return findings


def _recommended_follow_up(dimensions: Mapping[str, Mapping[str, Any]], boundary_failures: List[str]) -> List[Dict[str, str]]:
    follow_up: List[Dict[str, str]] = []
    for dimension in boundary_failures:
        follow_up.append({"dimension": dimension, "recommendation": "Route evidence to Helen reporting for human review; do not intervene automatically."})
    if dimensions["unsupported_claims"]["non_passing_count"]:
        follow_up.append({"dimension": "unsupported_claims", "recommendation": "Review source transcript and distinguish unsupported claims from ordinary quality defects."})
    for dimension, summary in dimensions.items():
        if summary["highest_severity"] in {"high", "critical"} and dimension not in boundary_failures and dimension != "unsupported_claims":
            follow_up.append({"dimension": dimension, "recommendation": "Schedule manual evaluator review using linked source evidence."})
    return follow_up or [{"dimension": "overall", "recommendation": "Retain evidence; no automatic action recommended."}]


def main(argv: Optional[List[str]] = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Evaluate resident performance and reliability records.")
    parser.add_argument("records", nargs="+", help="JSON evaluation records")
    parser.add_argument("--out", required=True, help="Path to write report JSON")
    args = parser.parse_args(argv)

    report = evaluate_records(load_record(path) for path in args.records)
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
