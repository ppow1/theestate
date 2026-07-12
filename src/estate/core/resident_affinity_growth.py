"""Resident affinity and growth runtime for Campaign 06.

The runtime is an evidence-backed relationship and development projection layer.
It persists only append-only/correction records under runtime/, keeps authority
and privacy explicit, and never grants consent, access, priority, credentials, or
governance power from relationship warmth, confidence, skill, or milestones.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from estate.core.paths import ESTATE_ROOT

SCHEMA_VERSION = "estate_resident_affinity_growth.v1"
AFFINITY_PATH = Path("runtime/resident_affinity/affinity_graph.json")
EXPERIENCE_PATH = Path("runtime/resident_growth/experience_ledger.jsonl")
SKILL_PATH = Path("runtime/resident_growth/skill_profiles.json")
CONFIDENCE_PATH = Path("runtime/resident_growth/confidence_profiles.json")
PREFERENCE_PATH = Path("runtime/resident_growth/preference_refinements.json")
MILESTONE_PATH = Path("runtime/resident_growth/milestones.json")
LEGACY_REL_PATH = Path("data/relationships/resident_relationships.json")

AFFINITY_DIMENSIONS = {
    "trust", "respect", "familiarity", "warmth", "affection", "admiration", "comfort",
    "playfulness", "protectiveness", "attraction", "rivalry", "professional_confidence",
}
PROTECTED_DIMENSIONS = {"attraction", "affection", "protected_bond"}
PRIVATE_VISIBILITIES = {"private", "restricted", "protected"}
TRUST_EVENTS = {
    "promise_kept", "promise_broken", "accurate_judgment", "competence", "candor",
    "confidentiality", "boundary_respect", "support", "conflict", "apology", "repair",
}
FRIENDSHIP_EVENTS = {"voluntary_time", "shared_humor", "reciprocal_support", "disclosure_comfort", "ritual", "shared_experience"}
MENTORSHIP_EVENTS = {"guidance_request", "teaching_event", "feedback", "progress_evidence", "role_boundary"}
SUPPORT_SIGNALS = {"workload_pressure", "frustration", "fatigue", "conflict", "uncertainty", "isolation", "explicit_request", "urgent_risk"}
SKILL_DOMAINS = {"operations", "engineering", "research", "hospitality", "governance", "communication", "character_architecture"}
MILESTONE_TYPES = {"tenure", "landmark_project", "service", "mastery", "mentorship", "recovery", "cultural_contribution", "steward_recognition"}


def _root(root: str | Path | None = None) -> Path:
    return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


def _iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _read_json(root: Path, rel: Path, default: Any) -> Any:
    path = root / rel
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(root: Path, rel: Path, payload: Any) -> None:
    path = root / rel; path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _read_jsonl(root: Path, rel: Path) -> list[dict[str, Any]]:
    path = root / rel
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _append_jsonl(root: Path, rel: Path, payload: Mapping[str, Any]) -> None:
    path = root / rel; path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(dict(payload), sort_keys=True) + "\n")


def _stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()[:16]
    return f"{prefix}-{digest}"


def clamp(value: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return round(max(lo, min(hi, float(value))), 4)


def migrate_affinity_graph(root: str | Path | None = None) -> dict[str, Any]:
    """Create the v1 affinity graph, migrating legacy relationship hints if present."""
    rootp = _root(root)
    existing = _read_json(rootp, AFFINITY_PATH, None)
    if isinstance(existing, Mapping) and existing.get("schema_version") == SCHEMA_VERSION:
        return dict(existing)
    graph = {"schema_version": SCHEMA_VERSION, "migrated_at": _iso(), "edges": {}, "diagnostics": []}
    legacy = _read_json(rootp, LEGACY_REL_PATH, {})
    rows = legacy if isinstance(legacy, list) else legacy.get("relationships", []) if isinstance(legacy, Mapping) else []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        src = row.get("source") or row.get("from") or row.get("resident_id")
        dst = row.get("target") or row.get("to") or row.get("other_resident_id") or row.get("steward_id")
        if not src or not dst:
            graph["diagnostics"].append({"severity": "warning", "code": "legacy_relationship_missing_endpoint"}); continue
        warmth = clamp(float(row.get("warmth", row.get("familiarity", 0))) / 100 if abs(float(row.get("warmth", row.get("familiarity", 0)))) > 1 else row.get("warmth", row.get("familiarity", 0)))
        set_affinity_dimension(graph, src, dst, "familiarity", warmth, confidence=0.35, evidence_refs=[str(LEGACY_REL_PATH)], privacy_class=row.get("privacy_class", "staff-only"), source_layer="migrated_legacy")
    _write_json(rootp, AFFINITY_PATH, graph)
    return graph


def set_affinity_dimension(graph: dict[str, Any], source: str, target: str, dimension: str, value: float, *, confidence: float, evidence_refs: Iterable[str], privacy_class: str = "staff-only", source_layer: str = "observed_evidence") -> dict[str, Any]:
    if dimension not in AFFINITY_DIMENSIONS:
        raise ValueError(f"unsupported affinity dimension: {dimension}")
    key = f"{source}->{target}"
    edge = graph.setdefault("edges", {}).setdefault(key, {"source_resident_id": source, "target_id": target, "dimensions": {}, "authority_effect": "none"})
    previous = edge["dimensions"].get(dimension, {}).get("value", 0.0)
    bounded = clamp(previous + clamp(value - previous, -0.15, 0.15))
    edge["dimensions"][dimension] = {"value": bounded, "confidence": clamp(confidence, 0, 1), "freshness": _iso(), "source_layer": source_layer, "evidence_refs": list(evidence_refs), "privacy_class": privacy_class, "change_rate_limited": bounded != value, "authority_effect": "none"}
    return edge["dimensions"][dimension]


def save_affinity_graph(root: str | Path | None, graph: Mapping[str, Any]) -> None:
    _write_json(_root(root), AFFINITY_PATH, dict(graph))


def present_affinity(root: str | Path | None, source: str, target: str, *, caller_clearance: str = "public") -> dict[str, Any]:
    graph = migrate_affinity_graph(root); edge = graph.get("edges", {}).get(f"{source}->{target}", {})
    dims = {}
    for name, rec in edge.get("dimensions", {}).items():
        if (name in PROTECTED_DIMENSIONS or rec.get("privacy_class") in PRIVATE_VISIBILITIES) and caller_clearance not in {"restricted", "private", "admin"}:
            dims[name] = {"redacted": True, "privacy_class": rec.get("privacy_class"), "authority_effect": "none"}
        else:
            dims[name] = rec
    return {"schema_version": SCHEMA_VERSION, "source_resident_id": source, "target_id": target, "dimensions": dims, "single_score_available": False, "authority_effect": "none"}


def record_trust_evidence(root: str | Path | None, source: str, target: str, event_type: str, *, domain: str = "general", magnitude: float = 0.05, evidence_refs: Iterable[str] = (), disputed: bool = False, privacy_class: str = "staff-only") -> dict[str, Any]:
    if event_type not in TRUST_EVENTS:
        raise ValueError(f"unsupported trust evidence: {event_type}")
    rootp = _root(root); graph = migrate_affinity_graph(rootp)
    if disputed:
        return {"applied": False, "reason": "disputed_evidence", "event_type": event_type}
    sign = -1 if event_type in {"promise_broken", "conflict"} else 1
    dim = "respect" if event_type in {"competence", "accurate_judgment"} else "trust"
    rec = set_affinity_dimension(graph, source, target, dim, sign * abs(magnitude), confidence=0.65, evidence_refs=evidence_refs, privacy_class=privacy_class, source_layer=f"trust_evidence:{domain}:{event_type}")
    _write_json(rootp, AFFINITY_PATH, graph)
    return {"applied": True, "dimension": dim, "state": rec, "authority_effect": "none"}


def evaluate_friendship_mentorship(events: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    counts = {"friendship": 0, "mentorship": 0}; private_refs = []
    for e in events:
        t = e.get("event_type")
        if t in FRIENDSHIP_EVENTS and e.get("reciprocal", False): counts["friendship"] += 1
        if t in MENTORSHIP_EVENTS and e.get("boundary_respected", True): counts["mentorship"] += 1
        if e.get("privacy_class") in PRIVATE_VISIBILITIES: private_refs.append(e.get("event_id"))
    return {"friendship_state": "emerging" if counts["friendship"] >= 2 else "insufficient_evidence", "mentorship_state": "active_professional" if counts["mentorship"] >= 2 else "insufficient_evidence", "private_event_refs": private_refs, "authority_effect": "none", "forced_reciprocity": False}


def propose_support_response(signal: Mapping[str, Any], *, resident_style: str = "practical") -> dict[str, Any]:
    kind = signal.get("signal_type")
    if kind not in SUPPORT_SIGNALS:
        return {"action": "no_action", "reason": "unsupported_signal"}
    if signal.get("declined"):
        return {"action": "respect_decline", "repeat_pressure_allowed": False, "authority_effect": "none"}
    if kind == "urgent_risk":
        return {"action": "route_to_institution", "institution": signal.get("institution", "safety_or_privacy_authority"), "consent_required_for_nonurgent": True, "authority_effect": "none"}
    return {"action": "offer_support", "style": resident_style, "requires_consent_before_intervention": True, "stores_private_content": False, "authority_effect": "none"}


def append_experience(root: str | Path | None, event: Mapping[str, Any]) -> dict[str, Any]:
    rootp = _root(root); payload = dict(event)
    required = ["resident_id", "occurred_at", "source_refs", "domains", "significance", "privacy_class", "confidence"]
    missing = [k for k in required if k not in payload]
    if missing: raise ValueError(f"missing experience fields: {missing}")
    payload.setdefault("schema_version", SCHEMA_VERSION); payload.setdefault("recorded_at", _iso()); payload.setdefault("participants", [])
    payload.setdefault("supersedes", None); payload.setdefault("idempotency_key", _stable_id("idem", payload))
    existing = _read_jsonl(rootp, EXPERIENCE_PATH)
    for rec in existing:
        if rec.get("idempotency_key") == payload["idempotency_key"]:
            return {"appended": False, "duplicate_of": rec["event_id"], "event": rec}
    payload.setdefault("event_id", _stable_id("EXP", payload))
    _append_jsonl(rootp, EXPERIENCE_PATH, payload)
    return {"appended": True, "event": payload}


def list_experiences(root: str | Path | None = None, *, resident_id: str | None = None, caller_clearance: str = "public") -> list[dict[str, Any]]:
    rows = _read_jsonl(_root(root), EXPERIENCE_PATH); out = []
    for r in rows:
        if resident_id and r.get("resident_id") != resident_id: continue
        if r.get("privacy_class") in PRIVATE_VISIBILITIES and caller_clearance not in {"restricted", "private", "admin"}: continue
        out.append(r)
    return sorted(out, key=lambda r: (r.get("occurred_at", ""), r.get("event_id", "")))


def propose_skill_growth(root: str | Path | None, resident_id: str, skill_id: str) -> dict[str, Any]:
    domain = skill_id.split(":", 1)[0]
    if domain not in SKILL_DOMAINS: raise ValueError(f"unapproved skill domain: {domain}")
    evidence = [e for e in list_experiences(root, resident_id=resident_id, caller_clearance="admin") if domain in e.get("domains", [])]
    strong = [e for e in evidence if e.get("significance") in {"reviewed_outcome", "deliberate_practice", "instruction", "demonstrated_transfer", "peer_review"}]
    current = _read_json(_root(root), SKILL_PATH, {}).get(resident_id, {}).get(skill_id, {"level": 0, "confidence": 0.0})
    increment = 1 if len(strong) >= max(2, current.get("level", 0) + 1) else 0
    return {"resident_id": resident_id, "skill_id": skill_id, "approved_domain": domain, "current_level": current.get("level", 0), "proposed_level": min(5, current.get("level", 0) + increment), "evidence_refs": [e["event_id"] for e in strong], "bounded_increment": increment <= 1, "review_required": True}


def adjust_confidence(root: str | Path | None, resident_id: str, domain: str, evidence_event_id: str, outcome: str) -> dict[str, Any]:
    rootp = _root(root); data = _read_json(rootp, CONFIDENCE_PATH, {})
    rec = data.setdefault(resident_id, {}).setdefault(domain, {"baseline": 0.0, "current": 0.0, "evidence_refs": [], "volatility": 0.1, "recovery_state": "stable"})
    delta = {"success": 0.08, "failure": -0.08, "preparation": 0.04, "feedback": 0.03, "uncertainty": -0.03, "recovery": 0.06}.get(outcome, 0.0)
    rec["current"] = clamp(rec["current"] + delta); rec["evidence_refs"].append(evidence_event_id); rec["competence_authority_effect"] = "none"
    if abs(rec["current"] - rec["baseline"]) > 0.6: rec["review_status"] = "oscillation_review_required"
    _write_json(rootp, CONFIDENCE_PATH, data); return rec


def refine_preference(root: str | Path | None, resident_id: str, preference_id: str, *, context: str, evidence_refs: Iterable[str], classification: str = "durable", protected_trait: bool = False) -> dict[str, Any]:
    if protected_trait and classification != "explicit_self_correction":
        return {"applied": False, "reason": "protected_identity_anchor"}
    rootp = _root(root); data = _read_json(rootp, PREFERENCE_PATH, {})
    rec = {"preference_id": preference_id, "context": context, "strength": 0.2 if classification == "temporary" else 0.55, "stability": classification, "provenance": list(evidence_refs), "exceptions": [], "last_reviewed": _iso(), "protected_trait": protected_trait}
    data.setdefault(resident_id, {})[preference_id] = rec; _write_json(rootp, PREFERENCE_PATH, data); return {"applied": True, "preference": rec}


def propose_milestone(root: str | Path | None, resident_id: str, milestone_type: str, evidence_refs: Iterable[str], summary: str, *, visibility_class: str = "staff-only", approval_state: str = "candidate") -> dict[str, Any]:
    if milestone_type not in MILESTONE_TYPES: raise ValueError(f"unsupported milestone type: {milestone_type}")
    rootp = _root(root); data = _read_json(rootp, MILESTONE_PATH, {"schema_version": SCHEMA_VERSION, "milestones": []})
    rec = {"milestone_id": _stable_id("MS", {"resident_id": resident_id, "type": milestone_type, "evidence": list(evidence_refs)}), "resident_id": resident_id, "milestone_type": milestone_type, "evidence_refs": list(evidence_refs), "approval_state": approval_state, "visibility_class": visibility_class, "occurred_at": _iso(), "narrative_summary": summary, "supersedes": None}
    if any(m["milestone_id"] == rec["milestone_id"] for m in data["milestones"]):
        return {"created": False, "duplicate": True, "milestone": rec}
    data["milestones"].append(rec); _write_json(rootp, MILESTONE_PATH, data); return {"created": True, "milestone": rec}


def review_affinity(root: str | Path | None = None, *, caller_clearance: str = "public") -> dict[str, Any]:
    graph = migrate_affinity_graph(root); diagnostics = []
    for key, edge in graph.get("edges", {}).items():
        dims = edge.get("dimensions", {})
        if len({round(v.get("value", 0), 2) for v in dims.values()}) == 1 and len(dims) > 4:
            diagnostics.append({"severity": "warning", "code": "possible_one_score_collapse", "edge": key})
        if any(v.get("value", 0) > 0.8 and not v.get("evidence_refs") for v in dims.values()):
            diagnostics.append({"severity": "error", "code": "unsupported_intimacy_or_affinity", "edge": key})
    return {"schema_version": SCHEMA_VERSION, "reviewed_at": _iso(), "diagnostics": diagnostics, "requires_independent_validation": True, "steward_acceptance_required": True, "private_details_redacted": caller_clearance not in {"restricted", "private", "admin"}}


def validate_affinity_growth_runtime(root: str | Path | None = None) -> dict[str, Any]:
    migrate_affinity_graph(root); review = review_affinity(root, caller_clearance="admin")
    paths = [AFFINITY_PATH, EXPERIENCE_PATH, SKILL_PATH, CONFIDENCE_PATH, PREFERENCE_PATH, MILESTONE_PATH]
    return {"schema_version": SCHEMA_VERSION, "valid": not any(d.get("severity") == "error" for d in review["diagnostics"]), "checked_boundaries": ["directional_affinity", "privacy_redaction", "append_only_experience", "bounded_growth", "confidence_not_competence", "preferences_under_existing_authority", "candidate_milestones_require_approval", "no_authority_from_affinity"], "persistence_paths": [str(p) for p in paths], "migration": str(AFFINITY_PATH), "diagnostics": review["diagnostics"]}
