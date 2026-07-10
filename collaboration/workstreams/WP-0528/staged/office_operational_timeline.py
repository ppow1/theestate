from __future__ import annotations

import copy
import csv
import io
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

SCHEMA = "estate.office_operational_timeline.v1"
EVENT_TYPES = {
    "merge",
    "validation",
    "decision",
    "resident_duty",
    "office_action",
    "provider_result",
    "operational_event",
}
OUTCOMES = {"passed", "failed", "completed", "blocked", "pending", "accepted", "rejected", "unknown"}


@dataclass(frozen=True)
class TimelineEvent:
    id: str
    occurred_at: str
    event_type: str
    title: str
    source_type: str
    evidence_path: str
    actor: str | None = None
    package: str | None = None
    project: str | None = None
    office: str | None = None
    outcome: str = "unknown"
    correlation_id: str | None = None
    canonical_artifact: str | None = None
    summary: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _parse_dt(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def _normalize_event(raw: TimelineEvent | Mapping[str, Any], *, root: Path, stale_after_days: int) -> tuple[dict[str, Any] | None, list[str]]:
    event = raw if isinstance(raw, TimelineEvent) else TimelineEvent(**raw)
    warnings: list[str] = []
    occurred = _parse_dt(event.occurred_at)
    malformed = occurred is None or not event.evidence_path or event.event_type not in EVENT_TYPES
    evidence = root / event.evidence_path if event.evidence_path else None
    missing = evidence is None or not evidence.exists()
    if malformed:
        warnings.append(f"malformed evidence: {event.id}")
    if missing:
        warnings.append(f"missing evidence: {event.id}")
    duplicate_key = f"{event.occurred_at}|{event.event_type}|{event.source_type}|{event.evidence_path}|{event.title}"
    age_days = None
    stale = False
    if occurred is not None:
        age_days = (datetime.now(timezone.utc) - occurred.astimezone(timezone.utc)).days
        stale = age_days > stale_after_days
    indicators = {
        "freshness": "malformed" if occurred is None else ("stale" if stale else "fresh"),
        "age_days": age_days,
        "evidence_exists": not missing,
        "malformed_evidence": malformed,
        "duplicate": False,
        "gap_after_previous_days": None,
    }
    return {
        "id": event.id,
        "occurred_at": event.occurred_at,
        "event_type": event.event_type,
        "title": event.title,
        "source": {"type": event.source_type, "evidence_path": event.evidence_path},
        "actor": event.actor,
        "package": event.package,
        "project": event.project,
        "office": event.office,
        "outcome": event.outcome if event.outcome in OUTCOMES else "unknown",
        "correlation_id": event.correlation_id,
        "canonical_artifact": event.canonical_artifact or event.evidence_path,
        "summary": event.summary,
        "metadata": copy.deepcopy(dict(event.metadata)),
        "indicators": indicators,
        "_dt": occurred,
        "_duplicate_key": duplicate_key,
    }, warnings


def build_timeline(events: Iterable[TimelineEvent | Mapping[str, Any]], *, root: str | Path = ".", stale_after_days: int = 30) -> dict[str, Any]:
    base = Path(root)
    normalized: list[dict[str, Any]] = []
    warnings: list[str] = []
    seen: set[str] = set()
    for raw in events:
        item, item_warnings = _normalize_event(raw, root=base, stale_after_days=stale_after_days)
        warnings.extend(item_warnings)
        if item is None:
            continue
        if item["_duplicate_key"] in seen:
            item["indicators"]["duplicate"] = True
            warnings.append(f"duplicate suppressed: {item['id']}")
            continue
        seen.add(item["_duplicate_key"])
        normalized.append(item)
    normalized.sort(key=lambda item: (item["_dt"] is None, item["_dt"] or datetime.max.replace(tzinfo=timezone.utc), item["event_type"], item["id"]))
    previous = None
    for item in normalized:
        if previous is not None and item["_dt"] is not None and previous["_dt"] is not None:
            gap = (item["_dt"] - previous["_dt"]).days
            item["indicators"]["gap_after_previous_days"] = gap if gap > 1 else None
        previous = item
    for item in normalized:
        del item["_dt"]
        del item["_duplicate_key"]
    return {"schema": SCHEMA, "staged_not_installed": True, "generated_at": utc_now(), "count": len(normalized), "events": normalized, "warnings": warnings}


def filter_timeline(timeline: Mapping[str, Any], **filters: Any) -> dict[str, Any]:
    allowed = {key: value for key, value in filters.items() if value not in (None, "", [])}
    start = _parse_dt(str(allowed.pop("date_from"))) if "date_from" in allowed else None
    end = _parse_dt(str(allowed.pop("date_to"))) if "date_to" in allowed else None
    result = []
    for event in timeline.get("events", []):
        occurred = _parse_dt(event.get("occurred_at", ""))
        if start and (occurred is None or occurred < start):
            continue
        if end and (occurred is None or occurred > end):
            continue
        if any(event.get(key) != value for key, value in allowed.items()):
            continue
        result.append(copy.deepcopy(event))
    output = copy.deepcopy(dict(timeline))
    output["events"] = result
    output["count"] = len(result)
    output["filters"] = filters
    return output


def correlate_timeline(timeline: Mapping[str, Any]) -> dict[str, Any]:
    groups: dict[str, list[str]] = {}
    for event in timeline.get("events", []):
        key = event.get("correlation_id") or event.get("package") or event.get("project") or event["id"]
        groups.setdefault(key, []).append(event["id"])
    return {"schema": SCHEMA, "staged_not_installed": True, "correlations": groups}


def export_timeline(timeline: Mapping[str, Any], *, format: str = "json") -> str:
    events: Sequence[Mapping[str, Any]] = timeline.get("events", [])
    if format == "json":
        import json

        return json.dumps({"schema": timeline.get("schema", SCHEMA), "events": list(events)}, indent=2, sort_keys=True)
    if format != "csv":
        raise ValueError("format must be json or csv")
    out = io.StringIO()
    fields = ["id", "occurred_at", "event_type", "actor", "package", "project", "office", "outcome", "title", "evidence_path"]
    writer = csv.DictWriter(out, fieldnames=fields)
    writer.writeheader()
    for event in events:
        row = {field: event.get(field, "") for field in fields}
        row["evidence_path"] = event.get("source", {}).get("evidence_path", "")
        writer.writerow(row)
    return out.getvalue()
