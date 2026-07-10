"""Governed automatic admission for canonical merge-discovery candidates."""
from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from estate.core.merge_discovery_consolidation import CANONICAL, REQUESTS, STATUS, _read, _write
from estate.core.post_merge_audit import PostMergeAuditRequest
from estate.core.post_merge_audit_lifecycle import (
    ACTIVE_REQUEST_STATES, FINAL_VERDICTS, INELIGIBLE_CANDIDATE_STATES,
    RUNNING_REQUEST_STATES, TERMINAL_REQUEST_STATES, duplicate_key,
    is_active_request, is_retryable_request, is_terminal_request, request_state,
)

HOLDS = Path("runtime/merge_discovery/holds")
BLOCKED_STATES = {"superseded", "blocked", "retired", "already_audited", "ambiguous", "quarantined"}


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
        state = candidate.get("state")
        if state in INELIGIBLE_CANDIDATE_STATES: return state
        if state in {"completed", "ring2_required", "blocked", "validation_failed", "workspace_failed", "already_audited"}: return state
        if self._has_final_verdict(target, wp, candidate): return "already_audited"
        req = self._matching_request(candidate)
        if req:
            if is_terminal_request(req): return "already_audited" if self._has_final_verdict(target, wp, candidate) else request_state(req)
            if is_retryable_request(req): return "retryable_failed"
            if request_state(req) == "pending": return "pending"
            if is_active_request(req): return "running"
        created = _parse_time(candidate.get("created_at"))
        if created and datetime.now(timezone.utc) - created > timedelta(hours=recency_hours): return "historical_backfill"
        return "eligible"

    def eligibility(self, candidate: dict[str, Any], *, target: str = "estate-main", recency_hours: int = 48) -> dict[str, Any]:
        classification = self.classify(candidate, target=target, recency_hours=recency_hours)
        md = candidate.get("metadata") or {}
        receipt = md.get("receipt") or {}
        reasons: list[str] = []
        if not candidate.get("work_package_id"): reasons.append("ambiguous_or_missing_work_package_id")
        if not candidate.get("target_id"): reasons.append("canonical_target_missing")
        if classification not in {"eligible", "pending", "running"}: reasons.append(classification)
        if classification in {"pending", "running"}: reasons.append("existing_active_request")
        if candidate.get("state") in INELIGIBLE_CANDIDATE_STATES: reasons.append(candidate.get("state"))
        if not candidate.get("completion_receipt_path") and not receipt: reasons.append("completion_receipt_missing")
        if candidate.get("provider_execution_performed") is True: reasons.append("provider_execution_performed")
        if candidate.get("dispatch_execution_performed") is True: reasons.append("dispatch_execution_performed")
        return {"classification": classification, "eligible": not reasons, "blocking_reasons": reasons}

    def auto_admit(self, target: str = "estate-main", *, max_requests: int = 5, recency_hours: int = 48) -> dict[str, Any]:
        candidates = self.load_candidates(target)
        requests = self._load_requests()
        active_count = sum(1 for r in requests if is_active_request(r))
        pending_count = sum(1 for r in requests if request_state(r) == "pending")
        running_count = sum(1 for r in requests if request_state(r) in RUNNING_REQUEST_STATES)
        terminal_count = sum(1 for r in requests if is_terminal_request(r))
        capacity = max(0, max_requests - active_count)
        admitted=[]; held=[]; historical=[]; evaluated=0; limit=False
        existing_pending=existing_active=already=retryable=0
        for c in candidates:
            evaluated += 1
            e = self.eligibility(c, target=target, recency_hours=recency_hours)
            c["admission"] = e
            cls=e["classification"]
            if cls == "historical_backfill": historical.append(c)
            if cls == "pending": existing_pending += 1; c["state"]="pending"
            if cls == "running": existing_active += 1; c["state"]="running"
            if cls == "already_audited": already += 1; c["state"]="already_audited"
            if cls == "retryable_failed": retryable += 1; c["state"]="retryable_failed"
            if not e["eligible"]:
                held.append(c); self._persist_candidate(c); continue
            if len(admitted) >= capacity:
                limit = True; held.append(c); c["admission"]["blocking_reasons"].append("queue_limit_reached"); self._persist_candidate(c); continue
            req = self._create_request(c)
            c.update({"state": "admitted", "audit_request_id": req.get("audit_id"), "admitted_at": utc_now_iso()})
            self._persist_candidate(c); admitted.append(c)
        after_active = active_count + len(admitted)
        summary = {"auto_admission_enabled": True, "candidates_evaluated": evaluated, "candidates_auto_admitted": len(admitted), "candidates_held": len(held), "historical_candidates_quarantined": len(historical), "current_candidates": sum(1 for c in candidates if (c.get("admission") or {}).get("classification") in {"eligible","pending","running"}), "historical_candidates": len(historical), "admitted_candidates": len(admitted), "admitted_requests": len(admitted), "held_candidates": len(held), "active_audit_limit": max_requests, "latest_admitted_work_package": admitted[-1].get("work_package_id") if admitted else None, "queue_limit_reached": limit, "active_request_count": active_count, "pending_request_count": pending_count, "running_request_count": running_count, "terminal_request_count": terminal_count, "new_requests_created": len(admitted), "existing_pending_requests": existing_pending, "existing_active_requests": existing_active, "already_audited_candidates": already, "retryable_failed_requests": retryable, "available_capacity_before": capacity, "available_capacity_after": max(0, max_requests - after_active)}
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
    def _load_requests(self) -> list[dict[str, Any]]:
        if not self.requests_dir.exists(): return []
        out=[]
        for p in self.requests_dir.glob("*.json"):
            d=_read(p); d.setdefault("state", d.get("status", "pending")); d["request_path"]=str(p); out.append(d)
        return out

    def _matching_request(self, c: dict[str, Any]) -> dict[str, Any] | None:
        key = duplicate_key(c)
        cid=c.get("canonical_discovery_id")
        for d in self._load_requests():
            md=d.get("metadata") or {}
            if md.get("canonical_discovery_id") == cid: return d
            if duplicate_key(d) == key: return d
        return None

    def _create_request(self, c: dict[str, Any]) -> dict[str, Any]:
        existing = self._matching_request(c)
        if existing: return existing
        self.requests_dir.mkdir(parents=True, exist_ok=True); cid=c.get("canonical_discovery_id")
        req=PostMergeAuditRequest.create(c["target_id"], c["work_package_id"], c.get("source_kind", "merge"), c.get("source_reference") or c.get("source_commit") or "HEAD", expected_files=[], metadata={"canonical_discovery_id": cid, "canonical_status": "admitted", "completion_receipt_path": c.get("completion_receipt_path"), "admitted_at": utc_now_iso()})
        d=req.to_dict(); d["state"]="pending"; _write(self.requests_dir / f"{req.audit_id}.json", d); return d

    def _has_final_verdict(self, target: str, wp: str | None, candidate: dict[str, Any] | None = None) -> bool:
        vd=self.root/"runtime/post_merge_audit/verdicts"
        if not vd.exists(): return False
        cid=(candidate or {}).get("canonical_discovery_id")
        source=(candidate or {}).get("source_commit") or (candidate or {}).get("source_reference")
        for p in vd.glob("*.json"):
            d=_read(p); md=d.get("metadata") or {}
            same_identity = (not md.get("canonical_discovery_id") and not d.get("source_commit")) or (md.get("canonical_discovery_id") and md.get("canonical_discovery_id") == cid) or (d.get("source_commit") and d.get("source_commit") == source) or (not cid and not source)
            if d.get("target_id")==target and d.get("work_package_id")==wp and d.get("verdict") in FINAL_VERDICTS and same_identity:
                return True
        return False
