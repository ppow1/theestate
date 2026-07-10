from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from estate.core.paths import ESTATE_ROOT

STATES = ("active", "reflection_due", "in_reflection", "continuity_ready", "new_cycle_ready", "archived")
CLASSIFICATIONS = ("Public", "Estate Internal", "Restricted", "Steward Only", "Local Only")
SCHEMA_VERSION = "character-continuity-record-v1"
ARTIFACT_VERSION = "character-continuity-artifact-v1"
MAX_PUBLIC_ITEM_CHARS = 320


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _slug(value: str) -> str:
    return "".join(c.lower() if c.isalnum() else "-" for c in value).strip("-") or "resident"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def continuity_root(root: Path | None = None) -> Path:
    return (root or ESTATE_ROOT) / "operations" / "residents" / "continuity"


def resident_dir(resident_id: str, root: Path | None = None) -> Path:
    return continuity_root(root) / _slug(resident_id)


def cycle_path(resident_id: str, cycle_id: str, root: Path | None = None) -> Path:
    return resident_dir(resident_id, root) / "cycles" / f"{cycle_id}.json"


def artifact_path(resident_id: str, cycle_id: str, root: Path | None = None) -> Path:
    return resident_dir(resident_id, root) / "artifacts" / f"{cycle_id}_continuity.json"


def index_path(resident_id: str, root: Path | None = None) -> Path:
    return resident_dir(resident_id, root) / "index.json"


def _safe_items(items: list[Any], allow_private: bool) -> list[str]:
    safe = []
    for item in items:
        if isinstance(item, dict):
            classification = item.get("classification", "Estate Internal")
            text = str(item.get("text", "")).strip()
            summary_safe = bool(item.get("summary_safe", classification in ("Public", "Estate Internal")))
        else:
            classification = "Estate Internal"
            text = str(item).strip()
            summary_safe = True
        if not text:
            continue
        if classification in ("Restricted", "Steward Only", "Local Only") and not allow_private:
            continue
        if not summary_safe and not allow_private:
            continue
        safe.append(text[:MAX_PUBLIC_ITEM_CHARS])
    return safe


def create_cycle(resident_id: str, resident_name: str, *, root: Path | None = None, predecessor_cycle_id: str | None = None, initialized_from_artifact_id: str | None = None, classification: str = "Estate Internal") -> dict[str, Any]:
    if classification not in CLASSIFICATIONS:
        raise ValueError(f"Unsupported classification: {classification}")
    base = resident_dir(resident_id, root)
    cycles = sorted((base / "cycles").glob("cycle-*.json")) if (base / "cycles").exists() else []
    cycle_number = len(cycles) + 1
    cycle_id = f"cycle-{cycle_number:04d}"
    record = {
        "schema_version": SCHEMA_VERSION,
        "resident_identity": {"resident_id": resident_id, "resident_name": resident_name},
        "cycle": {"cycle_id": cycle_id, "cycle_number": cycle_number, "state": "active", "started_at": _now(), "predecessor_cycle_id": predecessor_cycle_id},
        "working_journal_summary": [],
        "lessons_retained": [],
        "contradictions_unresolved_drift": [],
        "reflection_outcome": {},
        "continuity_artifact_ref": initialized_from_artifact_id,
        "next_cycle_initialization": {"initialized_from_artifact_id": initialized_from_artifact_id, "carry_full_transcript": False},
        "classification": {"level": classification, "protected_private": classification in ("Restricted", "Steward Only", "Local Only"), "public_output_allowed": classification in ("Public", "Estate Internal")},
        "review_hooks": {"helen_review_required": False, "helen_review_status": "not_requested", "ingrid_classification_required": True, "ingrid_classification_status": "pending"},
        "audit": {"created_at": _now(), "updated_at": _now(), "predecessor_cycle_id": predecessor_cycle_id, "successor_cycle_id": None},
    }
    _write_json(cycle_path(resident_id, cycle_id, root), record)
    _write_json(index_path(resident_id, root), {"resident_id": resident_id, "resident_name": resident_name, "current_cycle_id": cycle_id, "cycles": [p.stem for p in cycles] + [cycle_id]})
    return record


def load_current(resident_id: str, root: Path | None = None) -> dict[str, Any]:
    idx = _read_json(index_path(resident_id, root))
    return _read_json(cycle_path(resident_id, idx["current_cycle_id"], root))


def save_record(record: dict[str, Any], root: Path | None = None) -> None:
    record["audit"]["updated_at"] = _now()
    rid = record["resident_identity"]["resident_id"]
    cid = record["cycle"]["cycle_id"]
    _write_json(cycle_path(rid, cid, root), record)


def prepare_reflection(resident_id: str, evidence: dict[str, Any], *, root: Path | None = None) -> dict[str, Any]:
    record = load_current(resident_id, root)
    if record["cycle"]["state"] not in ("active", "reflection_due"):
        raise ValueError("Cycle is not eligible for reflection preparation")
    record["working_journal_summary"] = _safe_items(evidence.get("working_journal_summary", []), False)
    record["lessons_retained"] = _safe_items(evidence.get("lessons_retained", []), False)
    record["contradictions_unresolved_drift"] = _safe_items(evidence.get("contradictions_unresolved_drift", []), False)
    record["cycle"]["state"] = "in_reflection"
    record["review_hooks"]["helen_review_required"] = bool(evidence.get("helen_review_required", True))
    record["review_hooks"]["helen_review_status"] = "pending" if record["review_hooks"]["helen_review_required"] else "not_required"
    record["review_hooks"]["ingrid_classification_status"] = "pending"
    save_record(record, root)
    return record


def create_continuity(resident_id: str, reflection_outcome: dict[str, Any], *, root: Path | None = None, public: bool = True) -> dict[str, Any]:
    record = load_current(resident_id, root)
    if record["cycle"]["state"] != "in_reflection":
        raise ValueError("Cycle must be in_reflection before continuity creation")
    allow_private = not public
    artifact = {
        "schema_version": ARTIFACT_VERSION,
        "artifact_id": f"{record['cycle']['cycle_id']}-continuity",
        "resident_identity": record["resident_identity"],
        "source_cycle_id": record["cycle"]["cycle_id"],
        "created_at": _now(),
        "stable_identity": record["resident_identity"],
        "lessons_retained": _safe_items(record.get("lessons_retained", []), allow_private),
        "unresolved_drift": _safe_items(record.get("contradictions_unresolved_drift", []), allow_private),
        "reflection_outcome": {k: v for k, v in reflection_outcome.items() if allow_private or k not in {"private_notes", "restricted_notes"}},
        "next_cycle_initialization": {"carry_full_transcript": False, "use_artifact_id": f"{record['cycle']['cycle_id']}-continuity"},
        "classification": {"level": "Estate Internal" if public else record["classification"]["level"], "private_content_excluded": public},
        "audit": {"source_cycle_id": record["cycle"]["cycle_id"], "successor_cycle_id": None},
    }
    _write_json(artifact_path(resident_id, record["cycle"]["cycle_id"], root), artifact)
    record["reflection_outcome"] = artifact["reflection_outcome"]
    record["continuity_artifact_ref"] = artifact["artifact_id"]
    record["cycle"]["state"] = "continuity_ready"
    save_record(record, root)
    return artifact


def start_next_cycle(resident_id: str, *, root: Path | None = None) -> dict[str, Any]:
    current = load_current(resident_id, root)
    if current["cycle"]["state"] not in ("continuity_ready", "new_cycle_ready"):
        raise ValueError("Continuity artifact is required before starting a new cycle")
    current["cycle"]["state"] = "archived"
    identity = current["resident_identity"]
    new_record = create_cycle(identity["resident_id"], identity["resident_name"], root=root, predecessor_cycle_id=current["cycle"]["cycle_id"], initialized_from_artifact_id=current["continuity_artifact_ref"], classification=current["classification"]["level"])
    current["audit"]["successor_cycle_id"] = new_record["cycle"]["cycle_id"]
    save_record(current, root)
    return new_record


def status(resident_id: str, root: Path | None = None) -> dict[str, Any]:
    return load_current(resident_id, root)
