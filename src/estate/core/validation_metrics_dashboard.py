"""Validation metrics dashboard aggregation.

This module summarizes existing validation artifacts without changing their
results or becoming a source of truth for validation decisions.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from estate.core.paths import ESTATE_ROOT

JSON_OUTPUT = "runtime/validation/validation_metrics_dashboard.json"
MARKDOWN_OUTPUT = "operations/validation/validation_metrics_dashboard.md"
COMPLETIONS_DIR = Path("collaboration/work_packages/completions")


def _base(root: str | Path | None = None) -> Path:
    if root is not None:
        return Path(root)
    return ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _read_json(path: Path, warnings: list[dict[str, str]]) -> Any | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except json.JSONDecodeError as exc:
        warnings.append({"type": "invalid_json", "path": str(path), "message": f"Could not parse JSON: {exc.msg}"})
    except OSError as exc:
        warnings.append({"type": "read_error", "path": str(path), "message": str(exc)})
    return None


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _result_from_record(record: dict[str, Any]) -> str:
    text = " ".join(str(record.get(key) or "") for key in ("validation_result", "review_result", "result", "status", "known_limitations")).lower()
    if any(token in text for token in ("fail", "failed", "failure")):
        return "fail"
    if any(token in text for token in ("conditional pass", "conditionally passed", "warning", "limitation")):
        return "conditional_pass"
    if str(record.get("codex_status", "")).lower() in {"done", "completed"}:
        return "pass"
    return "unknown"


def _completion_timestamp(record: dict[str, Any], path: Path) -> str:
    value = record.get("completed_at") or record.get("timestamp") or record.get("generated_at")
    if value:
        return str(value)
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).date().isoformat()


def _aggregate_completion_records(root: Path, warnings: list[dict[str, str]]) -> tuple[list[dict[str, Any]], Counter, dict[str, int]]:
    rows: list[dict[str, Any]] = []
    counts: Counter = Counter()
    trend: dict[str, int] = defaultdict(int)
    directory = root / COMPLETIONS_DIR
    if not directory.exists():
        warnings.append({"type": "missing_artifact", "path": str(COMPLETIONS_DIR), "message": "No work package completion directory found."})
        return rows, counts, {}
    for path in sorted(directory.glob("*_done.json")):
        record = _read_json(path, warnings)
        if not isinstance(record, dict):
            continue
        result = _result_from_record(record)
        timestamp = _completion_timestamp(record, path)
        date = timestamp[:10] if len(timestamp) >= 10 else "unknown"
        counts[result] += 1
        trend[date] += 1
        rows.append({
            "work_package_id": record.get("work_package_id") or path.stem.replace("_codex_done", ""),
            "result": result,
            "completed_at": timestamp,
            "ready_for_ca_review": record.get("ready_for_ca_review"),
            "path": _rel(path, root),
        })
    return rows, counts, dict(sorted(trend.items()))


def _load_observations(root: Path, warnings: list[dict[str, str]]) -> list[dict[str, Any]]:
    path = root / "validation/observations/validation_observations.jsonl"
    if not path.exists():
        return []
    observations: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            warnings.append({"type": "invalid_observation", "path": f"{_rel(path, root)}:{line_number}", "message": exc.msg})
            continue
        if isinstance(payload, dict):
            observations.append(payload)
        else:
            warnings.append({"type": "invalid_observation", "path": f"{_rel(path, root)}:{line_number}", "message": "Observation record is not an object."})
    return observations


def generate_validation_metrics_dashboard(root: str | Path | None = None, write: bool = True) -> dict[str, Any]:
    base = _base(root)
    warnings: list[dict[str, str]] = []
    completions, result_counts, trend = _aggregate_completion_records(base, warnings)
    observations = _load_observations(base, warnings)
    open_observations = [o for o in observations if str(o.get("status") or "").lower() in {"open", "investigating", "accepted"}]
    confirmed_defects = [o for o in observations if str(o.get("severity") or "").lower() == "confirmed-defect"]
    deferred = [o for o in observations if str(o.get("status") or "").lower() == "deferred"]
    sources = [
        {"name": "work_package_completions", "path": str(COMPLETIONS_DIR), "available": (base / COMPLETIONS_DIR).exists()},
        {"name": "validation_observations", "path": "validation/observations/validation_observations.jsonl", "available": (base / "validation/observations/validation_observations.jsonl").exists()},
        {"name": "local_operational_validation", "path": "runtime/validation/local_operational_validation_run.json", "available": (base / "runtime/validation/local_operational_validation_run.json").exists()},
        {"name": "operational_validation", "path": "runtime/validation/operational_validation_report.json", "available": (base / "runtime/validation/operational_validation_report.json").exists()},
    ]
    payload = {
        "generated_at": _now(),
        "source_of_truth_boundary": "Dashboard reads existing validation artifacts and does not alter or replace validation results.",
        "summary": {
            "total_validated_work_packages": len(completions),
            "pass_count": result_counts.get("pass", 0),
            "conditional_pass_count": result_counts.get("conditional_pass", 0),
            "fail_count": result_counts.get("fail", 0),
            "unknown_result_count": result_counts.get("unknown", 0),
            "open_observation_count": len(open_observations),
            "confirmed_defect_count": len(confirmed_defects),
            "deferred_observation_count": len(deferred),
        },
        "validation_trend_over_time": [{"date": date, "validated_work_packages": count} for date, count in trend.items()],
        "work_packages": completions,
        "observations": {
            "open": open_observations,
            "confirmed_defects": confirmed_defects,
            "deferred": deferred,
        },
        "sources": sources,
        "warnings": warnings,
    }
    if write:
        (base / JSON_OUTPUT).parent.mkdir(parents=True, exist_ok=True)
        (base / MARKDOWN_OUTPUT).parent.mkdir(parents=True, exist_ok=True)
        (base / JSON_OUTPUT).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (base / MARKDOWN_OUTPUT).write_text(format_validation_metrics_dashboard(payload) + "\n", encoding="utf-8")
    return payload


def format_validation_metrics_dashboard(payload: dict[str, Any]) -> str:
    s = payload.get("summary", {})
    lines = ["# Validation Metrics Dashboard", "", payload.get("source_of_truth_boundary", ""), "", "## Summary"]
    for key in ("total_validated_work_packages", "pass_count", "conditional_pass_count", "fail_count", "open_observation_count", "confirmed_defect_count", "deferred_observation_count"):
        lines.append(f"- {key.replace('_', ' ').title()}: {s.get(key, 0)}")
    lines += ["", "## Validation Trend Over Time"]
    trend = payload.get("validation_trend_over_time") or []
    lines += [f"- {row.get('date')}: {row.get('validated_work_packages')} validated work package(s)" for row in trend] or ["- No validation trend data available yet."]
    lines += ["", "## Artifact Links"]
    for source in payload.get("sources", []):
        state = "available" if source.get("available") else "missing"
        lines.append(f"- {source.get('name')}: `{source.get('path')}` ({state})")
    if payload.get("warnings"):
        lines += ["", "## Warnings"] + [f"- {w.get('type')}: {w.get('message')}" for w in payload["warnings"]]
    return "\n".join(lines)


def format_validation_metrics_summary(payload: dict[str, Any]) -> str:
    s = payload.get("summary", {})
    return (
        "Validation Metrics Dashboard\n"
        f"Validated work packages: {s.get('total_validated_work_packages', 0)}\n"
        f"Pass / conditional / fail: {s.get('pass_count', 0)} / {s.get('conditional_pass_count', 0)} / {s.get('fail_count', 0)}\n"
        f"Open observations / confirmed defects / deferred: {s.get('open_observation_count', 0)} / {s.get('confirmed_defect_count', 0)} / {s.get('deferred_observation_count', 0)}\n"
        f"JSON: {JSON_OUTPUT}\nMarkdown: {MARKDOWN_OUTPUT}"
    )
