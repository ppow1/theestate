"""Staged resident session manager for WP-4025.

This module is intentionally uninstalled.  It defines the durable session and
conversation-recovery behavior that WP-4031 can integrate into the resident
runtime after conflict review.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import json
import os
import re
from typing import Any, Iterable
from uuid import uuid4

ACTIVE_STATUSES = {"active", "interrupted"}
TERMINAL_STATUSES = {"archived", "forgotten"}
VALID_STATUSES = ACTIVE_STATUSES | TERMINAL_STATUSES
SESSION_ID_RE = re.compile(r"^[A-Z0-9][A-Z0-9_.-]{2,80}$")


@dataclass(frozen=True)
class ResidentSessionIdentity:
    resident_id: str
    resident_name: str | None = None
    office_surface: str = "resident_private"


@dataclass(frozen=True)
class ConversationCheckpoint:
    checkpoint_id: str
    sequence: int
    created_at: str
    message_count: int
    digest: str
    active_cycle_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class ResidentSessionStore:
    """Durable JSON-file session registry with restart-safe writes.

    The staged store keeps session metadata, checkpoints, and compatibility
    mappings in one registry file.  It intentionally stores references to
    external conversation records instead of creating a second conversation
    transcript store.
    """

    def __init__(self, root: str | Path, *, now: str | None = None) -> None:
        self.root = Path(root)
        self.registry_path = self.root / "resident_sessions.json"
        self.tmp_path = self.root / "resident_sessions.json.tmp"
        self.recovery_path = self.root / "resident_sessions.recovered.json"
        self.now = now
        self.root.mkdir(parents=True, exist_ok=True)
        self._recover_interrupted_write()
        if not self.registry_path.exists():
            self._write_registry(self._empty_registry())

    def create_session(
        self,
        identity: ResidentSessionIdentity,
        *,
        name: str,
        active_cycle_id: str | None = None,
        open_webui_conversation_id: str | None = None,
        existing_chat_record_refs: Iterable[str] = (),
    ) -> dict[str, Any]:
        self._validate_identity(identity)
        registry = self._read_registry()
        session_id = self._new_session_id(registry)
        created_at = self._timestamp()
        session = {
            "session_id": session_id,
            "resident_id": identity.resident_id,
            "resident_name": identity.resident_name,
            "name": self._clean_name(name),
            "status": "active",
            "office_surface": identity.office_surface,
            "active_cycle_id": active_cycle_id,
            "created_at": created_at,
            "updated_at": created_at,
            "archived_at": None,
            "forgotten_at": None,
            "conversation_record_refs": sorted(set(existing_chat_record_refs)),
            "checkpoints": [],
            "audit_log": [self._audit("created", created_at, {"active_cycle_id": active_cycle_id})],
            "open_webui": {"conversation_id": open_webui_conversation_id},
        }
        registry["sessions"][session_id] = session
        self._index_mapping(registry, session)
        self._write_registry(registry)
        return dict(session)

    def rename_session(self, resident_id: str, session_id: str, name: str) -> dict[str, Any]:
        return self._mutate_session(resident_id, session_id, "renamed", lambda s: s.update({"name": self._clean_name(name)}))

    def link_active_cycle(self, resident_id: str, session_id: str, active_cycle_id: str) -> dict[str, Any]:
        return self._mutate_session(resident_id, session_id, "active_cycle_linked", lambda s: s.update({"active_cycle_id": active_cycle_id}))

    def checkpoint(
        self,
        resident_id: str,
        session_id: str,
        *,
        message_count: int,
        digest: str,
        conversation_record_ref: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ConversationCheckpoint:
        registry = self._read_registry()
        session = self._require_session(registry, resident_id, session_id, allow_terminal=False)
        sequence = len(session["checkpoints"]) + 1
        checkpoint = ConversationCheckpoint(
            checkpoint_id=f"{session_id}-CP-{sequence:04d}",
            sequence=sequence,
            created_at=self._timestamp(),
            message_count=message_count,
            digest=digest,
            active_cycle_id=session.get("active_cycle_id"),
            metadata=metadata or {},
        )
        session["checkpoints"].append(checkpoint.__dict__)
        if conversation_record_ref:
            session["conversation_record_refs"] = sorted(set(session["conversation_record_refs"] + [conversation_record_ref]))
        self._touch(session, "checkpoint_created", {"checkpoint_id": checkpoint.checkpoint_id})
        self._write_registry(registry)
        return checkpoint

    def resume_session(self, resident_id: str, session_id: str) -> dict[str, Any]:
        registry = self._read_registry()
        session = self._require_session(registry, resident_id, session_id, allow_terminal=False)
        latest = session["checkpoints"][-1] if session["checkpoints"] else None
        self._touch(session, "resumed", {"checkpoint_id": latest and latest["checkpoint_id"]})
        self._write_registry(registry)
        return {"session": dict(session), "resume_from_checkpoint": latest, "conversation_record_refs": list(session["conversation_record_refs"])}

    def archive_session(self, resident_id: str, session_id: str, *, reason: str) -> dict[str, Any]:
        def archive(s: dict[str, Any]) -> None:
            s["status"] = "archived"
            s["archived_at"] = self._timestamp()
            s["archive_reason"] = reason
        return self._mutate_session(resident_id, session_id, "archived", archive, allow_terminal=False)

    def forget_session(self, resident_id: str, session_id: str, *, reason: str) -> dict[str, Any]:
        def forget(s: dict[str, Any]) -> None:
            s["status"] = "forgotten"
            s["forgotten_at"] = self._timestamp()
            s["forget_reason"] = reason
            s["name"] = "Forgotten session"
            s["conversation_record_refs"] = []
            s["checkpoints"] = []
            s["open_webui"] = {"conversation_id": None}
        return self._mutate_session(resident_id, session_id, "forgotten", forget, allow_terminal=True)

    def recover(self) -> dict[str, Any]:
        """Recover from restart and mark sessions with dangling writes interrupted."""
        self._recover_interrupted_write()
        registry = self._read_registry()
        recovered = []
        for session in registry["sessions"].values():
            if session["status"] == "active" and session.get("write_in_progress"):
                session["status"] = "interrupted"
                self._touch(session, "interrupted_write_recovered", {})
                session.pop("write_in_progress", None)
                recovered.append(session["session_id"])
        if recovered:
            self._write_registry(registry)
        return {"recovered_session_ids": sorted(recovered), "registry_path": str(self.registry_path)}

    def list_sessions(self, resident_id: str, *, include_archived: bool = False, include_forgotten: bool = False) -> list[dict[str, Any]]:
        registry = self._read_registry()
        rows = []
        for session in registry["sessions"].values():
            if session["resident_id"] != resident_id:
                continue
            if session["status"] == "archived" and not include_archived:
                continue
            if session["status"] == "forgotten" and not include_forgotten:
                continue
            rows.append(self._status_row(session))
        return sorted(rows, key=lambda row: (row["status"] not in ACTIVE_STATUSES, row["session_id"]))

    def map_open_webui(self, resident_id: str, conversation_id: str) -> dict[str, Any] | None:
        registry = self._read_registry()
        session_id = registry["open_webui_map"].get(conversation_id)
        if not session_id:
            return None
        session = self._require_session(registry, resident_id, session_id, allow_terminal=True)
        if session["status"] in TERMINAL_STATUSES:
            return None
        return self._status_row(session)

    def _mutate_session(self, resident_id: str, session_id: str, action: str, mutator, *, allow_terminal: bool = False) -> dict[str, Any]:
        registry = self._read_registry()
        session = self._require_session(registry, resident_id, session_id, allow_terminal=allow_terminal)
        mutator(session)
        self._touch(session, action, {})
        self._index_mapping(registry, session)
        self._write_registry(registry)
        return dict(session)

    def _require_session(self, registry: dict[str, Any], resident_id: str, session_id: str, *, allow_terminal: bool) -> dict[str, Any]:
        if not SESSION_ID_RE.match(session_id):
            raise ValueError("invalid session id")
        session = registry["sessions"].get(session_id)
        if not session:
            raise KeyError(session_id)
        if session["resident_id"] != resident_id:
            raise PermissionError("resident identity mismatch during session recovery")
        if session["status"] in TERMINAL_STATUSES and not allow_terminal:
            raise ValueError(f"session is {session['status']} and cannot be resumed as active memory")
        return session

    def _status_row(self, session: dict[str, Any]) -> dict[str, Any]:
        return {
            "session_id": session["session_id"],
            "resident_id": session["resident_id"],
            "name": session["name"],
            "status": session["status"],
            "active_cycle_id": session.get("active_cycle_id"),
            "updated_at": session["updated_at"],
            "checkpoint_count": len(session.get("checkpoints", [])),
            "open_webui_conversation_id": session.get("open_webui", {}).get("conversation_id"),
            "private_to_resident": session.get("office_surface") == "resident_private",
        }

    def _index_mapping(self, registry: dict[str, Any], session: dict[str, Any]) -> None:
        conversation_id = session.get("open_webui", {}).get("conversation_id")
        if conversation_id and session["status"] not in TERMINAL_STATUSES:
            registry["open_webui_map"][conversation_id] = session["session_id"]

    def _touch(self, session: dict[str, Any], action: str, details: dict[str, Any]) -> None:
        ts = self._timestamp()
        session["updated_at"] = ts
        session.setdefault("audit_log", []).append(self._audit(action, ts, details))

    def _audit(self, action: str, at: str, details: dict[str, Any]) -> dict[str, Any]:
        return {"at": at, "action": action, "details": details}

    def _recover_interrupted_write(self) -> None:
        if self.tmp_path.exists() and not self.registry_path.exists():
            os.replace(self.tmp_path, self.registry_path)
        elif self.tmp_path.exists():
            os.replace(self.tmp_path, self.recovery_path)

    def _read_registry(self) -> dict[str, Any]:
        with self.registry_path.open(encoding="utf-8") as handle:
            return json.load(handle)

    def _write_registry(self, registry: dict[str, Any]) -> None:
        registry["schema_version"] = "estate.resident_sessions.v1.staged"
        with self.tmp_path.open("w", encoding="utf-8") as handle:
            json.dump(registry, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(self.tmp_path, self.registry_path)

    def _empty_registry(self) -> dict[str, Any]:
        return {"schema_version": "estate.resident_sessions.v1.staged", "sessions": {}, "open_webui_map": {}}

    def _new_session_id(self, registry: dict[str, Any]) -> str:
        while True:
            candidate = f"RS-{uuid4().hex[:12].upper()}"
            if candidate not in registry["sessions"]:
                return candidate

    def _timestamp(self) -> str:
        return self.now or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    def _validate_identity(self, identity: ResidentSessionIdentity) -> None:
        if not identity.resident_id.startswith("RES-"):
            raise ValueError("resident_id must be a canonical RES-* identity")
        if identity.office_surface != "resident_private":
            raise PermissionError("staged sessions may not be exposed through public Office surfaces")

    def _clean_name(self, name: str) -> str:
        cleaned = " ".join(name.split())
        if not cleaned:
            raise ValueError("session name is required")
        return cleaned[:120]
