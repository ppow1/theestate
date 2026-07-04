"""Validation handoff artifact workflow.

This module creates a read-only handoff packet from existing validation
artifacts so reviewers can move from validation execution to follow-up review
without changing validation results or creating new governance records.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from estate.core.paths import ESTATE_ROOT

JSON_OUTPUT = "runtime/validation/validation_handoff_artifact_workflow.json"
MARKDOWN_OUTPUT = "operations/validation/validation_handoff_artifact_workflow.md"
METRICS_JSON = "runtime/validation/validation_metrics_dashboard.json"
OBSERVATIONS_JSONL = "validation/observations/validation_observations.jsonl"
COMPLETIONS_DIR = "collaboration/work_packages/completions"


def _base(root: str | Path | None = None) -> Path:
    if root is not None:
        return Path(root)
    return ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _read_json(path: Path, warnings: list[dict[str, str]]) -> Any | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except json.JSONDecodeError as exc:
        warnings.append({"type": "invalid_json", "path": str(path), "message": exc.msg})
    except OSError as exc:
        warnings.append({"type": "read_error", "path": str(path), "message": str(exc)})
    return None


def _load_observations(root: Path, warnings: list[dict[str, str]]) -> list[dict[str, Any]]:
    path = root / OBSERVATIONS_JSONL
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            warnings.append({"type": "invalid_observation", "path": f"{OBSERVATIONS_JSONL}:{line_number}", "message": exc.msg})
            continue
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def _latest_completions(root: Path, limit: int = 5) -> list[dict[str, Any]]:
    directory = root / COMPLETIONS_DIR
    if not directory.exists():
        return []
    rows: list[dict[str, Any]] = []
    for path in sorted(directory.glob("*_done.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        record = _read_json(path, [])
        if not isinstance(record, dict):
            continue
        rows.append({
            "work_package_id": record.get("work_package_id") or path.stem.replace("_codex_done", ""),
            "completed_at": record.get("completed_at") or record.get("timestamp") or record.get("generated_at"),
            "ready_for_ca_review": record.get("ready_for_ca_review"),
            "validation_result": record.get("validation_result") or record.get("review_result") or record.get("result"),
            "path": _rel(path, root),
        })
        if len(rows) >= limit:
            break
    return rows


def _source(root: Path, name: str, rel: str, source_type: str) -> dict[str, Any]:
    path = root / rel
    return {"name": name, "path": rel, "type": source_type, "available": path.exists()}


def generate_validation_handoff_artifact_workflow(root: str | Path | None = None, write: bool = True) -> dict[str, Any]:
    """Generate the validation handoff packet from existing validation artifacts."""
    base = _base(root)
    warnings: list[dict[str, str]] = []
    metrics = _read_json(base / METRICS_JSON, warnings)
    metrics_summary = metrics.get("summary", {}) if isinstance(metrics, dict) else {}
    observations = _load_observations(base, warnings)
    open_observations = [o for o in observations if str(o.get("status") or "").lower() in {"open", "investigating", "accepted"}]
    confirmed_defects = [o for o in observations if str(o.get("severity") or "").lower() == "confirmed-defect"]
    sources = [
        _source(base, "validation_metrics_dashboard", METRICS_JSON, "runtime_json"),
        _source(base, "validation_metrics_markdown", "operations/validation/validation_metrics_dashboard.md", "markdown"),
        _source(base, "validation_observations", OBSERVATIONS_JSONL, "jsonl"),
        _source(base, "local_operational_validation", "runtime/validation/local_operational_validation_run.json", "runtime_json"),
        _source(base, "operational_validation_report", "runtime/validation/operational_validation_report.json", "runtime_json"),
        _source(base, "work_package_completions", COMPLETIONS_DIR, "directory"),
    ]
    missing = [s for s in sources if not s["available"]]
    if not isinstance(metrics, dict):
        warnings.append({"type": "missing_artifact", "path": METRICS_JSON, "message": "Validation metrics dashboard is unavailable; handoff uses direct observations and completion records only."})
    recommended_next_action = "Review confirmed defects before closing validation handoff." if confirmed_defects else "Review open observations, then archive handoff with the relevant completion record."
    payload = {
        "generated_at": _now(),
        "workflow_id": "validation_handoff_artifact_workflow",
        "source_of_truth_boundary": "This handoff packet aggregates existing validation artifacts and does not alter validation results, observations, defects, or work package state.",
        "summary": {
            "state": "ready" if not missing else "partial",
            "available_source_count": len(sources) - len(missing),
            "missing_source_count": len(missing),
            "total_validated_work_packages": metrics_summary.get("total_validated_work_packages"),
            "pass_count": metrics_summary.get("pass_count"),
            "conditional_pass_count": metrics_summary.get("conditional_pass_count"),
            "fail_count": metrics_summary.get("fail_count"),
            "open_observation_count": len(open_observations),
            "confirmed_defect_count": len(confirmed_defects),
            "recommended_next_action": recommended_next_action,
        },
        "handoff_steps": [
            {"step": "collect", "description": "Collect current validation metrics, observations, and completion artifacts."},
            {"step": "review", "description": "Review open observations separately from confirmed defects."},
            {"step": "route", "description": "Link follow-up work packages only where an authoritative follow-up already exists."},
            {"step": "archive", "description": "Attach this handoff packet to the relevant completion or review record."},
        ],
        "latest_completion_artifacts": _latest_completions(base),
        "observations": {"open": open_observations, "confirmed_defects": confirmed_defects},
        "sources": sources,
        "warnings": warnings + [{"type": "missing_artifact", "path": s["path"], "message": "Source artifact is unavailable."} for s in missing],
    }
    if write:
        (base / JSON_OUTPUT).parent.mkdir(parents=True, exist_ok=True)
        (base / MARKDOWN_OUTPUT).parent.mkdir(parents=True, exist_ok=True)
        (base / JSON_OUTPUT).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (base / MARKDOWN_OUTPUT).write_text(format_validation_handoff_artifact_workflow(payload) + "\n", encoding="utf-8")
    return payload


def format_validation_handoff_artifact_workflow(payload: dict[str, Any]) -> str:
    summary = payload.get("summary", {})
    lines = ["# Validation Handoff Artifact Workflow", "", payload.get("source_of_truth_boundary", ""), "", "## Summary"]
    for key in ("state", "available_source_count", "missing_source_count", "total_validated_work_packages", "pass_count", "conditional_pass_count", "fail_count", "open_observation_count", "confirmed_defect_count", "recommended_next_action"):
        lines.append(f"- {key.replace('_', ' ').title()}: {summary.get(key, 'unavailable')}")
    lines += ["", "## Handoff Steps"]
    for step in payload.get("handoff_steps", []):
        lines.append(f"- {step.get('step')}: {step.get('description')}")
    lines += ["", "## Artifact Links"]
    for source in payload.get("sources", []):
        state = "available" if source.get("available") else "missing"
        lines.append(f"- {source.get('name')}: `{source.get('path')}` ({state})")
    lines += ["", "## Open Observations"]
    open_obs = payload.get("observations", {}).get("open", [])
    lines += [f"- {o.get('observation_id', 'unknown')}: {o.get('observed_behavior', '')}" for o in open_obs] or ["- None recorded."]
    lines += ["", "## Confirmed Defects"]
    defects = payload.get("observations", {}).get("confirmed_defects", [])
    lines += [f"- {o.get('observation_id', 'unknown')}: {o.get('observed_behavior', '')}" for o in defects] or ["- None recorded."]
    if payload.get("warnings"):
        lines += ["", "## Warnings"] + [f"- {w.get('type')}: {w.get('path')} — {w.get('message')}" for w in payload["warnings"]]
    return "\n".join(lines)


def format_validation_handoff_summary(payload: dict[str, Any]) -> str:
    summary = payload.get("summary", {})
    return (
        "Validation Handoff Artifact Workflow\n"
        f"State: {summary.get('state')}\n"
        f"Open observations / confirmed defects: {summary.get('open_observation_count', 0)} / {summary.get('confirmed_defect_count', 0)}\n"
        f"Next action: {summary.get('recommended_next_action')}\n"
        f"JSON: {JSON_OUTPUT}\nMarkdown: {MARKDOWN_OUTPUT}"
    )
