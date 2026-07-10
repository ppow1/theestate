from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

STALE_WORK_DAYS = 7
BLOCKER_WEIGHT = 100
FAILED_VALIDATION_WEIGHT = 90
PENDING_REVIEW_WEIGHT = 80
UNRESOLVED_DECISION_WEIGHT = 70
PROVIDER_HEALTH_WEIGHT = 65
STALE_WORK_WEIGHT = 45
MISSING_EVIDENCE_WEIGHT = 25

DEFAULT_EVIDENCE_PATHS = {
    "work_packages_pending": "collaboration/work_packages/pending",
    "work_packages_active": "collaboration/work_packages/active",
    "work_packages_reviews": "collaboration/work_packages/reviews",
    "work_packages_completions": "collaboration/work_packages/completions",
    "operations_board": "operations/board/latest.md",
    "service_status_board": "operations/services/service_status_board.md",
    "provider_catalog": "config/providers/catalog.json",
    "validation_observations": "operations/validation",
    "office_readiness_json": "runtime/steward/office_operational_readiness.json",
}

@dataclass(frozen=True)
class Evidence:
    path: str
    kind: str
    summary: str
    exists: bool = True


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(errors="replace")


def _parse_dt(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _json(path: Path) -> Any | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _severity(label: str, score: int) -> str:
    if score >= 90:
        return "critical"
    if score >= 70:
        return "high"
    if score >= 45:
        return "medium"
    return label


def _item(item_id: str, category: str, title: str, score: int, evidence: list[Evidence], explanation: str, recommendation: str) -> dict[str, Any]:
    return {
        "id": item_id,
        "category": category,
        "title": title,
        "priority_score": score,
        "severity": _severity("low", score),
        "explanation": explanation,
        "recommended_next_governed_action": recommendation,
        "evidence": [e.__dict__ for e in evidence],
        "autonomous_execution": False,
        "decision_status": "recommendation_only",
    }


def _iter_files(path: Path, suffixes: tuple[str, ...]) -> Iterable[Path]:
    if not path.exists():
        return []
    return sorted(p for p in path.rglob("*") if p.is_file() and p.suffix.lower() in suffixes)


def _scan_markdown_for_terms(root: Path, rel: str, terms: tuple[str, ...], kind: str) -> list[Evidence]:
    base = root / rel
    found: list[Evidence] = []
    paths = [base] if base.is_file() else list(_iter_files(base, (".md", ".txt")))
    for path in paths:
        text = _read_text(path).lower()
        if any(term in text for term in terms):
            found.append(Evidence(_rel(path, root), kind, f"Contains one or more monitored terms: {', '.join(terms)}"))
    return found


def build_executive_workspace(root: Path | str | None = None, *, now: datetime | None = None) -> dict[str, Any]:
    root = Path(root or Path.cwd())
    now = now or datetime.now(timezone.utc)
    items: list[dict[str, Any]] = []
    missing: list[Evidence] = []

    for name, rel in DEFAULT_EVIDENCE_PATHS.items():
        if not (root / rel).exists():
            missing.append(Evidence(rel, "missing_evidence", f"Expected evidence source is absent: {name}", False))

    blockers = _scan_markdown_for_terms(root, "collaboration/work_packages", ("blocker", "blocked", "blocking"), "blocker")
    if blockers:
        items.append(_item("attention.blockers", "current_blockers", "Current blockers require Steward attention", BLOCKER_WEIGHT + min(len(blockers), 10), blockers[:12], "Existing work-package evidence mentions blocked or blocking work.", "Review the controlling work package, decide whether to hold, unblock, or request revision, and record the decision through governed Office controls."))

    failures = _scan_markdown_for_terms(root, "operations", ("failed", "failure", "not production ready", "validation failed"), "failed_validation")
    if failures:
        items.append(_item("attention.failed_validation", "failed_validation", "Validation or readiness failures are present", FAILED_VALIDATION_WEIGHT + min(len(failures), 10), failures[:12], "Operations evidence contains failed validation or non-ready status language.", "Inspect the validation artifact, assign remediation, and require fresh validation before acceptance."))

    pending_reviews = list(_iter_files(root / "collaboration/work_packages/reviews", (".md", ".json")))
    if pending_reviews:
        evidence = [Evidence(_rel(p, root), "pending_review", "Review artifact awaits governed disposition.") for p in pending_reviews[:12]]
        items.append(_item("attention.pending_reviews", "pending_reviews", "Pending reviews await Steward disposition", PENDING_REVIEW_WEIGHT + min(len(pending_reviews), 10), evidence, "Review artifacts exist in the work-package review area.", "Open the review artifacts and either accept, reject, or request changes according to the Estate change process."))

    decisions = _scan_markdown_for_terms(root, "collaboration", ("decision needed", "unresolved decision", "requires steward", "steward attention"), "unresolved_decision")
    if decisions:
        items.append(_item("attention.unresolved_decisions", "unresolved_decisions", "Unresolved decisions are documented", UNRESOLVED_DECISION_WEIGHT + min(len(decisions), 10), decisions[:12], "Collaboration evidence explicitly asks for Steward attention or a decision.", "Resolve the decision in the controlling workspace; treat this queue as evidence, not the decision record."))

    provider_texts = _scan_markdown_for_terms(root, "operations/services", ("down", "degraded", "unavailable", "saturated", "warning"), "provider_runtime_health")
    catalog = _json(root / "config/providers/catalog.json")
    if isinstance(catalog, dict) and not catalog:
        provider_texts.append(Evidence("config/providers/catalog.json", "provider_runtime_health", "Provider catalog is empty."))
    if provider_texts:
        items.append(_item("attention.provider_health", "provider_runtime_health", "Provider or runtime health may limit safe unattended operation", PROVIDER_HEALTH_WEIGHT + min(len(provider_texts), 10), provider_texts[:12], "Provider/runtime evidence contains degraded, unavailable, saturated, warning, or empty-catalog signals.", "Check provider capacity and runtime status before starting or leaving autonomous work unattended."))

    stale_evidence: list[Evidence] = []
    for area in (root / "collaboration/work_packages/active", root / "collaboration/work_packages/pending"):
        for path in _iter_files(area, (".md", ".json")):
            age_days = (now - datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)).days
            if age_days > STALE_WORK_DAYS:
                stale_evidence.append(Evidence(_rel(path, root), "stale_work", f"File age is {age_days} days, above {STALE_WORK_DAYS}-day threshold."))
    if stale_evidence:
        items.append(_item("attention.stale_work", "stale_work", "Stale pending or active work exists", STALE_WORK_WEIGHT + min(len(stale_evidence), 10), stale_evidence[:12], "Pending or active work-package files have not changed within the stale-work threshold.", "Confirm whether each stale item is still active, should be closed, or should be re-planned."))

    if missing:
        items.append(_item("attention.missing_evidence", "missing_evidence", "Some expected evidence sources are missing", MISSING_EVIDENCE_WEIGHT + min(len(missing), 10), missing, "Readiness cannot be fully proven because one or more expected evidence sources are absent.", "Collect or regenerate the missing evidence before treating the Estate as safe to leave unattended."))

    items.sort(key=lambda value: (-int(value["priority_score"]), str(value["id"])))
    top = items[0] if items else None
    critical = [i for i in items if i["priority_score"] >= 90]
    high = [i for i in items if 70 <= i["priority_score"] < 90]
    readiness = "not_ready" if critical else "conditional" if high or missing else "ready"
    return {
        "kind": "office_executive_workspace_staged",
        "staged_not_installed": True,
        "generated_at": now.isoformat(),
        "attention_queue": items,
        "readiness_verdict": {
            "short_unattended_operation": readiness,
            "safe_to_leave_unattended": readiness == "ready",
            "reason": "Critical attention items block unattended operation." if critical else "High-risk or missing evidence requires Steward awareness." if readiness == "conditional" else "No monitored blockers were found in available evidence.",
        },
        "recommended_next_governed_action": None if top is None else {"item_id": top["id"], "action": top["recommended_next_governed_action"], "why": top["explanation"], "evidence": top["evidence"]},
        "uncertainty": {"missing_evidence": [e.__dict__ for e in missing], "truthful_limitations": "This staged workspace only reports evidence and recommendations; it does not approve, reject, install, or execute work."},
        "authority_boundaries": {"recommendations_are_decisions": False, "autonomous_approval": False, "autonomous_execution": False},
        "drill_down": {"source_root": str(root), "controlling_workspaces": sorted({e["path"].split("/")[0] for item in items for e in item["evidence"] if e.get("path")})},
    }


def render_executive_workspace_markdown(payload: dict[str, Any]) -> str:
    lines = ["# Staged Executive Workspace", "", f"Generated: {payload.get('generated_at')}", f"Staged not installed: {payload.get('staged_not_installed')}", "", "## Readiness", "", f"Short unattended operation: **{payload['readiness_verdict']['short_unattended_operation']}**", payload['readiness_verdict']['reason'], "", "## Attention Queue"]
    for item in payload.get("attention_queue", []):
        lines.extend(["", f"### {item['priority_score']} - {item['title']}", f"Category: {item['category']}", item["explanation"], f"Recommended governed action: {item['recommended_next_governed_action']}", "Evidence:"])
        for evidence in item.get("evidence", []):
            lines.append(f"- `{evidence['path']}` ({evidence['kind']}): {evidence['summary']}")
    if not payload.get("attention_queue"):
        lines.append("No monitored attention items found in available evidence.")
    lines.extend(["", "## Authority Boundary", "", "Recommendations are evidence, not decisions. This staged module performs no approval or execution."])
    return "\n".join(lines) + "\n"
