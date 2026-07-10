"""Merge discovery canonicalization and historical backfill controls."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from estate.core.post_merge_audit import PostMergeAuditRequest

BASE = Path("runtime/merge_discovery")
DISCOVERIES = BASE / "discoveries"
CANONICAL = BASE / "canonical"
STATUS = BASE / "status"
REQUESTS = Path("runtime/post_merge_audit/requests")
EVIDENCE_RANK = {
    "commit_message": 1,
    "changed_path": 1,
    "proposal_commit": 2,
    "pending_package_commit": 2,
    "receipt_filename": 3,
    "merge": 3,
    "merge_commit": 3,
    "implementation": 4,
    "implementation_commit": 4,
    "receipt_work_package_id": 5,
    "completion_receipt": 5,
    "completion_receipt_commit": 5,
}
DEFAULT_LIMITS = {
    "max_commits": 50,
    "max_age_hours": 48,
    "max_candidates": 20,
    "max_requests_per_cycle": 5,
    "minimum_evidence_level": "implementation",
}
ACTIVE_STATES = {"pending", "claimed", "running_validation", "running_ring2"}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _rank(record: dict[str, Any]) -> int:
    md = record.get("metadata") or {}
    return max(
        EVIDENCE_RANK.get(str(record.get("evidence_level") or ""), 0),
        EVIDENCE_RANK.get(str(record.get("correlation_method") or ""), 0),
        EVIDENCE_RANK.get(str(md.get("evidence_level") or ""), 0),
        EVIDENCE_RANK.get(str(record.get("source_kind") or ""), 0),
    )


def evidence_level(record: dict[str, Any]) -> str:
    rank = _rank(record)
    if rank >= 5: return "receipt"
    if rank >= 4: return "implementation"
    if rank >= 3: return "merge"
    if rank >= 2: return "proposal"
    return "commit-message-only"


def _eligible(record: dict[str, Any], minimum: str) -> bool:
    minimum_rank = {"commit-message-only": 1, "proposal": 2, "merge": 3, "implementation": 4, "receipt": 5}.get(minimum, 4)
    return _rank(record) >= minimum_rank


@dataclass
class BackfillPolicy:
    mode: str = "quarantine"
    max_candidates: int = DEFAULT_LIMITS["max_candidates"]
    max_requests_per_cycle: int = DEFAULT_LIMITS["max_requests_per_cycle"]
    minimum_evidence_level: str = DEFAULT_LIMITS["minimum_evidence_level"]


class MergeDiscoveryConsolidator:
    def __init__(self, root: Path | None = None) -> None:
        self.root = Path(root) if root is not None else Path.cwd()

    @property
    def requests_dir(self) -> Path:
        return self.root / REQUESTS

    @property
    def discoveries_dir(self) -> Path:
        return self.root / DISCOVERIES

    def load_records(self) -> list[dict[str, Any]]:
        if not self.discoveries_dir.exists(): return []
        return [_read(p) for p in sorted(self.discoveries_dir.glob("*.json"))]

    def consolidate(self, target_id: str = "estate-main", *, records: list[dict[str, Any]] | None = None, mode: str = "quarantine", max_candidates: int = 20, max_requests_per_cycle: int = 5, minimum_evidence_level: str = "implementation") -> dict[str, Any]:
        records = [dict(r) for r in (records if records is not None else self.load_records()) if r.get("target_id") == target_id and r.get("work_package_id")]
        ambiguous = [r for r in records if r.get("state") == "ambiguous"]
        eligible = [r for r in records if r.get("state") != "ambiguous" and _eligible(r, minimum_evidence_level)]
        if len(eligible) > max_candidates:
            eligible = eligible[-max_candidates:]
            limit_reached = True
        else:
            limit_reached = False
        by_wp: dict[tuple[str, str], list[dict[str, Any]]] = {}
        for r in eligible:
            by_wp.setdefault((r["target_id"], r["work_package_id"]), []).append(r)
        canonical = []
        superseded = []
        quarantined = []
        admitted = []
        suppressed = 0
        for (_target, wp), group in sorted(by_wp.items()):
            strongest = sorted(group, key=lambda r: (_rank(r), r.get("created_at", ""), r.get("source_commit") or ""), reverse=True)[0]
            promoted_revision = strongest.get("promoted_revision") or strongest.get("source_commit") or strongest.get("source_reference")
            canonical_id = f"mc-{target_id}-{wp}-{str(promoted_revision)[:12]}"
            strongest.update({"state": "canonical", "canonical_discovery_id": canonical_id, "promoted_revision": promoted_revision, "evidence_level": evidence_level(strongest), "backfill_mode": mode})
            canonical.append(strongest)
            for weak in group:
                if weak.get("discovery_id") == strongest.get("discovery_id"): continue
                weak.update({"state": "superseded", "superseded_by": strongest.get("discovery_id"), "canonical_discovery_id": canonical_id, "promoted_revision": promoted_revision})
                superseded.append(weak); suppressed += 1
            if mode == "admit" and len(admitted) < max_requests_per_cycle:
                req = self._ensure_request(strongest, canonical_id)
                strongest["audit_request_id"] = req.get("audit_id")
                admitted.append(strongest)
            else:
                strongest["state"] = "quarantined" if mode == "quarantine" else "observed"
                quarantined.append(strongest)
            _write(self.root / CANONICAL / f"{canonical_id}.json", strongest)
        for r in superseded + quarantined + admitted:
            did = r.get("discovery_id")
            if did: _write(self.discoveries_dir / f"{did}.json", r)
        metrics = {"canonical_candidates": len(canonical), "superseded_discoveries": len(superseded), "quarantined_discoveries": len(quarantined), "admitted_requests": len(admitted), "requests_suppressed_by_grouping": suppressed, "backfill_limit_reached": limit_reached, "ambiguous_discoveries": len(ambiguous), "queue_limit": max_requests_per_cycle, "backfill_mode": mode, "latest_canonical_work_package": (canonical[-1].get("work_package_id") if canonical else None)}
        payload = {"target_id": target_id, "canonical_candidates": canonical, "superseded_discoveries": superseded, "quarantined_candidates": quarantined, "admitted_requests": admitted, "ambiguous_discoveries": ambiguous, "summary": metrics, "provider_execution_performed": False, "dispatch_execution_performed": False}
        _write(self.root / STATUS / "consolidation_latest.json", payload)
        return payload

    def _ensure_request(self, record: dict[str, Any], canonical_id: str) -> dict[str, Any]:
        self.requests_dir.mkdir(parents=True, exist_ok=True)
        for p in self.requests_dir.glob("*.json"):
            d = _read(p); md = d.get("metadata") or {}
            if md.get("canonical_discovery_id") == canonical_id and d.get("state", "pending") in ACTIVE_STATES:
                return d
        req = PostMergeAuditRequest.create(record["target_id"], record["work_package_id"], record.get("source_kind", "merge"), record.get("source_reference") or record.get("source_commit"), expected_files=[], metadata={"discovery_id": record.get("discovery_id"), "canonical_discovery_id": canonical_id, "promoted_revision": record.get("promoted_revision"), "canonical_status": "admitted", "correlation_method": record.get("correlation_method")})
        d = req.to_dict(); d["state"] = "pending"; _write(self.requests_dir / f"{req.audit_id}.json", d); return d

    def admit(self, target_id: str, work_package_id: str, *, max_requests_per_cycle: int = 5) -> dict[str, Any]:
        records = [r for r in self.load_records() if r.get("target_id") == target_id and r.get("work_package_id") == work_package_id]
        return self.consolidate(target_id, records=records, mode="admit", max_candidates=len(records) or 1, max_requests_per_cycle=max_requests_per_cycle, minimum_evidence_level="commit-message-only")

    def quarantine_status(self, target_id: str = "estate-main") -> dict[str, Any]:
        records = [r for r in self.load_records() if r.get("target_id") == target_id]
        return {"target_id": target_id, "quarantined_candidates": [r for r in records if r.get("state") == "quarantined"], "superseded_discoveries": [r for r in records if r.get("state") == "superseded"], "summary": {"quarantined_candidates": sum(1 for r in records if r.get("state") == "quarantined"), "superseded_discoveries": sum(1 for r in records if r.get("state") == "superseded")}, "provider_execution_performed": False, "dispatch_execution_performed": False}

    def reconcile_requests(self, target_id: str = "estate-main") -> dict[str, Any]:
        reqs = [_read(p) | {"request_path": str(p)} for p in sorted(self.requests_dir.glob("*.json"))] if self.requests_dir.exists() else []
        groups: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
        for r in reqs:
            if r.get("target_id") != target_id: continue
            md = r.get("metadata") or {}; rev = md.get("promoted_revision") or md.get("source_commit") or r.get("source_reference") or "unknown"
            groups.setdefault((r.get("target_id"), r.get("work_package_id"), rev), []).append(r)
        retained=[]; changed=[]
        for _k, group in groups.items():
            keep = sorted(group, key=lambda r: (EVIDENCE_RANK.get(((r.get("metadata") or {}).get("correlation_method") or r.get("source_kind") or ""), 0), r.get("created_at", "")), reverse=True)[0]
            retained.append(keep)
            for r in group:
                if r.get("audit_id") == keep.get("audit_id"): continue
                r["state"] = "superseded" if r.get("state", "pending") in ACTIVE_STATES else r.get("state", "superseded")
                r.setdefault("history", []).append({"at": utc_now_iso(), "action": "reconciled_as_superseded", "retained_request_id": keep.get("audit_id")})
                _write(Path(r["request_path"]), {k:v for k,v in r.items() if k != "request_path"}); changed.append(r)
        return {"target_id": target_id, "retained_requests": retained, "reconciled_requests": changed, "summary": {"reconciled_existing_requests": len(changed), "retained_requests": len(retained)}, "provider_execution_performed": False, "dispatch_execution_performed": False}
