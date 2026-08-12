"""Durable Estate reasoning-consultation lineage.

This store owns logical consultation identity and memory only.  Comms8 owns
the live request lifecycle; PTM and GitHub are referenced projections, not
duplicated authorities.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import hashlib
from pathlib import Path
import sqlite3
from typing import Any
from uuid import uuid4


SCHEMA_VERSION = 1
DEFAULT_PATH = Path(r"A:\theestate-data\consultations\consultations.db")
MAX_TURN = 99
CONSULTATION_STATUSES = {
    "open", "awaiting_reasoning", "claimed", "reasoning", "response_received",
    "validating", "continuation_required", "steward_decision_required", "closed", "resolved", "abandoned",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _json(value: Any) -> str | None:
    return None if value is None else json.dumps(value, ensure_ascii=True, sort_keys=True)


def _from_json(value: str | None) -> Any:
    return None if value is None else json.loads(value)


@dataclass(frozen=True)
class ConsultationRecord:
    logical_consultation_id: str
    consultation_root_id: int
    consultation_turn_number: int
    root_logical_id: str
    predecessor_logical_id: str | None
    parent_logical_id: str | None
    ec8_request_id: str | None
    workflow_id: str | None
    actor: str | None
    worker: str | None
    status: str
    subject: str | None
    objective: str | None
    question: str | None
    current_evidence: Any
    prior_context_summary: str | None
    recommendation: str | None
    response: Any
    response_id: str | None
    expected_result: str | None
    observed_result: str | None
    validation_evidence: Any
    new_constraint: str | None
    continuation_reason: str | None
    ptm_project_id: str | None
    ptm_work_item_id: str | None
    github_projection_status: str
    github_reference: str | None
    tags: tuple[str, ...]
    created_at: str
    updated_at: str
    closed_at: str | None
    compact_summary: str | None
    summary_updated_at: str | None


@dataclass(frozen=True)
class TransportAttempt:
    logical_consultation_id: str
    attempt_number: int
    request_id: str | None
    workflow_id: str | None
    status: str
    failure_class: str | None
    supersedes_request_id: str | None
    worker_id: str | None
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class ExecutionRequestLink:
    execution_request_id: str
    logical_consultation_id: str
    dispatch_id: str
    provider_id: str | None
    provider_type: str | None
    required_capability: str | None
    status: str
    current_attempt_id: str | None
    result_json: Any
    result_reference: str | None
    validation_status: str | None
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class ExecutionAttemptLink:
    execution_request_id: str
    attempt_number: int
    execution_attempt_id: str
    provider_id: str
    status: str
    result_reference: str | None
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class EscalationRecord:
    escalation_id: str
    consultation_root_id: int
    root_logical_id: str
    current_logical_id: str
    ec8_request_id: str | None
    ptm_project_id: str | None
    reason: str
    state: str
    snapshot: Any
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class StewardDecisionRecord:
    decision_id: str
    escalation_id: str
    selected_option: str | None
    decision_text: str
    decision_action: str | None
    decision_actor: str
    rationale: str | None
    created_at: str


@dataclass(frozen=True)
class EscalationOutcomeRecord:
    outcome_id: str
    decision_id: str
    execution_references: Any
    observed_result: str
    validation_result: str | None
    new_evidence: Any
    classification: str
    consultation_status: str
    outcome_at: str


class ConsultationStore:
    """SQLite-backed consultation memory with atomic Estate-owned numbering."""

    def __init__(self, path: str | Path = DEFAULT_PATH) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA busy_timeout=10000")
        return connection

    def _initialize(self) -> None:
        with self._connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS consultation_store_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                INSERT OR IGNORE INTO consultation_store_meta(key, value)
                    VALUES ('schema_version', '1');
                CREATE TABLE IF NOT EXISTS consultation_sequences (
                    name TEXT PRIMARY KEY,
                    next_value INTEGER NOT NULL
                );
                INSERT OR IGNORE INTO consultation_sequences(name, next_value)
                    VALUES ('root', 1);
                CREATE TABLE IF NOT EXISTS consultations (
                    logical_consultation_id TEXT PRIMARY KEY,
                    consultation_root_id INTEGER NOT NULL,
                    consultation_turn_number INTEGER NOT NULL CHECK (consultation_turn_number BETWEEN 0 AND 99),
                    root_logical_id TEXT NOT NULL,
                    predecessor_logical_id TEXT UNIQUE,
                    parent_logical_id TEXT UNIQUE REFERENCES consultations(logical_consultation_id),
                    ec8_request_id TEXT UNIQUE,
                    workflow_id TEXT,
                    actor TEXT,
                    worker TEXT,
                    status TEXT NOT NULL,
                    subject TEXT,
                    objective TEXT,
                    question TEXT,
                    current_evidence_json TEXT,
                    prior_context_summary TEXT,
                    recommendation TEXT,
                    response_json TEXT,
                    response_id TEXT,
                    expected_result TEXT,
                    observed_result TEXT,
                    validation_evidence_json TEXT,
                    new_constraint TEXT,
                    continuation_reason TEXT,
                    ptm_project_id TEXT,
                    ptm_work_item_id TEXT,
                    github_projection_status TEXT NOT NULL DEFAULT 'pending',
                    github_reference TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    closed_at TEXT,
                    UNIQUE (consultation_root_id, consultation_turn_number)
                );
                CREATE TABLE IF NOT EXISTS consultation_tags (
                    logical_consultation_id TEXT NOT NULL REFERENCES consultations(logical_consultation_id) ON DELETE CASCADE,
                    tag TEXT NOT NULL,
                    PRIMARY KEY (logical_consultation_id, tag)
                );
                CREATE INDEX IF NOT EXISTS idx_consultations_status ON consultations(status);
                CREATE INDEX IF NOT EXISTS idx_consultations_workflow ON consultations(workflow_id);
                CREATE INDEX IF NOT EXISTS idx_consultations_ptm_project ON consultations(ptm_project_id);
                CREATE INDEX IF NOT EXISTS idx_consultations_ec8 ON consultations(ec8_request_id);
                CREATE INDEX IF NOT EXISTS idx_consultation_tags_tag ON consultation_tags(tag);
                CREATE TABLE IF NOT EXISTS consultation_transport_attempts (
                    logical_consultation_id TEXT NOT NULL REFERENCES consultations(logical_consultation_id) ON DELETE CASCADE,
                    attempt_number INTEGER NOT NULL CHECK (attempt_number >= 1),
                    request_id TEXT UNIQUE,
                    workflow_id TEXT,
                    status TEXT NOT NULL,
                    failure_class TEXT,
                    supersedes_request_id TEXT,
                    worker_id TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (logical_consultation_id, attempt_number)
                );
                CREATE INDEX IF NOT EXISTS idx_transport_attempt_request ON consultation_transport_attempts(request_id);
                CREATE TABLE IF NOT EXISTS consultation_execution_requests (
                    execution_request_id TEXT PRIMARY KEY,
                    logical_consultation_id TEXT NOT NULL REFERENCES consultations(logical_consultation_id) ON DELETE CASCADE,
                    dispatch_id TEXT NOT NULL,
                    provider_id TEXT,
                    provider_type TEXT,
                    required_capability TEXT,
                    status TEXT NOT NULL,
                    current_attempt_id TEXT,
                    result_json TEXT,
                    result_reference TEXT,
                    validation_status TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_consultation_execution_logical ON consultation_execution_requests(logical_consultation_id);
                CREATE TABLE IF NOT EXISTS consultation_execution_attempts (
                    execution_request_id TEXT NOT NULL REFERENCES consultation_execution_requests(execution_request_id) ON DELETE CASCADE,
                    attempt_number INTEGER NOT NULL CHECK (attempt_number >= 1),
                    execution_attempt_id TEXT PRIMARY KEY,
                    provider_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    result_reference TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE (execution_request_id, attempt_number)
                );
                CREATE INDEX IF NOT EXISTS idx_consultation_execution_attempt_request ON consultation_execution_attempts(execution_request_id);
                CREATE TABLE IF NOT EXISTS consultation_evidence_reservations (
                    root_consultation_id INTEGER NOT NULL,
                    request_key TEXT NOT NULL,
                    slot INTEGER NOT NULL CHECK (slot BETWEEN 1 AND 3),
                    logical_consultation_id TEXT NOT NULL REFERENCES consultations(logical_consultation_id) ON DELETE CASCADE,
                    status TEXT NOT NULL DEFAULT 'reserved',
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (root_consultation_id, request_key),
                    UNIQUE (root_consultation_id, slot)
                );
                CREATE TABLE IF NOT EXISTS consultation_escalations (
                    escalation_id TEXT PRIMARY KEY,
                    consultation_root_id INTEGER NOT NULL,
                    root_logical_id TEXT NOT NULL,
                    current_logical_id TEXT NOT NULL REFERENCES consultations(logical_consultation_id),
                    ec8_request_id TEXT,
                    ptm_project_id TEXT,
                    reason TEXT NOT NULL,
                    state TEXT NOT NULL,
                    snapshot_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE (current_logical_id, reason)
                );
                CREATE INDEX IF NOT EXISTS idx_escalations_root ON consultation_escalations(consultation_root_id);
                CREATE INDEX IF NOT EXISTS idx_escalations_ptm ON consultation_escalations(ptm_project_id);
                CREATE TABLE IF NOT EXISTS escalation_decisions (
                    decision_id TEXT PRIMARY KEY,
                    escalation_id TEXT NOT NULL REFERENCES consultation_escalations(escalation_id),
                    selected_option TEXT,
                    decision_text TEXT NOT NULL,
                    decision_action TEXT,
                    decision_actor TEXT NOT NULL,
                    rationale TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS escalation_steward_evidence (
                    evidence_id TEXT PRIMARY KEY,
                    escalation_id TEXT NOT NULL REFERENCES consultation_escalations(escalation_id),
                    decision_id TEXT REFERENCES escalation_decisions(decision_id),
                    kind TEXT NOT NULL,
                    content_json TEXT NOT NULL,
                    provenance TEXT NOT NULL,
                    impact TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS escalation_outcomes (
                    outcome_id TEXT PRIMARY KEY,
                    decision_id TEXT NOT NULL REFERENCES escalation_decisions(decision_id),
                    execution_references_json TEXT,
                    observed_result TEXT NOT NULL,
                    validation_result TEXT,
                    new_evidence_json TEXT,
                    classification TEXT NOT NULL,
                    consultation_status TEXT NOT NULL,
                    outcome_at TEXT NOT NULL
                );
                """
            )
            columns = {row[1] for row in db.execute("PRAGMA table_info(consultations)")}
            if "compact_summary" not in columns:
                db.execute("ALTER TABLE consultations ADD COLUMN compact_summary TEXT")
            if "summary_updated_at" not in columns:
                db.execute("ALTER TABLE consultations ADD COLUMN summary_updated_at TEXT")

    @staticmethod
    def _logical(root: int, turn: int) -> str:
        return f"{root}.{turn:02d}"

    def _insert(self, db: sqlite3.Connection, *, root: int, turn: int, predecessor: str | None,
                parent: str | None, status: str, subject: str | None, objective: str | None,
                question: str | None, current_evidence: Any, prior_context_summary: str | None,
                continuation_reason: str | None, actor: str | None, worker: str | None,
                ptm_project_id: str | None, ptm_work_item_id: str | None, workflow_id: str | None,
                tags: tuple[str, ...]) -> ConsultationRecord:
        logical = self._logical(root, turn)
        now = _now()
        db.execute(
            """INSERT INTO consultations
            (logical_consultation_id, consultation_root_id, consultation_turn_number,
             root_logical_id, predecessor_logical_id, parent_logical_id, status,
             subject, objective, question, current_evidence_json, prior_context_summary,
             workflow_id,
             continuation_reason, actor, worker, ptm_project_id, ptm_work_item_id,
             created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (logical, root, turn, self._logical(root, 0), predecessor, parent, status,
             subject, objective, question, _json(current_evidence), prior_context_summary,
             workflow_id, continuation_reason, actor, worker, ptm_project_id, ptm_work_item_id, now, now),
        )
        for tag in sorted({tag.strip() for tag in tags if tag and tag.strip()}):
            db.execute("INSERT INTO consultation_tags(logical_consultation_id, tag) VALUES (?, ?)", (logical, tag))
        return self.get(logical, db=db)

    def allocate_root(self, **fields: Any) -> ConsultationRecord:
        """Allocate ``N.00``; rollover requires an explicit ``continues_from``."""
        predecessor = fields.pop("continues_from", None)
        defaults = dict(status="open", subject=None, objective=None, question=None,
                        current_evidence=None, prior_context_summary=None,
                        continuation_reason=None, actor=None, worker=None,
                        ptm_project_id=None, ptm_work_item_id=None, workflow_id=None, tags=())
        defaults.update(fields)
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            if predecessor is not None:
                prior = db.execute("SELECT consultation_turn_number FROM consultations WHERE logical_consultation_id = ?", (predecessor,)).fetchone()
                if prior is None or prior[0] != MAX_TURN:
                    raise ValueError("rollover requires an existing .99 predecessor")
            root = db.execute("SELECT next_value FROM consultation_sequences WHERE name = 'root'").fetchone()[0]
            db.execute("UPDATE consultation_sequences SET next_value = ? WHERE name = 'root'", (root + 1,))
            return self._insert(db, root=root, turn=0, predecessor=predecessor, parent=None, **defaults)

    def allocate_continuation(self, parent_logical_id: str, **fields: Any) -> ConsultationRecord:
        """Allocate the next ordered turn, refusing silent ``.100`` rollover."""
        defaults = dict(status="continuation_required", subject=None, objective=None, question=None,
                        current_evidence=None, prior_context_summary=None,
                        continuation_reason=None, actor=None, worker=None,
                        ptm_project_id=None, ptm_work_item_id=None, workflow_id=None, tags=())
        defaults.update(fields)
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            parent = db.execute("SELECT consultation_root_id, consultation_turn_number FROM consultations WHERE logical_consultation_id = ?", (parent_logical_id,)).fetchone()
            if parent is None:
                raise KeyError(parent_logical_id)
            if parent[1] >= MAX_TURN:
                raise ValueError("rollover_required_after_.99")
            return self._insert(db, root=parent[0], turn=parent[1] + 1, predecessor=None, parent=parent_logical_id, **defaults)

    def get(self, logical_consultation_id: str, *, db: sqlite3.Connection | None = None) -> ConsultationRecord:
        own = db is None
        connection = db or self._connect()
        try:
            row = connection.execute("SELECT * FROM consultations WHERE logical_consultation_id = ?", (logical_consultation_id,)).fetchone()
            if row is None:
                raise KeyError(logical_consultation_id)
            tags = tuple(item[0] for item in connection.execute("SELECT tag FROM consultation_tags WHERE logical_consultation_id = ? ORDER BY tag", (logical_consultation_id,)))
            return ConsultationRecord(**{key: _from_json(row[key]) if key in {"current_evidence_json", "response_json", "validation_evidence_json"} else row[key] for key in row.keys() if key not in {"current_evidence_json", "response_json", "validation_evidence_json"}}, current_evidence=_from_json(row["current_evidence_json"]), response=_from_json(row["response_json"]), validation_evidence=_from_json(row["validation_evidence_json"]), tags=tags)
        finally:
            if own:
                connection.close()

    def attach_ec8(self, logical_consultation_id: str, request_id: str, workflow_id: str | None = None) -> ConsultationRecord:
        with self._connect() as db:
            db.execute("UPDATE consultations SET ec8_request_id = ?, workflow_id = COALESCE(?, workflow_id), updated_at = ? WHERE logical_consultation_id = ?", (request_id, workflow_id, _now(), logical_consultation_id))
            return self.get(logical_consultation_id, db=db)

    def record_transport_attempt(self, logical_consultation_id: str, request_id: str, *,
                                 workflow_id: str | None = None, status: str = "queued",
                                 failure_class: str | None = None,
                                 supersedes_request_id: str | None = None,
                                 worker_id: str | None = None) -> TransportAttempt:
        """Durably record one transport attempt without changing Comms8 state."""
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM consultation_transport_attempts WHERE request_id = ?", (request_id,)).fetchone()
            if row:
                return TransportAttempt(**dict(row))
            last = db.execute("SELECT COALESCE(MAX(attempt_number), 0) FROM consultation_transport_attempts WHERE logical_consultation_id = ?", (logical_consultation_id,)).fetchone()[0]
            now = _now()
            db.execute("INSERT INTO consultation_transport_attempts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (logical_consultation_id, last + 1, request_id, workflow_id, status, failure_class, supersedes_request_id, worker_id, now, now))
            row = db.execute("SELECT * FROM consultation_transport_attempts WHERE logical_consultation_id = ? AND attempt_number = ?", (logical_consultation_id, last + 1)).fetchone()
            return TransportAttempt(**dict(row))

    def transport_attempts(self, logical_consultation_id: str) -> list[TransportAttempt]:
        with self._connect() as db:
            rows = db.execute("SELECT * FROM consultation_transport_attempts WHERE logical_consultation_id = ? ORDER BY attempt_number", (logical_consultation_id,)).fetchall()
            return [TransportAttempt(**dict(row)) for row in rows]

    def mark_transport_attempt(self, logical_consultation_id: str, attempt_number: int, *,
                               status: str, request_id: str | None = None,
                               failure_class: str | None = None,
                               worker_id: str | None = None) -> TransportAttempt:
        with self._connect() as db:
            db.execute("UPDATE consultation_transport_attempts SET status = ?, request_id = COALESCE(?, request_id), failure_class = COALESCE(?, failure_class), worker_id = COALESCE(?, worker_id), updated_at = ? WHERE logical_consultation_id = ? AND attempt_number = ?", (status, request_id, failure_class, worker_id, _now(), logical_consultation_id, attempt_number))
            row = db.execute("SELECT * FROM consultation_transport_attempts WHERE logical_consultation_id = ? AND attempt_number = ?", (logical_consultation_id, attempt_number)).fetchone()
            if row is None:
                raise KeyError((logical_consultation_id, attempt_number))
            return TransportAttempt(**dict(row))

    def attach_execution_request(self, logical_consultation_id: str, execution_request_id: str, *,
                                 dispatch_id: str, provider_id: str | None = None,
                                 provider_type: str | None = None,
                                 required_capability: str | None = None,
                                 status: str = "queued") -> ExecutionRequestLink:
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            existing = db.execute("SELECT * FROM consultation_execution_requests WHERE execution_request_id = ?", (execution_request_id,)).fetchone()
            if existing:
                if existing["logical_consultation_id"] != logical_consultation_id:
                    raise ValueError("execution_request_id_already_linked")
                return self._execution_request_from_row(existing)
            now = _now()
            db.execute("INSERT INTO consultation_execution_requests VALUES (?, ?, ?, ?, ?, ?, ?, NULL, NULL, NULL, NULL, ?, ?)", (execution_request_id, logical_consultation_id, dispatch_id, provider_id, provider_type, required_capability, status, now, now))
            return self._execution_request_from_row(db.execute("SELECT * FROM consultation_execution_requests WHERE execution_request_id = ?", (execution_request_id,)).fetchone())

    @staticmethod
    def _execution_request_from_row(row: sqlite3.Row) -> ExecutionRequestLink:
        values = dict(row)
        values["result_json"] = _from_json(values["result_json"])
        return ExecutionRequestLink(**values)

    def execution_request(self, execution_request_id: str) -> ExecutionRequestLink:
        with self._connect() as db:
            row = db.execute("SELECT * FROM consultation_execution_requests WHERE execution_request_id = ?", (execution_request_id,)).fetchone()
            if row is None:
                raise KeyError(execution_request_id)
            return self._execution_request_from_row(row)

    def execution_requests(self, logical_consultation_id: str) -> list[ExecutionRequestLink]:
        with self._connect() as db:
            rows = db.execute("SELECT * FROM consultation_execution_requests WHERE logical_consultation_id = ? ORDER BY created_at", (logical_consultation_id,)).fetchall()
            return [self._execution_request_from_row(row) for row in rows]

    def update_execution_request(self, execution_request_id: str, *, status: str | None = None,
                                 provider_id: str | None = None, provider_type: str | None = None,
                                 current_attempt_id: str | None = None, result: Any = None,
                                 result_reference: str | None = None,
                                 validation_status: str | None = None) -> ExecutionRequestLink:
        with self._connect() as db:
            current = db.execute("SELECT * FROM consultation_execution_requests WHERE execution_request_id = ?", (execution_request_id,)).fetchone()
            if current is None:
                raise KeyError(execution_request_id)
            db.execute("UPDATE consultation_execution_requests SET status = COALESCE(?, status), provider_id = COALESCE(?, provider_id), provider_type = COALESCE(?, provider_type), current_attempt_id = COALESCE(?, current_attempt_id), result_json = COALESCE(?, result_json), result_reference = COALESCE(?, result_reference), validation_status = COALESCE(?, validation_status), updated_at = ? WHERE execution_request_id = ?", (status, provider_id, provider_type, current_attempt_id, _json(result), result_reference, validation_status, _now(), execution_request_id))
            return self._execution_request_from_row(db.execute("SELECT * FROM consultation_execution_requests WHERE execution_request_id = ?", (execution_request_id,)).fetchone())

    def record_execution_attempt(self, execution_request_id: str, execution_attempt_id: str, *,
                                 provider_id: str, status: str, result_reference: str | None = None) -> ExecutionAttemptLink:
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            existing = db.execute("SELECT * FROM consultation_execution_attempts WHERE execution_attempt_id = ?", (execution_attempt_id,)).fetchone()
            if existing:
                db.execute("UPDATE consultation_execution_attempts SET status = ?, result_reference = COALESCE(?, result_reference), updated_at = ? WHERE execution_attempt_id = ?", (status, result_reference, _now(), execution_attempt_id))
                return ExecutionAttemptLink(**dict(db.execute("SELECT * FROM consultation_execution_attempts WHERE execution_attempt_id = ?", (execution_attempt_id,)).fetchone()))
            number = db.execute("SELECT COALESCE(MAX(attempt_number), 0) + 1 FROM consultation_execution_attempts WHERE execution_request_id = ?", (execution_request_id,)).fetchone()[0]
            now = _now()
            db.execute("INSERT INTO consultation_execution_attempts VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (execution_request_id, number, execution_attempt_id, provider_id, status, result_reference, now, now))
            row = db.execute("SELECT * FROM consultation_execution_attempts WHERE execution_attempt_id = ?", (execution_attempt_id,)).fetchone()
            return ExecutionAttemptLink(**dict(row))

    def execution_attempts(self, execution_request_id: str) -> list[ExecutionAttemptLink]:
        with self._connect() as db:
            rows = db.execute("SELECT * FROM consultation_execution_attempts WHERE execution_request_id = ? ORDER BY attempt_number", (execution_request_id,)).fetchall()
            return [ExecutionAttemptLink(**dict(row)) for row in rows]

    def reserve_transport_retry(self, logical_consultation_id: str, failed_request_id: str, *,
                                failure_class: str) -> TransportAttempt:
        """Atomically reserve exactly one replacement attempt for a failed turn."""
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            consultation = db.execute("SELECT response_json FROM consultations WHERE logical_consultation_id = ?", (logical_consultation_id,)).fetchone()
            if consultation is None:
                raise KeyError(logical_consultation_id)
            if consultation[0] is not None:
                raise ValueError("transport_retry_response_already_exists")
            latest = db.execute("SELECT * FROM consultation_transport_attempts WHERE logical_consultation_id = ? ORDER BY attempt_number DESC LIMIT 1", (logical_consultation_id,)).fetchone()
            if latest and latest["status"] in {"creating", "queued", "claimed", "acknowledged", "responded"}:
                return TransportAttempt(**dict(latest))
            number = (latest["attempt_number"] if latest else 0) + 1
            now = _now()
            db.execute("INSERT INTO consultation_transport_attempts VALUES (?, ?, NULL, NULL, 'creating', ?, ?, NULL, ?, ?)", (logical_consultation_id, number, failure_class, failed_request_id, now, now))
            row = db.execute("SELECT * FROM consultation_transport_attempts WHERE logical_consultation_id = ? AND attempt_number = ?", (logical_consultation_id, number)).fetchone()
            return TransportAttempt(**dict(row))

    def append_response(self, logical_consultation_id: str, response: Any, *, response_id: str | None = None, recommendation: str | None = None) -> ConsultationRecord:
        with self._connect() as db:
            db.execute("UPDATE consultations SET response_json = ?, response_id = ?, recommendation = COALESCE(?, recommendation), status = 'response_received', updated_at = ? WHERE logical_consultation_id = ?", (_json(response), response_id, recommendation, _now(), logical_consultation_id))
            record = self.get(logical_consultation_id, db=db)
            updated = self.update_compact_summary(logical_consultation_id, db=db)
            if record.logical_consultation_id != record.root_logical_id:
                self.update_compact_summary(record.root_logical_id, db=db)
            return updated

    def append_validation(self, logical_consultation_id: str, *, expected_result: str | None = None, observed_result: str | None = None, evidence: Any = None, status: str = "validating") -> ConsultationRecord:
        with self._connect() as db:
            db.execute("UPDATE consultations SET expected_result = ?, observed_result = ?, validation_evidence_json = ?, status = ?, updated_at = ? WHERE logical_consultation_id = ?", (expected_result, observed_result, _json(evidence), status, _now(), logical_consultation_id))
            record = self.get(logical_consultation_id, db=db)
            updated = self.update_compact_summary(logical_consultation_id, db=db)
            if record.logical_consultation_id != record.root_logical_id:
                self.update_compact_summary(record.root_logical_id, db=db)
            return updated

    def set_status(self, logical_consultation_id: str, status: str) -> ConsultationRecord:
        """Record a consultation workflow state without changing Comms8 state."""
        if status not in CONSULTATION_STATUSES:
            raise ValueError("invalid_consultation_status")
        with self._connect() as db:
            db.execute("UPDATE consultations SET status = ?, updated_at = ? WHERE logical_consultation_id = ?", (status, _now(), logical_consultation_id))
            return self.get(logical_consultation_id, db=db)

    def set_escalation_package(self, logical_consultation_id: str, package: Any) -> ConsultationRecord:
        """Persist a bounded Steward handoff without resolving the consultation."""
        if not isinstance(package, dict):
            raise ValueError("invalid_escalation_package")
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            current = db.execute(
                "SELECT consultation_root_id, root_logical_id FROM consultations WHERE logical_consultation_id = ?",
                (logical_consultation_id,),
            ).fetchone()
            if current is None:
                raise KeyError(logical_consultation_id)
            now = _now()
            encoded = _json(package)
            db.execute(
                "UPDATE consultations SET observed_result = 'STEWARD_DECISION_REQUIRED', validation_evidence_json = ?, status = 'steward_decision_required', updated_at = ? WHERE logical_consultation_id = ?",
                (encoded, now, logical_consultation_id),
            )
            # The root is the operator-visible authority for the consultation;
            # never mark it resolved merely because autonomous processing ended.
            db.execute(
                "UPDATE consultations SET observed_result = 'STEWARD_DECISION_REQUIRED', validation_evidence_json = ?, status = 'steward_decision_required', updated_at = ? WHERE logical_consultation_id = ? AND status <> 'closed'",
                (encoded, now, current[1]),
            )
            return self.get(logical_consultation_id, db=db)

    @staticmethod
    def _escalation_from_row(row: sqlite3.Row) -> EscalationRecord:
        values = dict(row)
        values["snapshot"] = _from_json(values.pop("snapshot_json"))
        return EscalationRecord(**values)

    def create_escalation_record(self, logical_consultation_id: str, snapshot: Any, *, reason: str = "bounded_autonomous_evidence_exhausted") -> EscalationRecord:
        current = self.get(logical_consultation_id)
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            existing = db.execute("SELECT * FROM consultation_escalations WHERE current_logical_id = ? AND reason = ?", (logical_consultation_id, reason)).fetchone()
            if existing:
                return self._escalation_from_row(existing)
            escalation_id = f"esc-{uuid4().hex[:16]}"
            now = _now()
            db.execute("INSERT INTO consultation_escalations VALUES (?, ?, ?, ?, ?, ?, ?, 'steward_decision_required', ?, ?, ?)", (escalation_id, current.consultation_root_id, current.root_logical_id, current.logical_consultation_id, current.ec8_request_id, current.ptm_project_id, reason, _json(snapshot), now, now))
            return self._escalation_from_row(db.execute("SELECT * FROM consultation_escalations WHERE escalation_id = ?", (escalation_id,)).fetchone())

    def escalation(self, escalation_id: str) -> EscalationRecord:
        with self._connect() as db:
            row = db.execute("SELECT * FROM consultation_escalations WHERE escalation_id = ?", (escalation_id,)).fetchone()
            if row is None:
                raise KeyError(escalation_id)
            return self._escalation_from_row(row)

    def set_escalation_state(self, escalation_id: str, state: str) -> EscalationRecord:
        if state not in {"steward_decision_required", "decision_recorded", "outcome_recorded", "closed"}:
            raise ValueError("invalid_escalation_state")
        with self._connect() as db:
            db.execute("UPDATE consultation_escalations SET state = ?, updated_at = ? WHERE escalation_id = ?", (state, _now(), escalation_id))
            return self.escalation(escalation_id)

    def escalations(self, *, ptm_project_id: str | None = None, tag: str | None = None, reason: str | None = None, confidence_band: str | None = None) -> list[EscalationRecord]:
        clauses, values = [], []
        if ptm_project_id is not None:
            clauses.append("ptm_project_id = ?"); values.append(ptm_project_id)
        if reason is not None:
            clauses.append("reason = ?"); values.append(reason)
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        with self._connect() as db:
            rows = db.execute(f"SELECT * FROM consultation_escalations{where} ORDER BY created_at", values).fetchall()
        result = [self._escalation_from_row(row) for row in rows]
        if tag is not None:
            result = [item for item in result if any(tag in record.tags for record in [self.get(item.current_logical_id)])]
        if confidence_band is None:
            return result
        def in_band(item: EscalationRecord) -> bool:
            score = item.snapshot.get("overall_confidence") if isinstance(item.snapshot, dict) else None
            return isinstance(score, (int, float)) and ((confidence_band == "low" and score < .60) or (confidence_band == "medium" and .60 <= score < .80) or (confidence_band == "high" and score >= .80))
        return [item for item in result if in_band(item)]

    def steward_decisions(self, escalation_id: str) -> list[StewardDecisionRecord]:
        with self._connect() as db:
            rows = db.execute("SELECT * FROM escalation_decisions WHERE escalation_id = ? ORDER BY created_at", (escalation_id,)).fetchall()
            return [StewardDecisionRecord(**dict(row)) for row in rows]

    def escalation_outcomes(self, decision_id: str) -> list[EscalationOutcomeRecord]:
        with self._connect() as db:
            rows = db.execute("SELECT * FROM escalation_outcomes WHERE decision_id = ? ORDER BY outcome_at", (decision_id,)).fetchall()
            return [EscalationOutcomeRecord(**{**dict(row), "execution_references": _from_json(row["execution_references_json"]), "new_evidence": _from_json(row["new_evidence_json"]),}) for row in rows]

    def record_steward_decision(self, escalation_id: str, *, selected_option: str | None, decision_text: str, decision_action: str | None = None, rationale: str | None = None, decision_actor: str = "Steward", steward_evidence: list[dict[str, Any]] | None = None) -> StewardDecisionRecord:
        if not decision_text.strip() or decision_actor != "Steward":
            raise ValueError("invalid_steward_decision")
        decision_id = f"dec-{uuid4().hex[:16]}"
        now = _now()
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("INSERT INTO escalation_decisions VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (decision_id, escalation_id, selected_option, decision_text, decision_action, decision_actor, rationale, now))
            for item in steward_evidence or []:
                if not item.get("content") or not item.get("provenance"):
                    raise ValueError("invalid_steward_evidence")
                db.execute("INSERT INTO escalation_steward_evidence VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (f"evidence-{uuid4().hex[:16]}", escalation_id, decision_id, "STEWARD_SUPPLIED_EVIDENCE", _json(item["content"]), str(item["provenance"]), item.get("impact"), now))
            db.execute("UPDATE consultation_escalations SET state = 'decision_recorded', updated_at = ? WHERE escalation_id = ?", (now, escalation_id))
            return StewardDecisionRecord(decision_id, escalation_id, selected_option, decision_text, decision_action, decision_actor, rationale, now)

    def record_escalation_outcome(self, decision_id: str, *, observed_result: str, validation_result: str | None, classification: str, consultation_status: str, execution_references: Any = None, new_evidence: Any = None) -> EscalationOutcomeRecord:
        allowed = {"SUCCESS", "FAILED", "PARTIAL", "NEW_CONSTRAINT_DISCOVERED", "ABANDONED", "UNKNOWN"}
        if classification not in allowed or not observed_result:
            raise ValueError("invalid_escalation_outcome")
        outcome_id = f"out-{uuid4().hex[:16]}"
        now = _now()
        with self._connect() as db:
            db.execute("INSERT INTO escalation_outcomes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (outcome_id, decision_id, _json(execution_references), observed_result, validation_result, _json(new_evidence), classification, consultation_status, now))
        return EscalationOutcomeRecord(outcome_id, decision_id, execution_references, observed_result, validation_result, new_evidence, classification, consultation_status, now)

    def reserve_evidence_acquisition(self, logical_consultation_id: str, request_identity: str, *, max_acquisitions: int = 3) -> dict[str, Any]:
        """Atomically reserve one bounded root-level evidence acquisition."""
        current = self.get(logical_consultation_id)
        root = current.consultation_root_id
        key = hashlib.sha256(str(request_identity).encode("utf-8")).hexdigest()
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            existing = db.execute("SELECT root_consultation_id, request_key, slot, logical_consultation_id, status FROM consultation_evidence_reservations WHERE root_consultation_id = ? AND request_key = ?", (root, key)).fetchone()
            if existing:
                return dict(existing)
            provider_count = db.execute(
                "SELECT COUNT(*) FROM consultation_execution_requests e JOIN consultations c ON c.logical_consultation_id = e.logical_consultation_id WHERE c.consultation_root_id = ? AND e.required_capability IN ('repository_read','filesystem_read','test_inspection','configuration_inspection','software_engineering_readonly')",
                (root,),
            ).fetchone()[0]
            reserved_count = db.execute("SELECT COUNT(*) FROM consultation_evidence_reservations WHERE root_consultation_id = ?", (root,)).fetchone()[0]
            if max(provider_count, reserved_count) >= max_acquisitions:
                raise ValueError("EVIDENCE_ACQUISITION_LIMIT_REACHED")
            slot = max(provider_count, reserved_count) + 1
            now = _now()
            db.execute("INSERT INTO consultation_evidence_reservations(root_consultation_id, request_key, slot, logical_consultation_id, status, created_at) VALUES (?, ?, ?, ?, 'reserved', ?)", (root, key, slot, logical_consultation_id, now))
            return {"root_consultation_id": root, "request_key": key, "slot": slot, "logical_consultation_id": logical_consultation_id, "status": "reserved"}

    def set_github_projection(self, logical_consultation_id: str, status: str, reference: str | None = None) -> ConsultationRecord:
        if status not in {"pending", "published", "failed"}:
            raise ValueError("invalid_github_projection_status")
        with self._connect() as db:
            db.execute("UPDATE consultations SET github_projection_status = ?, github_reference = ?, updated_at = ? WHERE logical_consultation_id = ?", (status, reference, _now(), logical_consultation_id))
            return self.get(logical_consultation_id, db=db)

    @staticmethod
    def _root_number(root_id: int | str) -> int:
        text = str(root_id).split(".", 1)[0]
        if not text.isdigit():
            raise ValueError("invalid_consultation_root")
        return int(text)

    def get_root(self, root_id: int | str) -> ConsultationRecord:
        root = self._root_number(root_id)
        rows = self.search(logical_id=f"{root}.00")
        if not rows:
            raise KeyError(f"{root}.00")
        return rows[0]

    def get_turn_range(self, root_id: int | str, start: int = 0, end: int = MAX_TURN) -> list[ConsultationRecord]:
        root = self._root_number(root_id)
        if not 0 <= start <= end <= MAX_TURN:
            raise ValueError("invalid_turn_range")
        with self._connect() as db:
            rows = db.execute("SELECT logical_consultation_id FROM consultations WHERE consultation_root_id = ? AND consultation_turn_number BETWEEN ? AND ? ORDER BY consultation_turn_number", (root, start, end)).fetchall()
            return [self.get(row[0], db=db) for row in rows]

    def latest_turns(self, root_id: int | str, limit: int = 5) -> list[ConsultationRecord]:
        if not 1 <= limit <= 20:
            raise ValueError("invalid_history_limit")
        turns = self.get_turn_range(root_id)
        return turns[-limit:]

    def update_compact_summary(self, logical_consultation_id: str, *, db: sqlite3.Connection | None = None, summary: str | None = None) -> ConsultationRecord:
        own = db is None
        connection = db or self._connect()
        try:
            record = self.get(logical_consultation_id, db=connection)
            if summary is None:
                root_row = connection.execute("SELECT logical_consultation_id FROM consultations WHERE logical_consultation_id = ?", (record.root_logical_id,)).fetchone()
                root = self.get(root_row[0], db=connection)
                latest_row = connection.execute("SELECT logical_consultation_id FROM consultations WHERE consultation_root_id = ? ORDER BY consultation_turn_number DESC LIMIT 1", (record.consultation_root_id,)).fetchone()
                latest = self.get(latest_row[0], db=connection)
                response = latest.response
                response_text = response.get("content", "") if isinstance(response, dict) else (str(response) if response else "")
                evidence = json.dumps(latest.current_evidence, ensure_ascii=True, sort_keys=True) if latest.current_evidence else ""
                summary = "\n".join(filter(None, [
                    f"Objective: {root.objective or ''}",
                    f"Current question: {latest.question or ''}",
                    f"Latest recommendation: {response_text[:1200]}",
                    f"Observed result: {latest.observed_result or ''}",
                    f"New constraint: {latest.new_constraint or ''}",
                    f"Evidence: {evidence[:1200]}",
                    f"Status: {latest.status}",
                ]))[:4000]
            connection.execute("UPDATE consultations SET compact_summary = ?, summary_updated_at = ?, updated_at = ? WHERE logical_consultation_id = ?", (summary, _now(), _now(), logical_consultation_id))
            return self.get(logical_consultation_id, db=connection)
        finally:
            if own:
                connection.close()

    def compact_summary(self, root_id: int | str) -> dict[str, Any]:
        root = self.get_root(root_id)
        return {"root_consultation_id": root.root_logical_id, "summary": root.compact_summary or self.update_compact_summary(root.logical_consultation_id).compact_summary or "", "status": root.status, "latest_turn": self.latest_turns(root_id, 1)[0].logical_consultation_id if self.latest_turns(root_id, 1) else None}

    def context_required(self, root_id: int | str, *, reason: str, start: int | None = None, end: int | None = None, latest: int | None = None) -> dict[str, Any]:
        if latest is not None:
            turns = self.latest_turns(root_id, latest)
            requested = f"latest:{latest}"
        else:
            turns = self.get_turn_range(root_id, start or 0, end if end is not None else MAX_TURN)
            requested = f"{self._root_number(root_id)}.{start or 0:02d}-{self._root_number(root_id)}.{(end if end is not None else MAX_TURN):02d}"
        return {"status": "CONTEXT_REQUIRED", "root_consultation_id": self._root_number(root_id), "requested": requested, "reason": reason, "turns": [{"logical_consultation_id": item.logical_consultation_id, "question": item.question, "evidence": item.current_evidence, "response": item.response, "validation_evidence": item.validation_evidence} for item in turns]}

    def add_tags(self, logical_consultation_id: str, tags: list[str] | tuple[str, ...]) -> ConsultationRecord:
        with self._connect() as db:
            for tag in sorted({tag.strip() for tag in tags if tag and tag.strip()}):
                db.execute("INSERT OR IGNORE INTO consultation_tags(logical_consultation_id, tag) VALUES (?, ?)", (logical_consultation_id, tag))
            db.execute("UPDATE consultations SET updated_at = ? WHERE logical_consultation_id = ?", (_now(), logical_consultation_id))
            return self.get(logical_consultation_id, db=db)

    def search(self, *, logical_id: str | None = None, ptm_project_id: str | None = None, tag: str | None = None, workflow_id: str | None = None, status: str | None = None, ec8_request_id: str | None = None) -> list[ConsultationRecord]:
        clauses, values = [], []
        for field, value in (("logical_consultation_id", logical_id), ("ptm_project_id", ptm_project_id), ("workflow_id", workflow_id), ("status", status), ("ec8_request_id", ec8_request_id)):
            if value is not None:
                clauses.append(f"c.{field} = ?")
                values.append(value)
        join = " JOIN consultation_tags t ON t.logical_consultation_id = c.logical_consultation_id" if tag is not None else ""
        if tag is not None:
            clauses.append("t.tag = ?")
            values.append(tag)
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        with self._connect() as db:
            rows = db.execute(f"SELECT c.logical_consultation_id FROM consultations c{join}{where} ORDER BY c.consultation_root_id, c.consultation_turn_number", values).fetchall()
            return [self.get(row[0], db=db) for row in rows]
