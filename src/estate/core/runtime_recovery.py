"""Durable recovery model for the Operations Runtime.

This module keeps the runtime's restart-critical state in append-preserving JSON
artifacts.  Recovery is intentionally plan-first: interrupted or corrupt state is
classified and described before any repair action is executed.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from estate.core.paths import ESTATE_ROOT

RECOVERY_BASE = Path("runtime/operations_runtime/persistence")
CHECKPOINTS_DIR = RECOVERY_BASE / "checkpoints"
BACKUPS_DIR = RECOVERY_BASE / "backups"
CORRUPT_DIR = RECOVERY_BASE / "corrupt"
RECOVERY_STATUS = RECOVERY_BASE / "recovery_status.json"
EVENT_LOG = RECOVERY_BASE / "events.jsonl"
MANIFEST = RECOVERY_BASE / "manifest.json"
STATE_KEYS = {
    "cycle_checkpoint",
    "leases",
    "claims",
    "scheduler_state",
    "campaign_state",
    "admitted_audit_state",
    "last_durable_event_position",
}
TERMINAL_CYCLE_STATES = {"completed", "failed", "cancelled", "stopped"}
ACTIVE_CYCLE_STATES = {"running", "starting", "sleeping", "stop_requested", "blocked"}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _root(root: Path | None = None) -> Path:
    return root or (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


def _json_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _atomic_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


@dataclass
class RecoveryClassification:
    artifact: str
    classification: str
    reason: str
    destructive_repair_required: bool = False
    actions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class RuntimePersistenceStore:
    """Persists recoverable Operations Runtime state with checksums and backups."""

    def __init__(self, root: Path | None = None, *, backup_limit: int = 5) -> None:
        self.root = _root(root)
        self.backup_limit = backup_limit

    @property
    def base(self) -> Path:
        return self.root / RECOVERY_BASE

    def ensure_dirs(self) -> None:
        for rel in [CHECKPOINTS_DIR, BACKUPS_DIR, CORRUPT_DIR]:
            (self.root / rel).mkdir(parents=True, exist_ok=True)

    def checkpoint_path(self, cycle_id: str) -> Path:
        return self.root / CHECKPOINTS_DIR / f"{cycle_id}.json"

    def persist_checkpoint(
        self,
        *,
        cycle_id: str,
        cycle_state: str,
        leases: dict[str, Any] | None = None,
        claims: dict[str, Any] | None = None,
        scheduler_state: dict[str, Any] | None = None,
        campaign_state: dict[str, Any] | None = None,
        admitted_audit_state: dict[str, Any] | None = None,
        last_durable_event_position: int = 0,
        completed_side_effects: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.ensure_dirs()
        path = self.checkpoint_path(cycle_id)
        if path.exists():
            self._backup(path)
        state = {
            "cycle_checkpoint": {"cycle_id": cycle_id, "state": cycle_state, "updated_at": utc_now_iso()},
            "leases": leases or {},
            "claims": claims or {},
            "scheduler_state": scheduler_state or {},
            "campaign_state": campaign_state or {},
            "admitted_audit_state": admitted_audit_state or {},
            "last_durable_event_position": last_durable_event_position,
            "completed_side_effects": completed_side_effects or [],
            "metadata": metadata or {},
        }
        envelope = {"schema_version": 1, "persisted_at": utc_now_iso(), "state": state, "checksum": _json_hash(state)}
        _atomic_write_json(path, envelope)
        self._write_manifest(cycle_id, path, envelope)
        self.append_event("checkpoint_persisted", {"cycle_id": cycle_id, "cycle_state": cycle_state, "path": str(path.relative_to(self.root))})
        self.rotate_backups()
        return envelope

    def load_checkpoint(self, cycle_id: str) -> dict[str, Any]:
        return self.load_checkpoint_path(self.checkpoint_path(cycle_id))

    def load_checkpoint_path(self, path: Path) -> dict[str, Any]:
        payload = json.loads(path.read_text(encoding="utf-8"))
        state = payload.get("state")
        if not isinstance(state, dict) or payload.get("checksum") != _json_hash(state):
            raise ValueError(f"checkpoint checksum mismatch: {path}")
        missing = sorted(STATE_KEYS - set(state))
        if missing:
            raise ValueError(f"checkpoint missing required state keys: {', '.join(missing)}")
        return payload

    def latest_checkpoint_path(self) -> Path | None:
        paths = sorted((self.root / CHECKPOINTS_DIR).glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        return paths[0] if paths else None

    def append_event(self, event_type: str, payload: dict[str, Any]) -> int:
        path = self.root / EVENT_LOG
        path.parent.mkdir(parents=True, exist_ok=True)
        position = 0
        if path.exists():
            position = sum(1 for _ in path.open(encoding="utf-8"))
        record = {"position": position, "event_id": f"rte-{uuid4().hex}", "event_type": event_type, "created_at": utc_now_iso(), "payload": payload}
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
        return position

    def isolate_corrupt(self, path: Path, reason: str) -> Path:
        self.ensure_dirs()
        destination = self.root / CORRUPT_DIR / f"{path.stem}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}{path.suffix}"
        shutil.move(str(path), destination)
        self.append_event("corrupt_state_isolated", {"source": str(path.relative_to(self.root)), "destination": str(destination.relative_to(self.root)), "reason": reason})
        return destination

    def rotate_backups(self) -> None:
        backups = sorted((self.root / BACKUPS_DIR).glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        for old in backups[self.backup_limit:]:
            old.unlink()

    def _backup(self, path: Path) -> None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        shutil.copy2(path, self.root / BACKUPS_DIR / f"{path.stem}-{stamp}.json")

    def _write_manifest(self, cycle_id: str, path: Path, envelope: dict[str, Any]) -> None:
        _atomic_write_json(self.root / MANIFEST, {"latest_cycle_id": cycle_id, "latest_checkpoint": str(path.relative_to(self.root)), "checksum": envelope["checksum"], "updated_at": utc_now_iso()})


class RuntimeRecoveryManager:
    """Classifies interrupted runtime work and produces safe recovery plans."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = _root(root)
        self.store = RuntimePersistenceStore(self.root)

    def inspect_startup(self) -> dict[str, Any]:
        checkpoint_path = self.store.latest_checkpoint_path()
        classifications: list[RecoveryClassification] = []
        safe_state = False
        checkpoint: dict[str, Any] | None = None
        if checkpoint_path is None:
            classifications.append(RecoveryClassification("runtime", "resumable", "no checkpoint exists; runtime may start cleanly"))
        else:
            try:
                checkpoint = self.store.load_checkpoint_path(checkpoint_path)
                classifications.extend(self._classify_checkpoint(checkpoint))
            except Exception as exc:
                safe_state = True
                classifications.append(RecoveryClassification(str(checkpoint_path.relative_to(self.root)), "manual-review-required", str(exc), True, ["isolate_corrupt_state", "start_in_safe_state"]))
        plan = self._build_plan(classifications, checkpoint_path, safe_state=safe_state)
        _atomic_write_json(self.root / RECOVERY_STATUS, plan)
        return plan

    def execute_non_destructive_plan(self, plan: dict[str, Any]) -> dict[str, Any]:
        if plan.get("destructive_repair_required"):
            raise ValueError("destructive recovery plan requires explicit operator review")
        self.store.append_event("recovery_plan_executed", {"plan_id": plan["plan_id"], "mode": "non_destructive"})
        result = {**plan, "executed": True, "executed_at": utc_now_iso()}
        _atomic_write_json(self.root / RECOVERY_STATUS, result)
        return result

    def isolate_corrupt_checkpoint(self, checkpoint_path: str, *, reason: str) -> dict[str, Any]:
        isolated = self.store.isolate_corrupt(self.root / checkpoint_path, reason)
        plan = self.inspect_startup()
        return {"isolated": str(isolated.relative_to(self.root)), "safe_state_plan": plan}

    def _classify_checkpoint(self, checkpoint: dict[str, Any]) -> list[RecoveryClassification]:
        state = checkpoint["state"]
        cycle = state["cycle_checkpoint"]
        items: list[RecoveryClassification] = []
        cycle_state = cycle.get("state")
        if cycle_state in ACTIVE_CYCLE_STATES:
            items.append(RecoveryClassification("cycle_checkpoint", "resumable", "cycle interrupted before terminal checkpoint", False, ["resume_from_checkpoint", "replay_after_last_durable_event_position"]))
        elif cycle_state in TERMINAL_CYCLE_STATES:
            items.append(RecoveryClassification("cycle_checkpoint", "resumable", "cycle has terminal checkpoint; reconstruct status only", False, ["reconstruct_state_from_events"]))
        else:
            items.append(RecoveryClassification("cycle_checkpoint", "manual-review-required", f"unknown cycle state {cycle_state}", False, ["hold_runtime_start"]))
        for lease_id, lease in (state.get("leases") or {}).items():
            status = lease.get("status", "active") if isinstance(lease, dict) else "active"
            if status == "active":
                items.append(RecoveryClassification(f"lease:{lease_id}", "retryable", "active lease found at startup", False, ["mark_stale_or_reclaim_deterministically"]))
        for claim_id, claim in (state.get("claims") or {}).items():
            status = claim.get("status", "claimed") if isinstance(claim, dict) else "claimed"
            if status in {"claimed", "running"}:
                items.append(RecoveryClassification(f"claim:{claim_id}", "retryable", "unfinished claim found at startup", False, ["release_or_requeue_claim_deterministically"]))
        return items

    def _build_plan(self, classifications: list[RecoveryClassification], checkpoint_path: Path | None, *, safe_state: bool) -> dict[str, Any]:
        destructive = any(c.destructive_repair_required for c in classifications)
        posture = "safe-state" if safe_state else ("operator-review" if destructive else "recoverable")
        pending = [action for c in classifications for action in c.actions]
        return {
            "plan_id": f"rrp-{uuid4().hex}",
            "generated_at": utc_now_iso(),
            "checkpoint": str(checkpoint_path.relative_to(self.root)) if checkpoint_path else None,
            "recovery_posture": posture,
            "destructive_repair_required": destructive,
            "classifications": [c.to_dict() for c in classifications],
            "pending_actions": pending,
            "safe_state_fallback": safe_state,
            "execute_destructive_repairs": False,
        }


def load_recovery_status(root: Path | None = None) -> dict[str, Any]:
    path = _root(root) / RECOVERY_STATUS
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return RuntimeRecoveryManager(root).inspect_startup()
