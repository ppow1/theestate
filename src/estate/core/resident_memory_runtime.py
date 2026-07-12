"""Governed resident memory and relationship maturation runtime.

This module extends the existing resident identity composer and relationship graph
without replacing them.  It stores only approved, source-lined records in one
JSON artifact and keeps conversation turns/proposals separate from durable truth.
"""
from __future__ import annotations

import copy, hashlib, json, re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from estate.core.paths import ESTATE_ROOT
from estate.core.relationship_graph import load_relationship_context
from estate.core.resident_registry_snapshot import build_resident_registry_snapshot

MEMORY_SCHEMA_VERSION = "resident_memory_runtime.v1"
MEMORY_PATH = Path("runtime/resident_memory/memory_store.json")
AUDIT_PATH = Path("runtime/resident_memory/audit_log.jsonl")
REPAIR_PATH = Path("runtime/resident_memory/repair_receipts.jsonl")
DURABLE_STATES = {"approved", "active", "superseded", "retired", "corrected"}
PRIVATE_SCOPES = {"private", "resident_private", "steward_restricted", "evelyn_steward_private"}
PERSONAL_CLASSES = {"lesson", "preference", "routine", "milestone", "aversion", "comfort", "commitment", "self_understanding"}
INSTITUTIONAL_CLASSES = {"decision", "lesson_learned", "institutional_milestone", "incident", "convention", "operating_context"}
EPISODE_CLASSES = {"episode"}
RELATIONSHIP_CLASSES = {"trust_familiarity", "conflict_repair", "ritual_milestone"}


def _root(root=None) -> Path:
    return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _key(value: Any) -> str:
    return re.sub(r"[^a-z0-9-]+", "-", str(value or "").lower()).strip("-") or "unknown"


def _hash(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()[:16]


def _empty_store() -> dict[str, Any]:
    return {"schema_version": MEMORY_SCHEMA_VERSION, "records": [], "relationship_proposals": [], "updated_at": None}


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return copy.deepcopy(default)
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, sort_keys=True) + "\n")


def _source_lines(evidence: Sequence[Mapping[str, Any]]) -> list[str]:
    lines = []
    for item in evidence:
        source = item.get("source") or item.get("path")
        if source:
            suffix = f"#{item.get('line')}" if item.get("line") else ""
            lines.append(f"{source}{suffix}")
    return lines


def _authorize(actor: str, operation: str, record: Mapping[str, Any] | None = None) -> bool:
    if operation in {"read", "query", "challenge"}:
        return True
    if actor in {"Steward", "Ingrid", "Helen", "Validation", "Chief Architect", "Engineering"}:
        return True
    if record and actor and _key(actor) == _key(record.get("subject")) and operation in {"propose", "flag"}:
        return True
    return False


class ResidentMemoryRuntime:
    """Single governed store for resident, episodic, institutional, and relationship memory."""

    def __init__(self, root=None):
        self.root = _root(root)
        self.path = self.root / MEMORY_PATH
        self.audit_path = self.root / AUDIT_PATH
        self.repair_path = self.root / REPAIR_PATH

    def load(self) -> dict[str, Any]:
        data = _read_json(self.path, _empty_store())
        if data.get("schema_version") != MEMORY_SCHEMA_VERSION:
            data = self.migrate(data)
        return data

    def save(self, store: Mapping[str, Any]) -> dict[str, Any]:
        payload = dict(store)
        payload["schema_version"] = MEMORY_SCHEMA_VERSION
        payload["updated_at"] = _now()
        _write_json(self.path, payload)
        return payload

    def migrate(self, data: Mapping[str, Any]) -> dict[str, Any]:
        records = data.get("records") if isinstance(data.get("records"), list) else []
        migrated = _empty_store(); migrated["records"] = [self._normalize_record(r, actor="migration") for r in records if isinstance(r, Mapping)]
        self.save(migrated)
        self._audit("migration", "system", {"from_schema": data.get("schema_version"), "record_count": len(migrated["records"])})
        return migrated

    def _audit(self, operation: str, actor: str, payload: Mapping[str, Any]) -> None:
        _append_jsonl(self.audit_path, {"at": _now(), "operation": operation, "actor": actor, "payload_hash": _hash(payload), "payload": payload})

    def _normalize_record(self, record: Mapping[str, Any], *, actor: str) -> dict[str, Any]:
        evidence = list(record.get("evidence") or [])
        subject = _key(record.get("subject") or record.get("resident_id") or "estate")
        memory_class = record.get("memory_class") or "general"
        rid = record.get("memory_id") or f"mem-{_hash({'subject': subject, 'class': memory_class, 'content': record.get('content'), 'evidence': evidence})}"
        now = _now()
        return {
            "memory_id": rid, "subject": subject, "memory_class": memory_class, "content": record.get("content") or record.get("summary") or "",
            "source_lineage": list(record.get("source_lineage") or _source_lines(evidence)), "evidence": evidence,
            "classification": record.get("classification") or "Estate Internal", "confidence": float(record.get("confidence", 0.5)),
            "created_at": record.get("created_at") or now, "updated_at": now, "retention": record.get("retention") or "reviewed_durable",
            "review_state": record.get("review_state") or "proposed", "disclosure_scope": record.get("disclosure_scope") or "resident_private",
            "status": record.get("status") or "proposed", "supersedes": list(record.get("supersedes") or []), "lineage": list(record.get("lineage") or []),
            "metadata": dict(record.get("metadata") or {}), "created_by": record.get("created_by") or actor,
        }

    def propose_memory(self, record: Mapping[str, Any], *, actor: str = "Steward", reason: str = "governed promotion proposal") -> dict[str, Any]:
        if not _authorize(actor, "propose", record):
            raise PermissionError("actor cannot propose memory")
        normalized = self._normalize_record({**record, "review_state": record.get("review_state") or "needs_review", "status": "proposed"}, actor=actor)
        store = self.load(); store.setdefault("records", []).append(normalized); self.save(store)
        self._audit("propose_memory", actor, {"memory_id": normalized["memory_id"], "reason": reason})
        return normalized

    def promote_memory(self, memory_id: str, *, actor: str = "Steward", reason: str = "approved durable promotion") -> dict[str, Any]:
        store = self.load(); rec = self._find(store, memory_id)
        if not rec or not _authorize(actor, "promote", rec):
            raise PermissionError("memory missing or actor cannot promote")
        if not rec.get("evidence") and rec.get("memory_class") not in {"self_understanding"}:
            raise ValueError("durable promotion requires evidence")
        rec.update({"status": "active", "review_state": "approved", "updated_at": _now()}); rec.setdefault("lineage", []).append({"operation": "promote", "actor": actor, "reason": reason, "at": _now()})
        self.save(store); self._audit("promote_memory", actor, {"memory_id": memory_id, "reason": reason})
        return rec

    def write_memory(self, record: Mapping[str, Any], *, actor: str = "Steward", reason: str = "approved memory write") -> dict[str, Any]:
        rec = self.propose_memory(record, actor=actor, reason=reason)
        return self.promote_memory(rec["memory_id"], actor=actor, reason=reason)

    def _find(self, store: Mapping[str, Any], memory_id: str) -> dict[str, Any] | None:
        return next((r for r in store.get("records", []) if r.get("memory_id") == memory_id), None)

    def query_memories(self, *, subject: str | None = None, memory_classes: Iterable[str] | None = None, surface_id: str = "resident", actor: str = "Steward", include_proposed: bool = False, limit: int = 8) -> list[dict[str, Any]]:
        wanted_classes = set(memory_classes or [])
        records = []
        for rec in self.load().get("records", []):
            if subject and _key(rec.get("subject")) != _key(subject) and _key(rec.get("subject")) != "estate":
                continue
            if wanted_classes and rec.get("memory_class") not in wanted_classes:
                continue
            if not include_proposed and rec.get("status") not in DURABLE_STATES:
                continue
            if rec.get("status") in {"retired", "quarantined"} and not include_proposed:
                continue
            if not self._can_disclose(rec, surface_id=surface_id, actor=actor):
                continue
            records.append(copy.deepcopy(rec))
        return sorted(records, key=lambda r: (r.get("confidence", 0), r.get("updated_at", "")), reverse=True)[:limit]

    def _can_disclose(self, rec: Mapping[str, Any], *, surface_id: str, actor: str) -> bool:
        scope = rec.get("disclosure_scope")
        if surface_id.startswith(("conference", "room")) and scope in PRIVATE_SCOPES:
            return False
        if scope in {"steward_restricted", "evelyn_steward_private"} and actor not in {"Steward", "Ingrid"}:
            return False
        return True

    def supersede_memory(self, memory_id: str, replacement: Mapping[str, Any], *, actor: str = "Steward", reason: str = "superseded") -> dict[str, Any]:
        store = self.load(); old = self._find(store, memory_id)
        if not old or not _authorize(actor, "supersede", old):
            raise PermissionError("memory missing or actor cannot supersede")
        old.update({"status": "superseded", "review_state": "superseded", "updated_at": _now()})
        new = self._normalize_record({**replacement, "supersedes": [memory_id], "status": "active", "review_state": "approved"}, actor=actor)
        new["lineage"].append({"operation": "supersede", "actor": actor, "reason": reason, "previous": memory_id, "at": _now()})
        store["records"].append(new); self.save(store); self._audit("supersede_memory", actor, {"old": memory_id, "new": new["memory_id"], "reason": reason})
        return new

    def retire_memory(self, memory_id: str, *, actor: str = "Steward", reason: str = "retired") -> dict[str, Any]:
        store = self.load(); rec = self._find(store, memory_id)
        if not rec or not _authorize(actor, "retire", rec):
            raise PermissionError("memory missing or actor cannot retire")
        rec.update({"status": "retired", "review_state": "retired", "updated_at": _now()}); rec.setdefault("lineage", []).append({"operation": "retire", "actor": actor, "reason": reason, "at": _now()})
        self.save(store); self._audit("retire_memory", actor, {"memory_id": memory_id, "reason": reason})
        return rec

    def correct_memory(self, memory_id: str, patch: Mapping[str, Any], *, actor: str = "Steward", reason: str = "correction") -> dict[str, Any]:
        return self.supersede_memory(memory_id, {**(self._find(self.load(), memory_id) or {}), **patch}, actor=actor, reason=reason)

    def create_episode(self, *, participants: Sequence[str], event_time: str, summary: str, evidence: Sequence[Mapping[str, Any]], actor: str = "Steward", **extra: Any) -> dict[str, Any]:
        record = {"subject": extra.get("subject") or _key(participants[0] if participants else "estate"), "memory_class": "episode", "content": summary, "evidence": list(evidence), "metadata": {"participants": [_key(p) for p in participants], "event_time": event_time, "place": extra.get("place"), "resident_perspective": extra.get("resident_perspective"), "verified_facts": extra.get("verified_facts", []), "feelings": extra.get("feelings", []), "uncertainty": extra.get("uncertainty", [])}, "disclosure_scope": extra.get("disclosure_scope", "resident_private"), "classification": extra.get("classification", "Estate Internal"), "confidence": extra.get("confidence", 0.7)}
        return self.write_memory(record, actor=actor, reason="approved episodic memory")

    def propose_long_term_memory(self, subject: str, memory_class: str, content: str, evidence: Sequence[Mapping[str, Any]], *, actor: str = "Steward", approval: bool = False, **extra: Any) -> dict[str, Any]:
        if memory_class not in PERSONAL_CLASSES:
            raise ValueError("unsupported personal memory class")
        rec = self.propose_memory({"subject": subject, "memory_class": memory_class, "content": content, "evidence": list(evidence), "metadata": {"state": extra.get("state", "tentative"), "review_after": extra.get("review_after") or (datetime.now(timezone.utc) + timedelta(days=90)).date().isoformat(), "decay": extra.get("decay", "class_policy")}, "disclosure_scope": extra.get("disclosure_scope", "resident_private"), "confidence": extra.get("confidence", 0.55)}, actor=actor, reason="long-term personal memory proposal")
        return self.promote_memory(rec["memory_id"], actor=actor, reason="explicitly approved long-term personal memory") if approval else rec

    def write_institutional_memory(self, memory_class: str, content: str, evidence: Sequence[Mapping[str, Any]], *, actor: str = "Steward", state: str = "current_policy", **extra: Any) -> dict[str, Any]:
        if memory_class not in INSTITUTIONAL_CLASSES:
            raise ValueError("unsupported institutional memory class")
        return self.write_memory({"subject": "estate", "memory_class": memory_class, "content": content, "evidence": list(evidence), "metadata": {"institutional_state": state, "canonical_source_required": True}, "disclosure_scope": extra.get("disclosure_scope", "shared_authorized"), "classification": extra.get("classification", "Estate Internal"), "confidence": extra.get("confidence", 0.8)}, actor=actor, reason="approved institutional memory")

    def inspect(self, *, actor: str = "Steward", surface_id: str = "resident", include_restricted: bool = False) -> dict[str, Any]:
        records = self.query_memories(surface_id=surface_id, actor=actor, include_proposed=True, limit=10_000)
        if not include_restricted:
            records = [{k: v for k, v in r.items() if k != "content" or self._can_disclose(r, surface_id=surface_id, actor=actor)} for r in records]
        return {"schema_version": MEMORY_SCHEMA_VERSION, "records": records, "diagnostics": self.diagnostics(actor=actor, surface_id=surface_id)}

    def diagnostics(self, *, actor: str = "Steward", surface_id: str = "resident") -> list[dict[str, Any]]:
        store = self.load(); out = []
        seen: dict[tuple[str, str, str], str] = {}
        registry_keys = {_key(r.get("id") or r.get("name")) for r in build_resident_registry_snapshot(self.root).get("residents", [])}
        for rec in store.get("records", []):
            if not self._can_disclose(rec, surface_id=surface_id, actor=actor):
                continue
            sig = (_key(rec.get("subject")), str(rec.get("memory_class")), str(rec.get("content")))
            if sig in seen: out.append({"type": "duplicate_memory", "memory_id": rec.get("memory_id"), "duplicate_of": seen[sig], "severity": "review"})
            seen[sig] = rec.get("memory_id")
            if rec.get("subject") not in {"estate", "steward"} and _key(rec.get("subject")) not in registry_keys:
                out.append({"type": "orphaned_subject", "memory_id": rec.get("memory_id"), "subject": rec.get("subject"), "severity": "warning"})
            if not rec.get("evidence") and rec.get("status") in DURABLE_STATES:
                out.append({"type": "unsupported_claim", "memory_id": rec.get("memory_id"), "severity": "blocking"})
            if surface_id.startswith(("conference", "room")) and rec.get("disclosure_scope") in PRIVATE_SCOPES:
                out.append({"type": "privacy_conflict", "memory_id": rec.get("memory_id"), "severity": "blocking"})
        by_subject_class: dict[tuple[str, str], list[dict[str, Any]]] = {}
        for rec in store.get("records", []): by_subject_class.setdefault((_key(rec.get("subject")), rec.get("memory_class")), []).append(rec)
        for group in by_subject_class.values():
            active = [r for r in group if r.get("status") == "active"]
            if len(active) > 1 and len({r.get("content") for r in active}) > 1:
                out.append({"type": "possible_contradiction", "memory_ids": [r.get("memory_id") for r in active], "severity": "review"})
        return out

    def repair(self, operation: str, memory_ids: Sequence[str], *, actor: str = "Steward", reason: str, patch: Mapping[str, Any] | None = None) -> dict[str, Any]:
        if not _authorize(actor, operation):
            raise PermissionError("actor cannot repair memory")
        before = self.load(); after = copy.deepcopy(before); touched = []
        for mid in memory_ids:
            rec = self._find(after, mid)
            if not rec: continue
            touched.append(mid)
            if operation == "quarantine": rec.update({"status": "quarantined", "review_state": "quarantined"})
            elif operation == "retire": rec.update({"status": "retired", "review_state": "retired"})
            elif operation == "patch" and patch: rec.update(patch); rec["review_state"] = "corrected"
            rec.setdefault("lineage", []).append({"operation": operation, "actor": actor, "reason": reason, "at": _now()})
        self.save(after)
        receipt = {"repair_id": f"repair-{_hash({'op': operation, 'ids': touched, 'at': _now()})}", "operation": operation, "actor": actor, "reason": reason, "memory_ids": touched, "before_hash": _hash(before), "after_hash": _hash(after), "rollback_instruction": "restore before_hash snapshot from VCS or audit backup", "at": _now()}
        _append_jsonl(self.repair_path, receipt); self._audit("repair", actor, receipt)
        return receipt

    def propose_relationship_change(self, participants: Sequence[str], dimension: str, value: float, evidence: Sequence[Mapping[str, Any]], *, actor: str = "Steward", disclosure_scope: str = "resident_private", state: str = "proposed") -> dict[str, Any]:
        proposal = {"proposal_id": f"rel-{_hash({'p': participants, 'd': dimension, 'v': value, 'e': evidence})}", "participants": [_key(p) for p in participants], "dimension": dimension, "bounded_value": max(-1.0, min(1.0, float(value))), "evidence": list(evidence), "source_lineage": _source_lines(evidence), "disclosure_scope": disclosure_scope, "review_state": state, "status": "proposed", "created_at": _now(), "actor": actor, "asymmetric": True}
        store = self.load(); store.setdefault("relationship_proposals", []).append(proposal); self.save(store); self._audit("propose_relationship_change", actor, proposal)
        return proposal

    def relationship_review(self, *, resident: str | None = None, actor: str = "Steward", surface_id: str = "resident") -> dict[str, Any]:
        graph = load_relationship_context(resident or "alfred", surface_id=surface_id, root=self.root)
        memories = self.query_memories(subject=resident, memory_classes=RELATIONSHIP_CLASSES, actor=actor, surface_id=surface_id, include_proposed=True, limit=1000) if resident else self.query_memories(memory_classes=RELATIONSHIP_CLASSES, actor=actor, surface_id=surface_id, include_proposed=True, limit=1000)
        findings = self.diagnostics(actor=actor, surface_id=surface_id)
        store = self.load()
        for proposal in store.get("relationship_proposals", []):
            if proposal.get("status") == "proposed" and not proposal.get("evidence"):
                findings.append({"type": "unsupported_relationship_proposal", "proposal_id": proposal.get("proposal_id"), "severity": "review"})
        if graph.get("redactions"):
            findings.append({"type": "privacy_redactions_present", "redactions": graph.get("redactions"), "severity": "info"})
        return {"schema_version": "resident_relationship_review.v1", "resident": _key(resident) if resident else "estate", "graph_hash": graph.get("graph_hash"), "relationship_memory_count": len(memories), "unresolved_proposals": [p for p in store.get("relationship_proposals", []) if p.get("status") == "proposed"], "findings": findings, "routes": {"privacy": "Ingrid", "continuity_health": "Helen", "implementation": "Engineering", "acceptance": "Steward/Chief Architect"}}


def retrieve_memory_context(resident: str, *, surface_id: str = "resident", root=None, actor: str = "Steward", limit: int = 6) -> dict[str, Any]:
    runtime = ResidentMemoryRuntime(root)
    records = runtime.query_memories(subject=resident, surface_id=surface_id, actor=actor, limit=limit)
    institutional = runtime.query_memories(subject="estate", surface_id=surface_id, actor=actor, limit=max(1, limit // 2))
    return {"schema_version": MEMORY_SCHEMA_VERSION, "resident_id": _key(resident), "canonical_truth_only": True, "records": records + institutional, "diagnostics": runtime.diagnostics(actor=actor, surface_id=surface_id)}
