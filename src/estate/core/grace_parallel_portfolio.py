"""Durable, root-scoped Grace portfolio and CME activation reservations.

The consultation store remains the logical source of truth.  This module adds
only the durable reservation projection needed to let CME select independent
roots safely; it is not a second queue or scheduler.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sqlite3
from typing import Any
from uuid import uuid4

from estate.core.consultation_store import ConsultationStore


RESERVATION_STATES = {"RESERVED", "LAUNCHING", "ACTIVE", "HELD_FOR_CAPACITY", "RELEASED", "FAILED"}
ACTIVE_STATES = {"RESERVED", "LAUNCHING", "ACTIVE"}
TERMINAL_ROOT_STATES = {"closed", "resolved"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=True)


@dataclass(frozen=True)
class ActivationReservation:
    activation_id: str
    root_logical_id: str
    continuation_logical_id: str
    worker_class: str
    provider_key: str
    idempotency_key: str
    state: str
    controller_pid: int | None
    worker_pid: int | None
    reason: str | None
    created_at: str
    updated_at: str


def _ensure_schema(store: ConsultationStore) -> None:
    with store._connect() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS grace_activation_reservations (
                activation_id TEXT PRIMARY KEY,
                root_logical_id TEXT NOT NULL,
                continuation_logical_id TEXT NOT NULL,
                worker_class TEXT NOT NULL,
                provider_key TEXT NOT NULL,
                idempotency_key TEXT NOT NULL UNIQUE,
                state TEXT NOT NULL,
                controller_pid INTEGER,
                worker_pid INTEGER,
                reason TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_grace_activation_state
                ON grace_activation_reservations(state);
            CREATE INDEX IF NOT EXISTS idx_grace_activation_capacity
                ON grace_activation_reservations(worker_class, provider_key, state);
            CREATE INDEX IF NOT EXISTS idx_grace_activation_root
                ON grace_activation_reservations(root_logical_id, continuation_logical_id);
            """
        )


def _row(row: sqlite3.Row) -> ActivationReservation:
    return ActivationReservation(**dict(row))


def list_activations(store: ConsultationStore, *, states: set[str] | None = None) -> list[ActivationReservation]:
    _ensure_schema(store)
    with store._connect() as db:
        if states:
            marks = ",".join("?" for _ in states)
            rows = db.execute(
                f"SELECT * FROM grace_activation_reservations WHERE state IN ({marks}) ORDER BY created_at, activation_id",
                tuple(sorted(states)),
            ).fetchall()
        else:
            rows = db.execute("SELECT * FROM grace_activation_reservations ORDER BY created_at, activation_id").fetchall()
    return [_row(item) for item in rows]


def claim_activation(
    store: ConsultationStore,
    *,
    root_logical_id: str,
    continuation_logical_id: str,
    worker_class: str,
    provider_key: str,
    idempotency_key: str,
    capacity: int | None,
    owner_pid: int | None = None,
    controller_pid: int | None = None,
) -> dict[str, Any]:
    """Atomically reserve one continuation, without claiming a worker PID.

    ``owner_pid`` is retained as a compatibility input but is deliberately
    stored as ``controller_pid``.  A real worker PID is attached only by
    :func:`mark_activation_active` after launch succeeds.
    """
    _ensure_schema(store)
    controller_pid = controller_pid if controller_pid is not None else owner_pid
    now = _now()
    activation_id = f"act-{uuid4().hex}"
    with store._connect() as db:
        db.execute("BEGIN IMMEDIATE")
        existing = db.execute(
            "SELECT * FROM grace_activation_reservations WHERE idempotency_key = ?",
            (idempotency_key,),
        ).fetchone()
        if existing:
            if existing["state"] == "HELD_FOR_CAPACITY" and capacity is not None and int(capacity) >= 1:
                used = db.execute(
                    "SELECT COUNT(*) AS n FROM grace_activation_reservations WHERE worker_class = ? AND provider_key = ? AND state IN ('RESERVED','LAUNCHING','ACTIVE')",
                    (worker_class, provider_key),
                ).fetchone()["n"]
                if used < int(capacity):
                    db.execute("UPDATE grace_activation_reservations SET state='RESERVED', reason=NULL, controller_pid=?, updated_at=? WHERE activation_id=?", (controller_pid, now, existing["activation_id"]))
                    db.commit()
                    return {"status": "RESERVED", "activation_id": existing["activation_id"], "reason": None, "controller_pid": controller_pid, "worker_pid": None}
            return {"status": "ALREADY_RESERVED", "activation": dict(existing), "activation_id": existing["activation_id"]}
        if capacity is None or int(capacity) < 1:
            state, reason = "HELD_FOR_CAPACITY", "unknown_or_invalid_capacity"
        else:
            used = db.execute(
                "SELECT COUNT(*) AS n FROM grace_activation_reservations WHERE worker_class = ? AND provider_key = ? AND state IN ('RESERVED','LAUNCHING','ACTIVE')",
                (worker_class, provider_key),
            ).fetchone()["n"]
            state, reason = (("HELD_FOR_CAPACITY", "provider_capacity_exhausted") if used >= int(capacity) else ("RESERVED", None))
        db.execute(
            "INSERT INTO grace_activation_reservations VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (activation_id, root_logical_id, continuation_logical_id, worker_class, provider_key,
             idempotency_key, state, controller_pid, None, reason, now, now),
        )
        db.execute("COMMIT")
        return {"status": state, "activation_id": activation_id, "reason": reason,
                "controller_pid": controller_pid, "worker_pid": None}


def mark_activation_active(store: ConsultationStore, activation_id: str, *, worker_pid: int) -> dict[str, Any]:
    _ensure_schema(store)
    with store._connect() as db:
        db.execute("BEGIN IMMEDIATE")
        row = db.execute("SELECT * FROM grace_activation_reservations WHERE activation_id = ?", (activation_id,)).fetchone()
        if row is None:
            db.rollback()
            return {"status": "UNKNOWN_ACTIVATION", "activation_id": activation_id}
        if row["state"] == "HELD_FOR_CAPACITY":
            db.rollback()
            return {"status": "CAPACITY_HELD", "activation_id": activation_id}
        db.execute("UPDATE grace_activation_reservations SET state='ACTIVE', worker_pid=?, reason=NULL, updated_at=? WHERE activation_id=?", (int(worker_pid), _now(), activation_id))
        db.commit()
        return {"status": "ACTIVE", "activation_id": activation_id, "worker_pid": int(worker_pid)}


def release_activation(store: ConsultationStore, activation_id: str, *, reason: str = "released") -> dict[str, Any]:
    _ensure_schema(store)
    with store._connect() as db:
        db.execute("UPDATE grace_activation_reservations SET state='RELEASED', reason=?, updated_at=? WHERE activation_id=? AND state NOT IN ('RELEASED','FAILED')", (reason, _now(), activation_id))
    return {"status": "RELEASED", "activation_id": activation_id, "reason": reason}


def recover_stale_activation(store: ConsultationStore, activation_id: str, *, alive_pids: set[int]) -> dict[str, Any]:
    """Recover only this activation; controller and worker ownership are distinct."""
    _ensure_schema(store)
    with store._connect() as db:
        row = db.execute("SELECT * FROM grace_activation_reservations WHERE activation_id=?", (activation_id,)).fetchone()
        if row is None:
            return {"status": "UNKNOWN_ACTIVATION", "activation_id": activation_id}
        pid = row["worker_pid"] if row["state"] == "ACTIVE" else row["controller_pid"]
        if pid and int(pid) in {int(item) for item in alive_pids}:
            return {"status": "LIVE_OWNER", "activation_id": activation_id, "pid": pid}
        if row["state"] not in ACTIVE_STATES:
            return {"status": "NOT_ACTIVE", "activation_id": activation_id, "state": row["state"]}
        db.execute("UPDATE grace_activation_reservations SET state='RELEASED', reason='stale_owner_recovered', updated_at=? WHERE activation_id=?", (_now(), activation_id))
    return {"status": "STALE_OWNER_RECOVERED", "activation_id": activation_id, "released_pid": pid}


def build_portfolio(store: ConsultationStore, *, reasoning_capacity: int | None = None, provider_key: str = "default") -> dict[str, Any]:
    """Return a bounded, deterministic projection with an explanation per item."""
    _ensure_schema(store)
    records = store.search()
    activations = list_activations(store)
    by_continuation = {item.continuation_logical_id: item for item in activations if item.state in ACTIVE_STATES | {"HELD_FOR_CAPACITY"}}
    items: list[dict[str, Any]] = []
    for record in sorted(records, key=lambda item: (item.root_logical_id, item.consultation_turn_number, item.logical_consultation_id)):
        activation = by_continuation.get(record.logical_consultation_id)
        if activation and activation.state in ACTIVE_STATES:
            classification, reason = "ACTIVE", f"activation {activation.activation_id} is {activation.state}"
        elif activation and activation.state == "HELD_FOR_CAPACITY":
            classification, reason = "HELD_CAPACITY", activation.reason or "provider capacity exhausted"
        elif record.status in TERMINAL_ROOT_STATES or record.response is not None and record.status in {"resolved", "closed"}:
            classification, reason = "COMPLETE", f"consultation status {record.status}"
        elif record.status == "steward_decision_required":
            classification, reason = "WAITING_STEWARD", "authoritative Steward decision required"
        elif any(tag.lower() in {"blocked_dependency", "dependency_blocked"} for tag in record.tags):
            classification, reason = "BLOCKED_DEPENDENCY", "durable consultation tag marks an unmet dependency"
        elif record.status in {"awaiting_reasoning", "open"}:
            classification, reason = "READY", f"consultation status {record.status}"
        elif record.status in {"continuation_required", "response_received", "validating"}:
            classification, reason = "VERIFYING", f"consultation status {record.status}"
        elif record.status in {"abandoned"}:
            classification, reason = "FAILED", f"consultation status {record.status}"
        else:
            classification, reason = "UNKNOWN", f"unsupported consultation status {record.status}"
        items.append({"root_id": record.root_logical_id, "continuation_id": record.logical_consultation_id, "classification": classification, "reason": reason, "status": record.status, "activation_id": activation.activation_id if activation else None})
    active = [item for item in activations if item.state in ACTIVE_STATES]
    held = [item for item in activations if item.state == "HELD_FOR_CAPACITY"]
    return {"schema_version": "estate.grace.parallel_portfolio.v1", "items": items,
            "active_activation_count": len(active), "newly_reserved_count": 0,
            "eligible_count": sum(item["classification"] == "READY" for item in items),
            "held_capacity_count": len(held), "blocked_count": sum(item["classification"] == "BLOCKED_DEPENDENCY" for item in items),
            "waiting_external_count": sum(item["classification"] == "WAITING_STEWARD" for item in items),
            "reasoning_capacity": reasoning_capacity, "provider_key": provider_key,
            "authoritative_source": str(store.path)}


def reconcile_ready(store: ConsultationStore, *, reasoning_capacity: int | None, provider_key: str = "default", controller_pid: int | None = None) -> dict[str, Any]:
    portfolio = build_portfolio(store, reasoning_capacity=reasoning_capacity, provider_key=provider_key)
    newly = []
    for item in portfolio["items"]:
        if item["classification"] not in {"READY", "HELD_CAPACITY"}:
            continue
        result = claim_activation(store, root_logical_id=item["root_id"], continuation_logical_id=item["continuation_id"], worker_class="reasoning", provider_key=provider_key, idempotency_key=f"{item['root_id']}:{item['continuation_id']}:reasoning", capacity=reasoning_capacity, controller_pid=controller_pid if controller_pid is not None else os.getpid())
        if result["status"] == "RESERVED":
            newly.append(result)
    result = build_portfolio(store, reasoning_capacity=reasoning_capacity, provider_key=provider_key)
    result["newly_reserved_count"] = len(newly)
    result["newly_reserved"] = newly
    return result
