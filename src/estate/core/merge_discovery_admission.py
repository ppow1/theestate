"""Governed automatic admission for canonical merge-discovery candidates."""
from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from estate.core.merge_discovery_consolidation import CANONICAL, REQUESTS, STATUS, _read, _write
from estate.core.post_merge_audit import PostMergeAuditRequest

HOLDS = Path("runtime/merge_discovery/holds")
FINAL_VERDICTS = {"accepted", "accepted_with_notes", "ring2_required", "needs_repair", "blocked", "not_merged", "workspace_failed", "validation_failed"}
BLOCKED_STATES = {"superseded", "blocked", "retired", "already_audited", "ambiguous"}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_time(value: str | None) -> datetime | None:
    if not value: return None
    try: return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError: return None


class MergeDiscoveryAdmission:
    def __init__(self, root: Path | None = None) -> None:
        self.root = Path(root) if root is not None else Path.cwd()

    @property
    def canonical_dir(self) -> Path: return self.root / CANONICAL
    @property
    def requests_dir(self) -> Path: return self.root / REQUESTS
    @property
    def holds_dir(self) -> Path: return self.root / HOLDS

    def load_candidates(self, target: str = "estate-main") -> list[dict[str, Any]]:
        if not self.canonical_dir.exists(): return []
        return [d for d in (_read(p) for p in sorted(self.canonical_dir.glob("*.json"))) if d.get("target_id") == target]

    def classify(self, candidate: dict[str, Any], *, target: str = "estate-main", recency_hours: int = 48) -> str:
        wp = candidate.get("work_package_id")
        if self._hold_path(target, wp).exists(): return "manual_hold"
        if candidate.get("state") in BLOCKED_STATES: return candidate.get("state") if candidate.get("state") == "superseded" else "ambiguous"
        if self._has_final_verdict(target, wp): return "already_audited"
        created = _parse_time(candidate.get("created_at"))
        if created and datetime.now(timezone.utc) - created > timedelta(hours=recency_hours): return "historical_backfill"
        return "current"

    def eligibility(self, candidate: dict[str, Any], *, target: str = "estate-main", recency_hours: int = 48) -> dict[str, Any]:
        classification = self.classify(candidate, target=target, recency_hours=recency_hours)
        md = candidate.get("metadata") or {}
        receipt = md.get("receipt") or {}
        reasons: list[str] = []
        if not candidate.get("work_package_id"): reasons.append("ambiguous_or_missing_work_package_id")
        if not candidate.get("target_id"): reasons.append("canonical_target_missing")
        if classification != "current": reasons.append(classification)
        if candidate.get("state") == "superseded": reasons.append("superseded")
        if not candidate.get("completion_receipt_path") and not receipt: reasons.append("completion_receipt_missing")
        if candidate.get("provider_execution_performed") is True: reasons.append("provider_execution_performed")
        if candidate.get("dispatch_execution_performed") is True: reasons.append("dispatch_execution_performed")
        return {"classification": classification, "eligible": not reasons, "blocking_reasons": reasons}

    def auto_admit(self, target: str = "estate-main", *, max_requests: int = 5, recency_hours: int = 48) -> dict[str, Any]:
        candidates = self.load_candidates(target)
        admitted=[]; held=[]; historical=[]; evaluated=0; limit=False
        for c in candidates:
            evaluated += 1
            e = self.eligibility(c, target=target, recency_hours=recency_hours)
            c["admission"] = e
            if e["classification"] == "historical_backfill": historical.append(c)
            if not e["eligible"]:
                held.append(c); self._persist_candidate(c); continue
            if len(admitted) >= max_requests:
                limit = True; held.append(c); c["admission"]["blocking_reasons"].append("queue_limit_reached"); self._persist_candidate(c); continue
            req = self._ensure_request(c)
            c.update({"state": "admitted", "audit_request_id": req.get("audit_id"), "admitted_at": utc_now_iso()})
            self._persist_candidate(c); admitted.append(c)
        summary = {"auto_admission_enabled": True, "candidates_evaluated": evaluated, "candidates_auto_admitted": len(admitted), "candidates_held": len(held), "historical_candidates_quarantined": len(historical), "current_candidates": sum(1 for c in candidates if (c.get("admission") or {}).get("classification") == "current"), "historical_candidates": len(historical), "admitted_candidates": len(admitted), "held_candidates": len(held), "active_audit_limit": max_requests, "latest_admitted_work_package": admitted[-1].get("work_package_id") if admitted else None, "queue_limit_reached": limit}
        payload={"target_id": target, "admitted_candidates": admitted, "held_candidates": held, "historical_candidates": historical, "summary": summary, "provider_execution_performed": False, "dispatch_execution_performed": False}
        _write(self.root / STATUS / "admission_latest.json", payload)
        return payload

    def status(self, target: str = "estate-main") -> dict[str, Any]:
        p = self.root / STATUS / "admission_latest.json"
        if p.exists(): return _read(p)
        return self.auto_admit(target, max_requests=0)

    def hold(self, target: str, work_package: str) -> dict[str, Any]:
        payload={"target_id": target, "work_package_id": work_package, "hold": True, "created_at": utc_now_iso()}
        _write(self._hold_path(target, work_package), payload); return payload

    def release(self, target: str, work_package: str) -> dict[str, Any]:
        p=self._hold_path(target, work_package); existed=p.exists()
        if existed: p.unlink()
        return {"target_id": target, "work_package_id": work_package, "released": existed, "provider_execution_performed": False, "dispatch_execution_performed": False}

    def _hold_path(self, target: str, wp: str | None) -> Path: return self.root / HOLDS / f"{target}-{wp}.json"
    def _persist_candidate(self, c: dict[str, Any]) -> None:
        cid = c.get("canonical_discovery_id") or f"mc-{c.get('target_id')}-{c.get('work_package_id')}"
        _write(self.root / CANONICAL / f"{cid}.json", c)
    def _ensure_request(self, c: dict[str, Any]) -> dict[str, Any]:
        self.requests_dir.mkdir(parents=True, exist_ok=True); cid=c.get("canonical_discovery_id")
        for p in self.requests_dir.glob("*.json"):
            d=_read(p); md=d.get("metadata") or {}
            if md.get("canonical_discovery_id") == cid and d.get("state", "pending") not in {"superseded", "failed"}: return d
        req=PostMergeAuditRequest.create(c["target_id"], c["work_package_id"], c.get("source_kind", "merge"), c.get("source_reference") or c.get("source_commit") or "HEAD", expected_files=[], metadata={"canonical_discovery_id": cid, "canonical_status": "admitted", "completion_receipt_path": c.get("completion_receipt_path"), "admitted_at": utc_now_iso()})
        d=req.to_dict(); d["state"]="pending"; _write(self.requests_dir / f"{req.audit_id}.json", d); return d
    def _has_final_verdict(self, target: str, wp: str | None) -> bool:
        vd=self.root/"runtime/post_merge_audit/verdicts"
        return any((_read(p).get("target_id")==target and _read(p).get("work_package_id")==wp and _read(p).get("verdict") in FINAL_VERDICTS) for p in vd.glob("*.json")) if vd.exists() else False
