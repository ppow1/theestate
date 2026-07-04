"""Lightweight validation observation log support.

Validation observations preserve follow-up findings without treating them as
confirmed defects or automatically creating work packages.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from estate.core.paths import ESTATE_ROOT

OBSERVATION_DIR = Path("validation/observations")
JSONL_NAME = "validation_observations.jsonl"
MARKDOWN_NAME = "validation_observations.md"

SEVERITIES = {"info", "follow-up", "defect-candidate", "confirmed-defect"}
STATUSES = {"open", "investigating", "accepted", "deferred", "converted-to-work-package", "closed"}
REQUIRED_FIELDS = {
    "observation_id",
    "related_work_package",
    "observed_behavior",
    "expected_behavior",
    "source_of_observation",
    "severity",
    "status",
    "recommended_next_action",
    "linked_follow_up_work_package",
    "timestamp",
}


def _base(root: str | Path | None = None) -> Path:
    if root is not None:
        return Path(root)
    return ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd()


def observation_paths(root: str | Path | None = None) -> dict[str, Path]:
    base = _base(root)
    return {
        "directory": base / OBSERVATION_DIR,
        "jsonl": base / OBSERVATION_DIR / JSONL_NAME,
        "markdown": base / OBSERVATION_DIR / MARKDOWN_NAME,
    }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def ensure_observation_log(root: str | Path | None = None) -> dict[str, Path]:
    paths = observation_paths(root)
    paths["directory"].mkdir(parents=True, exist_ok=True)
    paths["jsonl"].touch(exist_ok=True)
    if not paths["markdown"].exists():
        write_markdown_log([], root=root)
    return paths


def normalize_observation(observation: dict[str, Any]) -> dict[str, Any]:
    record = {field: observation.get(field) for field in REQUIRED_FIELDS}
    record["observation_id"] = str(record.get("observation_id") or "").strip()
    record["related_work_package"] = str(record.get("related_work_package") or "").strip() or None
    record["observed_behavior"] = str(record.get("observed_behavior") or "").strip()
    record["expected_behavior"] = str(record.get("expected_behavior") or "").strip() or None
    record["source_of_observation"] = str(record.get("source_of_observation") or "").strip()
    record["severity"] = str(record.get("severity") or "follow-up").strip()
    record["status"] = str(record.get("status") or "open").strip()
    record["recommended_next_action"] = str(record.get("recommended_next_action") or "").strip()
    record["linked_follow_up_work_package"] = str(record.get("linked_follow_up_work_package") or "").strip() or None
    record["timestamp"] = str(record.get("timestamp") or _now()).strip()

    if not record["observation_id"]:
        raise ValueError("observation_id is required")
    if not record["observed_behavior"]:
        raise ValueError("observed_behavior is required")
    if not record["source_of_observation"]:
        raise ValueError("source_of_observation is required")
    if record["severity"] not in SEVERITIES:
        raise ValueError(f"severity must be one of: {', '.join(sorted(SEVERITIES))}")
    if record["status"] not in STATUSES:
        raise ValueError(f"status must be one of: {', '.join(sorted(STATUSES))}")
    return record


def load_observations(root: str | Path | None = None) -> list[dict[str, Any]]:
    paths = ensure_observation_log(root)
    observations: list[dict[str, Any]] = []
    for line_number, line in enumerate(paths["jsonl"].read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSONL at line {line_number}: {exc}") from exc
        observations.append(normalize_observation(payload))
    return observations


def write_observations(observations: Iterable[dict[str, Any]], root: str | Path | None = None) -> dict[str, Path]:
    paths = ensure_observation_log(root)
    records = [normalize_observation(item) for item in observations]
    text = "".join(json.dumps(record, sort_keys=True) + "\n" for record in records)
    paths["jsonl"].write_text(text, encoding="utf-8")
    write_markdown_log(records, root=root)
    return paths


def append_observation(observation: dict[str, Any], root: str | Path | None = None) -> dict[str, Any]:
    observations = load_observations(root)
    record = normalize_observation(observation)
    if any(item["observation_id"] == record["observation_id"] for item in observations):
        raise ValueError(f"Observation already exists: {record['observation_id']}")
    observations.append(record)
    write_observations(observations, root=root)
    return record


def update_observation_status(observation_id: str, status: str, root: str | Path | None = None, linked_follow_up_work_package: str | None = None) -> dict[str, Any]:
    if status not in STATUSES:
        raise ValueError(f"status must be one of: {', '.join(sorted(STATUSES))}")
    observations = load_observations(root)
    for record in observations:
        if record["observation_id"] == observation_id:
            record["status"] = status
            if linked_follow_up_work_package is not None:
                record["linked_follow_up_work_package"] = linked_follow_up_work_package or None
            write_observations(observations, root=root)
            return record
    raise ValueError(f"Observation not found: {observation_id}")


def render_markdown_log(observations: Iterable[dict[str, Any]]) -> str:
    records = list(observations)
    lines = [
        "# Validation Observation Log",
        "",
        "Validation observations preserve findings for review. They are not confirmed defects and do not automatically create work packages.",
        "",
    ]
    if not records:
        lines.append("No validation observations recorded.")
        lines.append("")
        return "\n".join(lines)
    lines.extend(["| ID | Related WP | Severity | Status | Observed Behavior | Expected Behavior | Source | Recommended Next Action | Follow-up WP | Timestamp |", "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"])
    for record in records:
        values = [
            record["observation_id"], record.get("related_work_package") or "—", record["severity"], record["status"],
            record["observed_behavior"], record.get("expected_behavior") or "—", record["source_of_observation"],
            record["recommended_next_action"], record.get("linked_follow_up_work_package") or "—", record["timestamp"],
        ]
        lines.append("| " + " | ".join(str(value).replace("|", "\\|").replace("\n", " ") for value in values) + " |")
    lines.append("")
    return "\n".join(lines)


def write_markdown_log(observations: Iterable[dict[str, Any]], root: str | Path | None = None) -> Path:
    paths = observation_paths(root)
    paths["directory"].mkdir(parents=True, exist_ok=True)
    paths["markdown"].write_text(render_markdown_log(observations), encoding="utf-8")
    return paths["markdown"]
