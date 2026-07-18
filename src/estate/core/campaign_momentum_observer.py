"""Read-only, repository-grounded campaign momentum observation.

The observer projects canonical manifests and caller-supplied or repository
evidence.  It never writes, dispatches, or treats implementation as acceptance.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

SCHEMA_VERSION = "estate.campaign-momentum-observation.v1"
ENGINEERING_SCHEMA_VERSION = "estate.engineering-operational-projection.v1"
STATES = {
    "unready", "waiting", "eligible", "active", "review_gated",
    "protected_gated", "blocked", "degraded", "failed", "paused",
    "complete_pending_acceptance", "accepted_closed", "indeterminate",
}
TERMINAL = {"accepted_closed"}
SOURCE_PRECEDENCE = {
    "protected_acceptance": 100, "closure_record": 95,
    "schema_valid_receipt": 80, "canonical_artifact": 70,
    "repository_record": 60, "runtime_claim": 30,
    "dashboard": 20, "inference": 10,
}
EXPLICIT_PRIORITY = {
    "accepted_closed": 100, "failed": 90, "paused": 88, "blocked": 86,
    "protected_gated": 84, "review_gated": 82, "complete_pending_acceptance": 80,
    "active": 60, "degraded": 55, "eligible": 40, "waiting": 30,
    "unready": 20, "indeterminate": 10,
}

ENGINEERING_STATES = {
    "queued", "active", "blocked", "validating", "accepted", "paused",
    "abandoned", "indeterminate",
}
ENGINEERING_SOURCE_PRECEDENCE = {
    "protected_acceptance": 100,
    "protected_abandonment": 100,
    "review_record": 90,
    "validation_record": 80,
    "dispatch_record": 70,
    "work_package_record": 60,
    "runtime_claim": 30,
}
ENGINEERING_CONFIDENCE = {
    "protected_acceptance": "high",
    "protected_abandonment": "high",
    "review_record": "high",
    "validation_record": "high",
    "dispatch_record": "medium",
    "work_package_record": "medium",
    "runtime_claim": "low",
}


def _time(value: str | datetime | None) -> datetime | None:
    if isinstance(value, datetime):
        result = value
    elif value:
        try:
            result = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return None
    else:
        return None
    return result.replace(tzinfo=result.tzinfo or timezone.utc).astimezone(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _repository_identity(root: Path, manifest: Path) -> dict[str, Any]:
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True,
            capture_output=True, check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        commit = None
    return {"root": str(root.resolve()), "commit": commit, "manifest_sha256": _digest(manifest)}


def _normalize_evidence(item: dict[str, Any], now: datetime) -> dict[str, Any]:
    state = str(item.get("state") or "indeterminate").strip().lower().replace(" ", "_")
    aliases = {"complete": "complete_pending_acceptance", "accepted": "accepted_closed",
               "closed": "accepted_closed", "review_required": "review_gated",
               "protected": "protected_gated", "running": "active"}
    state = aliases.get(state, state)
    if state not in STATES:
        state = "indeterminate"
    timestamp = _time(item.get("effective_at") or item.get("observed_at"))
    expires = _time(item.get("expires_at"))
    stale = bool(item.get("stale")) or (expires is not None and now > expires)
    reference = str(item.get("reference") or "").strip()
    return {
        "state": state, "source_kind": str(item.get("source_kind") or "inference"),
        "source_precedence": SOURCE_PRECEDENCE.get(str(item.get("source_kind") or "inference"), 0),
        "reference": reference, "effective_at": _iso(timestamp) if timestamp else None,
        "stale": stale, "reason": str(item.get("reason") or "").strip(),
        "blocker_type": item.get("blocker_type"),
        "follow_up_destination": item.get("follow_up_destination"),
    }


def _repository_evidence(root: Path, package: dict[str, Any]) -> list[dict[str, Any]]:
    """Discover only manifest-declared receipts; existence proves completion, not acceptance."""
    receipt = package.get("receipt_path")
    if receipt and (root / receipt).is_file():
        return [{"state": "complete_pending_acceptance", "source_kind": "schema_valid_receipt",
                 "reference": receipt, "reason": "Manifest-declared completion receipt exists."}]
    return []


def _reconcile(package_id: str, evidence: Iterable[dict[str, Any]], now: datetime) -> tuple[str, list[dict[str, Any]], list[str]]:
    items = [_normalize_evidence(deepcopy(item), now) for item in evidence]
    warnings: list[str] = []
    if not items:
        return "", [], warnings
    current = [item for item in items if not item["stale"]]
    if not current:
        return "indeterminate", sorted(items, key=lambda x: (x["reference"], x["state"])), [f"{package_id}: all state evidence is stale"]
    highest = max(item["source_precedence"] for item in current)
    peers = [item for item in current if item["source_precedence"] == highest]
    peer_states = {item["state"] for item in peers}
    if len(peer_states) > 1:
        warnings.append(f"{package_id}: equally authoritative evidence is contradictory: {', '.join(sorted(peer_states))}")
        return "indeterminate", sorted(items, key=lambda x: (x["reference"], x["state"])), warnings
    selected = max(current, key=lambda x: (x["source_precedence"], EXPLICIT_PRIORITY[x["state"]], x["effective_at"] or "", x["reference"]))
    if any(item["stale"] for item in items):
        warnings.append(f"{package_id}: stale evidence was excluded")
    if not selected["reference"]:
        warnings.append(f"{package_id}: selected evidence has no canonical reference")
        return "indeterminate", sorted(items, key=lambda x: (x["reference"], x["state"])), warnings
    return selected["state"], sorted(items, key=lambda x: (x["reference"], x["state"])), warnings


def observe_campaign(
    root: str | Path, manifest_path: str | Path, *,
    evidence: Iterable[dict[str, Any]] = (), observed_at: str | datetime | None = None,
) -> dict[str, Any]:
    """Build a deterministic projection; ``evidence`` records name ``package_id``."""
    root = Path(root)
    manifest_file = Path(manifest_path)
    if not manifest_file.is_absolute():
        manifest_file = root / manifest_file
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    now = _time(observed_at) or datetime.now(timezone.utc)
    supplied: dict[str, list[dict[str, Any]]] = {}
    for item in evidence:
        supplied.setdefault(str(item.get("package_id") or ""), []).append(deepcopy(item))
    packages = manifest.get("packages") or []
    ids = [str(p["id"]) for p in packages]
    duplicate = len(ids) != len(set(ids))
    known = set(ids)
    results: list[dict[str, Any]] = []
    warnings: list[str] = []
    accepted: set[str] = set()

    # First pass resolves authoritative evidence independently of dependencies.
    resolved: dict[str, tuple[str, list[dict[str, Any]], list[str]]] = {}
    for package in packages:
        pid = str(package["id"])
        records = supplied.get(pid, []) or _repository_evidence(root, package)
        resolved[pid] = _reconcile(pid, records, now)
        if resolved[pid][0] == "accepted_closed":
            accepted.add(pid)
    if duplicate:
        warnings.append("campaign manifest contains duplicate package identifiers")

    for package in packages:
        pid = str(package["id"])
        state, lineage, local_warnings = resolved[pid]
        deps = [str(dep) for dep in package.get("depends_on") or []]
        unknown_deps = sorted(set(deps) - known)
        unmet = sorted(dep for dep in deps if dep not in accepted)
        if unknown_deps:
            state = "indeterminate"
            local_warnings.append(f"{pid}: manifest names unknown dependencies: {', '.join(unknown_deps)}")
        elif not state:
            state = "waiting" if unmet else "eligible"
            lineage = [{"state": state, "source_kind": "canonical_artifact", "source_precedence": 70,
                        "reference": str(package.get("path") or manifest.get("authoritative_campaign_path") or manifest_file.relative_to(root)),
                        "effective_at": None, "stale": False,
                        "reason": "Declared dependencies are incomplete." if unmet else "All declared dependencies are accepted/closed.",
                        "blocker_type": "dependency" if unmet else None, "follow_up_destination": None}]
        elif state in {"eligible", "active"} and unmet:
            state = "indeterminate"
            local_warnings.append(f"{pid}: progress evidence conflicts with unmet dependencies")
        warnings.extend(local_warnings)
        destination = next((x["follow_up_destination"] for x in lineage if x.get("follow_up_destination")), None)
        if not destination:
            destination = "protected acceptance lane" if state == "complete_pending_acceptance" else (
                "Chief Architect or applicable office" if state in {"protected_gated", "indeterminate"} else
                "Engineering execution lane" if state == "eligible" else "canonical evidence owner")
        explanation = {
            "waiting": f"Waiting for accepted dependencies: {', '.join(unmet)}.",
            "eligible": "All declared dependencies are accepted; observation does not authorize dispatch.",
            "complete_pending_acceptance": "Implementation completion evidence exists, but protected acceptance is absent.",
            "accepted_closed": "Protected acceptance or closure evidence is authoritative.",
            "indeterminate": "Evidence is missing, stale, contradictory, or inconsistent; progression fails closed.",
        }.get(state, next((x["reason"] for x in lineage if x["state"] == state and x["reason"]), f"Authoritative evidence reports {state}."))
        results.append({
            "package_id": pid, "canonical_reference": package.get("path"), "gate": package.get("gate"),
            "parallel_group": package.get("parallel_group"), "observed_state": state,
            "dependencies": deps, "dependency_satisfaction": {"satisfied": sorted(set(deps) & accepted), "unmet": unmet},
            "evidence_references": sorted({x["reference"] for x in lineage if x["reference"]}),
            "evidence_lineage": lineage, "warnings": sorted(set(local_warnings)),
            "explanation": explanation, "recommended_follow_up_destination": destination,
            "authorizes_action": False,
        })

    by_state = {state: sorted(x["package_id"] for x in results if x["observed_state"] == state) for state in sorted(STATES)}
    limiting = sorted(x["package_id"] for x in results if x["observed_state"] in {"waiting", "blocked", "failed", "paused", "indeterminate", "protected_gated"})
    campaign_state = "accepted_closed" if results and all(x["observed_state"] in TERMINAL for x in results) else (
        "paused" if any(x["observed_state"] == "paused" for x in results) else
        "failed" if any(x["observed_state"] == "failed" for x in results) else
        "indeterminate" if warnings or any(x["observed_state"] == "indeterminate" for x in results) else
        "blocked" if any(x["observed_state"] in {"blocked", "protected_gated"} for x in results) else
        "active" if any(x["observed_state"] == "active" for x in results) else
        "degraded" if any(x["observed_state"] == "degraded" for x in results) else
        "complete_pending_acceptance" if results and all(x["observed_state"] in TERMINAL | {"complete_pending_acceptance"} for x in results) else
        "eligible" if by_state["eligible"] else "waiting")
    return {
        "schema_version": SCHEMA_VERSION, "campaign_id": manifest["campaign_id"],
        "canonical_reference": manifest.get("authoritative_campaign_path") or str(manifest_file.relative_to(root)),
        "observation_timestamp": _iso(now), "repository_identity": _repository_identity(root, manifest_file),
        "campaign_momentum_state": campaign_state, "packages": results,
        "dependency_summary": {"accepted": sorted(accepted), "limiting_chain": limiting},
        "critical_path": limiting or None, "critical_path_determinable": bool(limiting),
        "eligible_packages": by_state["eligible"], "active_packages": by_state["active"],
        "blockers": sorted(x["package_id"] for x in results if x["observed_state"] in {"blocked", "failed", "waiting"}),
        "degraded_conditions": by_state["degraded"], "pending_review": by_state["review_gated"],
        "protected_decisions": by_state["protected_gated"] + by_state["complete_pending_acceptance"],
        "warnings": sorted(set(warnings)), "state_sets": by_state,
        "explanation": f"Campaign {manifest['campaign_id']} is observed as {campaign_state}; this projection authorizes no action.",
        "recommended_follow_up_destination": "Chief Architect" if warnings else "existing package-specific authority lanes",
        "observation_only": True,
    }


def render_momentum_markdown(observation: dict[str, Any]) -> str:
    """Render the stable observation as a concise human-readable view."""
    lines = [f"# {observation['campaign_id']} momentum", "", f"**Observed state:** {observation['campaign_momentum_state']}",
             f"**Observed at:** {observation['observation_timestamp']}", "", "| Package | State | Dependencies | Explanation |", "|---|---|---|---|"]
    for item in observation["packages"]:
        deps = ", ".join(item["dependency_satisfaction"]["unmet"]) or "satisfied"
        lines.append(f"| {item['package_id']} | {item['observed_state']} | {deps} | {item['explanation']} |")
    lines.extend(["", "> Observation only: this view does not dispatch, mutate state, or grant acceptance."])
    return "\n".join(lines) + "\n"


def project_engineering_operations(
    signals: Iterable[dict[str, Any]], *,
    observed_at: str | datetime | None = None,
    default_freshness_seconds: int = 86_400,
) -> dict[str, Any]:
    """Project canonical Engineering signals without mutating their sources.

    Callers adapt existing work-package, dispatch, validation, review, and
    protected-decision records into signals. A projection is deliberately
    unusable as dispatch, validation, acceptance, merge, or closure authority.
    """
    now = _time(observed_at) or datetime.now(timezone.utc)
    if default_freshness_seconds <= 0:
        raise ValueError("default_freshness_seconds must be positive")
    grouped: dict[str, list[dict[str, Any]]] = {}
    for original in signals:
        item = deepcopy(original)
        work_id = str(item.get("work_id") or item.get("package_id") or "").strip()
        source_kind = str(item.get("source_kind") or "").strip()
        state = str(item.get("state") or "indeterminate").strip().lower().replace(" ", "_")
        aliases = {
            "ready": "queued", "eligible": "queued", "running": "active",
            "in_progress": "active", "validation": "validating",
            "complete_pending_acceptance": "validating",
            "accepted_closed": "accepted", "cancelled": "abandoned",
        }
        state = aliases.get(state, state)
        if state not in ENGINEERING_STATES:
            state = "indeterminate"
        effective_at = _time(item.get("effective_at") or item.get("observed_at"))
        freshness_seconds = item.get("freshness_seconds", default_freshness_seconds)
        try:
            freshness_seconds = int(freshness_seconds)
        except (TypeError, ValueError):
            freshness_seconds = 0
        stale = (
            effective_at is None or freshness_seconds <= 0 or effective_at > now or
            (now - effective_at).total_seconds() > freshness_seconds or bool(item.get("stale"))
        )
        normalized = {
            "state": state,
            "source_kind": source_kind,
            "source_precedence": ENGINEERING_SOURCE_PRECEDENCE.get(source_kind, 0),
            "reference": str(item.get("reference") or "").strip(),
            "effective_at": _iso(effective_at) if effective_at else None,
            "freshness_seconds": freshness_seconds,
            "stale": stale,
            "confidence": ENGINEERING_CONFIDENCE.get(source_kind, "low"),
            "reason": str(item.get("reason") or "").strip(),
            "owner": item.get("owner"),
            "lane": item.get("lane"),
        }
        grouped.setdefault(work_id, []).append(normalized)

    projections: list[dict[str, Any]] = []
    warnings: list[str] = []
    for work_id in sorted(grouped):
        lineage = sorted(grouped[work_id], key=lambda x: (x["reference"], x["state"], x["source_kind"]))
        local: list[str] = []
        current = [item for item in lineage if not item["stale"]]
        selected: dict[str, Any] | None = None
        state = "indeterminate"
        if not work_id:
            local.append("Engineering signal is missing a canonical work identifier")
        if not current:
            local.append(f"{work_id or '<missing>'}: all Engineering signals are stale or undated")
        else:
            highest = max(item["source_precedence"] for item in current)
            peers = [item for item in current if item["source_precedence"] == highest]
            peer_states = {item["state"] for item in peers}
            if highest == 0:
                local.append(f"{work_id}: no recognized canonical Engineering source kind")
            elif len(peer_states) > 1:
                local.append(f"{work_id}: equally authoritative Engineering signals conflict: {', '.join(sorted(peer_states))}")
            else:
                selected = max(peers, key=lambda x: (x["effective_at"] or "", x["reference"]))
                state = selected["state"]
                if not selected["reference"]:
                    state = "indeterminate"
                    local.append(f"{work_id}: selected Engineering signal has no canonical reference")
        if not work_id:
            state = "indeterminate"
        if any(item["stale"] for item in lineage) and current:
            local.append(f"{work_id}: stale Engineering signals were excluded")
        warnings.extend(local)
        projections.append({
            "work_id": work_id or None,
            "observed_state": state,
            "owner": selected.get("owner") if selected else None,
            "implementation_lane": selected.get("lane") if selected else None,
            "confidence": selected.get("confidence") if selected and state != "indeterminate" else "low",
            "evidence_references": sorted({item["reference"] for item in lineage if item["reference"]}),
            "evidence_lineage": lineage,
            "warnings": sorted(set(local)),
            "derived_view_only": True,
            "authorizes_action": False,
        })

    state_counts = {
        state: sum(item["observed_state"] == state for item in projections)
        for state in sorted(ENGINEERING_STATES)
    }
    active_lanes = sorted({
        str(item["implementation_lane"]) for item in projections
        if item["observed_state"] == "active" and item["implementation_lane"]
    })
    return {
        "schema_version": ENGINEERING_SCHEMA_VERSION,
        "observation_timestamp": _iso(now),
        "work": projections,
        "capacity": {
            "active_work_count": state_counts["active"],
            "queued_work_count": state_counts["queued"],
            "blocked_work_count": state_counts["blocked"],
            "active_implementation_lanes": active_lanes,
            "capacity_limit": None,
            "capacity_limit_known": False,
        },
        "state_counts": state_counts,
        "limiting_dependencies": sorted(
            item["work_id"] for item in projections
            if item["work_id"] and item["observed_state"] in {"blocked", "indeterminate"}
        ),
        "warnings": sorted(set(warnings)),
        "derived_view_only": True,
        "authorizes_action": False,
        "authority_notice": (
            "Engineering governance and canonical records remain authoritative; "
            "this projection cannot dispatch, validate, accept, merge, close, pause, or abandon work."
        ),
    }
