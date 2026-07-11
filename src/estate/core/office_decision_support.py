from __future__ import annotations

import copy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

SCHEMA = "estate.office_decision_support.v1"
RECOMMENDATION_STATUSES = {"ready", "blocked", "needs_evidence", "alternative", "defer"}
REQUIRED_EVIDENCE = ("controlling_artifact", "workspace")


@dataclass(frozen=True)
class WorkItem:
    id: str
    title: str
    state: str
    controlling_artifact: str
    workspace: str
    dependencies: Sequence[str] = field(default_factory=tuple)
    blockers: Sequence[str] = field(default_factory=tuple)
    evidence: Mapping[str, str] = field(default_factory=dict)
    alternatives: Sequence[Mapping[str, Any]] = field(default_factory=tuple)
    updated_at: str | None = None
    authority: str = "operator"
    metadata: Mapping[str, Any] = field(default_factory=dict)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def _exists(root: Path, path: str | None) -> bool:
    return bool(path) and (root / str(path)).exists()


def _freshness(updated_at: str | None, stale_after_days: int) -> dict[str, Any]:
    parsed = _parse_dt(updated_at)
    if parsed is None:
        return {"status": "unknown", "age_days": None, "updated_at": updated_at}
    age_days = (datetime.now(timezone.utc) - parsed.astimezone(timezone.utc)).days
    return {"status": "stale" if age_days > stale_after_days else "fresh", "age_days": age_days, "updated_at": updated_at}


def _dependency_trace(item: WorkItem, by_id: Mapping[str, WorkItem], root: Path) -> list[dict[str, Any]]:
    trace = []
    for dep_id in item.dependencies:
        dep = by_id.get(dep_id)
        if dep is None:
            trace.append({"id": dep_id, "status": "missing", "state": None, "controlling_artifact": None, "workspace": None})
            continue
        evidence_ok = _exists(root, dep.controlling_artifact) and _exists(root, dep.workspace)
        ready = dep.state in {"accepted", "completed", "validated"} and evidence_ok
        trace.append({
            "id": dep.id,
            "status": "satisfied" if ready else "unsatisfied",
            "state": dep.state,
            "controlling_artifact": dep.controlling_artifact,
            "workspace": dep.workspace,
            "evidence_complete": evidence_ok,
        })
    return trace


def _missing_evidence(item: WorkItem, root: Path) -> list[dict[str, str]]:
    missing = []
    for label, path in (("controlling_artifact", item.controlling_artifact), ("workspace", item.workspace), *item.evidence.items()):
        if not _exists(root, path):
            missing.append({"kind": str(label), "path": str(path)})
    return missing


def _confidence(status: str, missing: Sequence[Mapping[str, str]], unsatisfied_dependencies: int, freshness: Mapping[str, Any]) -> dict[str, Any]:
    score = 0.9
    reasons = []
    if status != "ready":
        score -= 0.25
        reasons.append(f"status is {status}")
    if missing:
        score -= min(0.4, 0.1 * len(missing))
        reasons.append("required evidence is missing")
    if unsatisfied_dependencies:
        score -= min(0.3, 0.1 * unsatisfied_dependencies)
        reasons.append("dependencies are unsatisfied")
    if freshness.get("status") in {"stale", "unknown"}:
        score -= 0.1
        reasons.append(f"freshness is {freshness.get('status')}")
    score = max(0.0, round(score, 2))
    return {"score": score, "level": "high" if score >= 0.75 else ("medium" if score >= 0.45 else "low"), "uncertainty": reasons}


def build_decision_support(items: Iterable[WorkItem | Mapping[str, Any]], *, root: str | Path = ".", stale_after_days: int = 14) -> dict[str, Any]:
    base = Path(root)
    work_items = [raw if isinstance(raw, WorkItem) else WorkItem(**raw) for raw in items]
    by_id = {item.id: item for item in work_items}
    recommendations = []
    for item in sorted(work_items, key=lambda value: value.id):
        missing = _missing_evidence(item, base)
        trace = _dependency_trace(item, by_id, base)
        unsatisfied = [dep for dep in trace if dep["status"] != "satisfied"]
        blocked = list(item.blockers) + [f"dependency {dep['id']} is {dep['status']}" for dep in unsatisfied]
        if blocked:
            status = "blocked"
            next_action = "Resolve blockers and dependency gaps before requesting authorization."
        elif missing:
            status = "needs_evidence"
            next_action = "Attach missing evidence before requesting authorization."
        elif item.state in {"validated", "ready", "proposed"}:
            status = "ready"
            next_action = "Recommend operator authorization for the next governed action."
        else:
            status = "defer"
            next_action = "Defer until the work item reaches a governed decision state."
        freshness = _freshness(item.updated_at, stale_after_days)
        confidence = _confidence(status, missing, len(unsatisfied), freshness)
        recommendations.append({
            "id": item.id,
            "title": item.title,
            "state": item.state,
            "status": status,
            "explanation": {"blockers": blocked, "dependencies": trace, "missing_evidence": missing},
            "recommendation": next_action,
            "alternatives": [copy.deepcopy(dict(alt)) for alt in item.alternatives],
            "links": {"controlling_artifact": item.controlling_artifact, "workspace": item.workspace},
            "indicators": {"freshness": freshness, "confidence": confidence, "authority": item.authority},
            "governance_boundary": {
                "recommendation": True,
                "authorization": False,
                "execution": False,
                "validation": False,
                "acceptance": False,
                "note": "This staged decision support output is advisory only and does not mutate authority or state.",
            },
            "metadata": copy.deepcopy(dict(item.metadata)),
        })
    return {"schema": SCHEMA, "installed_by_wp_0531": True, "generated_at": utc_now(), "count": len(recommendations), "recommendations": recommendations}


def explain_work_item(decision_support: Mapping[str, Any], item_id: str) -> dict[str, Any]:
    for recommendation in decision_support.get("recommendations", []):
        if recommendation.get("id") == item_id:
            return copy.deepcopy(recommendation)
    raise KeyError(item_id)


def summarize_next_actions(decision_support: Mapping[str, Any]) -> list[dict[str, Any]]:
    rank = {"blocked": 0, "needs_evidence": 1, "ready": 2, "defer": 3, "alternative": 4}
    rows = []
    for rec in decision_support.get("recommendations", []):
        rows.append({"id": rec["id"], "status": rec["status"], "recommendation": rec["recommendation"], "confidence": rec["indicators"]["confidence"]["level"]})
    return sorted(rows, key=lambda row: (rank.get(row["status"], 99), row["id"]))
