"""Read-only readiness projection over canonical evidence supplied by callers."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Iterable

SCHEMA_VERSION = "estate.readiness-evidence-projection.v1"
STATES = {"unverified", "partially_evidenced", "validating", "ready", "accepted", "rejected", "stale", "indeterminate"}
SOURCE_PRECEDENCE = {
    "protected_acceptance": 100,
    "protected_rejection": 100,
    "approval_record": 90,
    "review_record": 80,
    "validation_result": 70,
    "test_result": 60,
    "completion_receipt": 50,
    "implementation_claim": 20,
}
CONFIDENCE = {100: "high", 90: "high", 80: "high", 70: "high", 60: "medium", 50: "medium", 20: "low"}


def _time(value: str | datetime | None) -> datetime | None:
    if isinstance(value, datetime):
        parsed = value
    elif value:
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return None
    else:
        return None
    return parsed.replace(tzinfo=parsed.tzinfo or timezone.utc).astimezone(timezone.utc)


def _iso(value: datetime | None) -> str | None:
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z") if value else None


def project_readiness_evidence(
    evidence: Iterable[dict[str, Any]], *,
    subjects: Iterable[str] = (),
    dependencies: dict[str, Iterable[str]] | None = None,
    observed_at: str | datetime | None = None,
    default_freshness_seconds: int = 86_400,
) -> dict[str, Any]:
    """Unify evidence into a reversible projection that grants no authority."""
    now = _time(observed_at) or datetime.now(timezone.utc)
    if default_freshness_seconds <= 0:
        raise ValueError("default_freshness_seconds must be positive")
    records = [deepcopy(item) for item in evidence]
    grouped: dict[str, list[dict[str, Any]]] = {str(subject): [] for subject in subjects}
    identity_seen: dict[str, dict[str, Any]] = {}
    global_warnings: list[str] = []
    superseded_ids = {str(item.get("supersedes")) for item in records if item.get("supersedes")}

    for raw in records:
        subject = str(raw.get("subject_id") or raw.get("package_id") or "").strip()
        evidence_id = str(raw.get("evidence_id") or "").strip()
        source_kind = str(raw.get("source_kind") or "").strip()
        state = str(raw.get("state") or "unverified").strip().lower().replace(" ", "_")
        aliases = {"complete": "partially_evidenced", "passed": "ready", "failed": "rejected", "accept": "accepted"}
        state = aliases.get(state, state)
        if state not in STATES:
            state = "indeterminate"
        issued_at = _time(raw.get("issued_at") or raw.get("effective_at"))
        expires_at = _time(raw.get("expires_at"))
        freshness = raw.get("freshness_seconds", default_freshness_seconds)
        try:
            freshness = int(freshness)
        except (TypeError, ValueError):
            freshness = 0
        inaccessible = bool(raw.get("inaccessible"))
        stale = (
            issued_at is None or issued_at > now or freshness <= 0 or
            (now - issued_at).total_seconds() > freshness or
            (expires_at is not None and now > expires_at) or bool(raw.get("stale"))
        )
        normalized = {
            "evidence_id": evidence_id,
            "state": state,
            "source_kind": source_kind,
            "source_precedence": SOURCE_PRECEDENCE.get(source_kind, 0),
            "reference": str(raw.get("reference") or "").strip(),
            "authority": str(raw.get("authority") or "").strip() or None,
            "issued_at": _iso(issued_at),
            "expires_at": _iso(expires_at),
            "freshness_seconds": freshness,
            "stale": stale,
            "inaccessible": inaccessible,
            "superseded": evidence_id in superseded_ids,
            "supersedes": str(raw.get("supersedes") or "").strip() or None,
            "confidence": CONFIDENCE.get(SOURCE_PRECEDENCE.get(source_kind, 0), "low"),
        }
        if evidence_id and evidence_id in identity_seen and identity_seen[evidence_id] != normalized:
            global_warnings.append(f"evidence identity {evidence_id} has conflicting content")
            normalized["identity_conflict"] = True
            identity_seen[evidence_id]["identity_conflict"] = True
        elif evidence_id:
            identity_seen[evidence_id] = normalized
        grouped.setdefault(subject, []).append(normalized)

    dependency_map = {str(key): [str(dep) for dep in value] for key, value in (dependencies or {}).items()}
    projections: list[dict[str, Any]] = []
    independently_accepted: set[str] = set()
    resolved: dict[str, tuple[str, dict[str, Any] | None, list[str], list[dict[str, Any]]]] = {}
    for subject in sorted(grouped):
        lineage = sorted(grouped[subject], key=lambda x: (x["evidence_id"], x["reference"], x["state"]))
        warnings: list[str] = []
        current = [item for item in lineage if not item["stale"] and not item["superseded"] and not item["inaccessible"]]
        state = "unverified"
        selected = None
        if not subject:
            warnings.append("evidence is missing a subject identifier")
            state = "indeterminate"
        if any(item["inaccessible"] for item in lineage):
            warnings.append(f"{subject or '<missing>'}: evidence is inaccessible")
        if lineage and not current:
            state = "stale" if all(item["stale"] or item["superseded"] for item in lineage) else "indeterminate"
        elif current:
            highest = max(item["source_precedence"] for item in current)
            peers = [item for item in current if item["source_precedence"] == highest]
            if highest == 0 or any(not item["evidence_id"] or not item["reference"] for item in peers):
                state = "indeterminate"
                warnings.append(f"{subject}: selected evidence lacks canonical identity, reference, or source kind")
            elif any(item.get("identity_conflict") for item in peers) or len({item["state"] for item in peers}) > 1:
                state = "indeterminate"
                warnings.append(f"{subject}: current equally authoritative evidence conflicts")
            else:
                selected = max(peers, key=lambda x: (x["issued_at"] or "", x["evidence_id"]))
                state = selected["state"]
                if state == "accepted" and (selected["source_kind"] != "protected_acceptance" or not selected["authority"]):
                    state = "ready"
                    warnings.append(f"{subject}: non-protected acceptance claim was reduced to ready")
        if any(item["stale"] for item in lineage) and current:
            warnings.append(f"{subject}: stale evidence was excluded")
        if any(item["superseded"] for item in lineage):
            warnings.append(f"{subject}: superseded evidence is retained in lineage but excluded")
        resolved[subject] = (state, selected, warnings, lineage)
        if state == "accepted":
            independently_accepted.add(subject)

    for subject in sorted(grouped):
        state, selected, warnings, lineage = resolved[subject]
        deps = dependency_map.get(subject, [])
        missing = sorted(dep for dep in deps if dep not in independently_accepted)
        if missing and state in {"ready", "accepted"}:
            state = "partially_evidenced"
            warnings.append(f"{subject}: dependent subjects are not accepted: {', '.join(missing)}")
        projections.append({
            "subject_id": subject or None,
            "readiness_state": state,
            "acceptance_authority": selected.get("authority") if selected and state == "accepted" else None,
            "confidence": selected.get("confidence") if selected and state not in {"indeterminate", "stale"} else "low",
            "dependencies": deps,
            "unaccepted_dependencies": missing,
            "evidence_references": sorted({item["reference"] for item in lineage if item["reference"]}),
            "evidence_lineage": lineage,
            "warnings": sorted(set(warnings)),
            "derived_view_only": True,
            "authorizes_action": False,
        })

    states = [item["readiness_state"] for item in projections]
    aggregate = (
        "unverified" if not projections else
        "indeterminate" if any(state == "indeterminate" for state in states) or global_warnings else
        "rejected" if any(state == "rejected" for state in states) else
        "stale" if any(state == "stale" for state in states) else
        "accepted" if all(state == "accepted" for state in states) else
        "ready" if all(state in {"ready", "accepted"} for state in states) else
        "validating" if any(state == "validating" for state in states) else
        "partially_evidenced" if any(state != "unverified" for state in states) else "unverified"
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "observed_at": _iso(now),
        "aggregate_readiness": aggregate,
        "subjects": projections,
        "warnings": sorted(set(global_warnings + [warning for item in projections for warning in item["warnings"]])),
        "derived_view_only": True,
        "authorizes_action": False,
        "acceptance_notice": "Only a current protected acceptance record with its issuing authority can project accepted state.",
    }
