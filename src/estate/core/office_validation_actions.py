"""Office validation, audit, and verdict control helpers for WP-0518.

The module is an Office-facing adapter only. It reads existing validation,
audit, and verdict artifacts and delegates state-changing work to canonical
validation/audit runtimes; it never grants institutional acceptance.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from estate.core.paths import ESTATE_ROOT
from estate.core.post_merge_audit_processor import PostMergeAuditProcessor, load_post_merge_audit_processor_status
from estate.core.production_readiness_validation import generate_production_readiness_report
from estate.core.work_package_validation import validate_work_package

VALIDATION_GLOBS = [
    "runtime/validation/work_packages/*.json",
    "runtime/validation/*.json",
    "operations/validation/**/*.md",
]
AUDIT_GLOBS = [
    "runtime/post_merge_audit/requests/*.json",
    "runtime/post_merge_audit/status/*.json",
    "runtime/post_merge_audit/verdicts/*.json",
    "runtime/post_merge_audit/evidence/**/*.json",
]
RUNNING_AUDIT_STATES = {"claimed", "running_validation", "running_ring2"}


def _root(root: str | Path | None = None) -> Path:
    return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _rel(base: Path, path: Path | str) -> str:
    p = Path(path)
    try:
        return str(p.relative_to(base)).replace("\\", "/")
    except ValueError:
        return str(p).replace("\\", "/")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _safe_path(base: Path, artifact_path: str) -> Path:
    path = (base / artifact_path).resolve()
    try:
        path.relative_to(base.resolve())
    except ValueError as exc:
        raise ValueError("artifact_path must stay inside the Estate root") from exc
    return path


def _status_from_payload(payload: Any) -> str:
    if not isinstance(payload, dict):
        return "unknown"
    for key in ("validation_status", "state", "status", "verdict", "result", "outcome"):
        if payload.get(key):
            return str(payload[key])
    summary = payload.get("summary")
    if isinstance(summary, dict):
        for key in ("status", "overall_status"):
            if summary.get(key):
                return str(summary[key])
    return "unknown"


def _wp_from_payload(path: Path, payload: Any) -> str | None:
    if isinstance(payload, dict):
        for key in ("work_package_id", "work_package", "runtime_owner"):
            if payload.get(key):
                return str(payload[key])
    stem = path.stem.upper()
    return stem.split("_")[0] if stem.startswith("WP-") else None


def _acknowledged_ids(base: Path) -> set[str]:
    path = base / "runtime/validation/failure_acknowledgements.jsonl"
    out: set[str] = set()
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                item = json.loads(line)
                if item.get("artifact_id"):
                    out.add(str(item["artifact_id"]))
            except Exception:
                continue
    return out


def _row(base: Path, path: Path, kind: str) -> dict[str, Any]:
    payload: Any = None
    if path.suffix == ".json":
        try:
            payload = _read_json(path)
        except Exception as exc:
            payload = {"status": "malformed", "errors": [str(exc)]}
    rel = _rel(base, path)
    status = _status_from_payload(payload)
    wp = _wp_from_payload(path, payload)
    state = "completed" if status in {"passed", "passed_with_findings", "completed", "accepted", "ring2_required"} else "failed" if status in {"failed", "validation_failed", "needs_repair", "blocked"} else "running" if status in RUNNING_AUDIT_STATES else "pending" if status == "pending" else "unknown"
    return {
        "artifact_id": rel,
        "kind": kind,
        "path": rel,
        "work_package_id": wp,
        "result": status,
        "state": state,
        "owner": (payload or {}).get("owner") if isinstance(payload, dict) else None,
        "attention_state": "acknowledged" if rel in _acknowledged_ids(base) else ("attention_required" if state == "failed" else "normal"),
        "updated_at": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(timespec="seconds"),
    }


def inspect_validation_control_center(root: str | Path | None = None, **filters: Any) -> dict[str, Any]:
    base = _root(root)
    rows: list[dict[str, Any]] = []
    for pattern in VALIDATION_GLOBS:
        for path in base.glob(pattern):
            if path.is_file():
                rows.append(_row(base, path, "validation"))
    for pattern in AUDIT_GLOBS:
        for path in base.glob(pattern):
            if path.is_file():
                kind = "verdict" if "verdict" in _rel(base, path) else "audit"
                rows.append(_row(base, path, kind))
    rows.sort(key=lambda r: r["updated_at"], reverse=True)
    rows = _apply_filters(rows, filters)
    payload = {
        "generated_at": _now(),
        "source_of_truth_boundary": "Validation and audit artifacts are evidence only; this control center never grants institutional acceptance.",
        "filters": {k: v for k, v in filters.items() if v not in (None, "")},
        "summary": {"row_count": len(rows), "failed_count": sum(1 for r in rows if r["state"] == "failed"), "attention_count": sum(1 for r in rows if r["attention_state"] == "attention_required")},
        "automatic_validator_status": automatic_validator_status(base),
        "rows": rows,
    }
    out = base / "runtime/validation/office_validation_control_center.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def _apply_filters(rows: list[dict[str, Any]], filters: dict[str, Any]) -> list[dict[str, Any]]:
    def ok(row: dict[str, Any]) -> bool:
        return all([
            not filters.get("result") or row.get("result") == filters["result"],
            not filters.get("package") or str(row.get("work_package_id") or "").lower() == str(filters["package"]).lower(),
            not filters.get("owner") or str(filters.get("owner")).lower() in str(row.get("owner") or "").lower(),
            not filters.get("attention_state") or row.get("attention_state") == filters["attention_state"],
            not filters.get("date_from") or row.get("updated_at", "") >= str(filters["date_from"]),
            not filters.get("date_to") or row.get("updated_at", "") <= str(filters["date_to"]),
        ])
    return [r for r in rows if ok(r)]


def request_validation(root: str | Path | None, work_package_id: str, *, revalidate: bool = False) -> dict[str, Any]:
    base = _root(root)
    payload = validate_work_package(work_package_id, root=base, write=True)
    if revalidate:
        generate_production_readiness_report(root=base, write=True)
    payload["institutional_acceptance_state"] = "not_granted"
    payload["office_request_type"] = "revalidation" if revalidate else "validation"
    inspect_validation_control_center(base)
    return payload


def acknowledge_failure(root: str | Path | None, artifact_id: str, acknowledged_by: str, reason: str | None = None) -> dict[str, Any]:
    base = _root(root)
    if not artifact_id or not acknowledged_by:
        raise ValueError("artifact_id and acknowledged_by are required")
    rec = {"artifact_id": artifact_id, "acknowledged_by": acknowledged_by, "reason": reason or "Office failure acknowledgement", "timestamp": _now(), "authority_boundary": "Acknowledgement records attention handling only; failure evidence remains unchanged."}
    path = base / "runtime/validation/failure_acknowledgements.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, sort_keys=True) + "\n")
    inspect_validation_control_center(base)
    return rec


def automatic_validator_status(root: str | Path | None = None) -> dict[str, Any]:
    status = load_post_merge_audit_processor_status(_root(root))
    summary = status.get("summary") or {}
    return {"available": bool(summary.get("automatic_validation_available", True)), "pending": summary.get("pending_audit_requests", 0), "running": summary.get("running_audit_request"), "latest_verdict": summary.get("latest_verdict"), "latest_validation_status": summary.get("latest_validation_status"), "evidence_root": summary.get("validation_evidence_root"), "provider_execution_performed": False, "dispatch_execution_performed": False}


def open_artifact(root: str | Path | None, artifact_path: str) -> dict[str, Any]:
    base = _root(root)
    path = _safe_path(base, artifact_path)
    if not path.exists() or not path.is_file():
        return {"outcome": "blocked", "message": f"Artifact unavailable: {artifact_path}", "artifact_path": artifact_path}
    return {"outcome": "completed", "message": f"Artifact available for opening: {artifact_path}", "artifact_path": artifact_path, "bytes": path.stat().st_size}


def governed_retry(root: str | Path | None = None, *, max_count: int = 1) -> dict[str, Any]:
    processor = PostMergeAuditProcessor(_root(root))
    result = processor.process_all(max_count=max(1, int(max_count or 1)))
    result["authority_boundary"] = "Retry used the existing PostMergeAuditProcessor queue only; no second retry queue was created."
    result["institutional_acceptance_state"] = "not_granted"
    return result
