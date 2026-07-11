"""Staged resident attachment exchange contracts for WP-4029.

This module is intentionally uninstalled.  It provides deterministic intake,
metadata, linkage, summary, read/download/export/archive, retention, redaction,
deduplication, and audit behavior that WP-4031 can adapt into the existing
resident attachment, mailbox, session, classification, audit, Office, and Open
WebUI surfaces.  It never executes uploaded files and summaries are separate
working artifacts, not source content.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import PurePosixPath
from typing import Any, Callable, Iterable
import mimetypes
import re

DEFAULT_MAX_BYTES = 5 * 1024 * 1024
SAFE_EXTENSIONS = {
    ".txt": "text/plain",
    ".md": "text/markdown",
    ".csv": "text/csv",
    ".json": "application/json",
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}
DANGEROUS_EXTENSIONS = {".exe", ".sh", ".bat", ".cmd", ".ps1", ".js", ".vbs", ".scr", ".msi", ".dll", ".py"}
RETENTION_STATES = {"active", "retained", "archived", "redacted", "deleted"}
SENSITIVE_CLASSIFICATIONS = {"restricted", "confidential"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slug(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip()).strip(".-_").lower()
    return cleaned or "unnamed"


@dataclass(frozen=True)
class AttachmentPolicy:
    max_bytes: int = DEFAULT_MAX_BYTES
    allowed_extensions: dict[str, str] = field(default_factory=lambda: dict(SAFE_EXTENSIONS))
    dangerous_extensions: set[str] = field(default_factory=lambda: set(DANGEROUS_EXTENSIONS))
    root: str = "resident_attachments"


@dataclass(frozen=True)
class AttachmentSource:
    owner_id: str
    resident_id: str
    source_kind: str
    source_id: str
    message_id: str | None = None
    task_id: str | None = None
    session_id: str | None = None
    conversation_id: str | None = None


@dataclass(frozen=True)
class SummaryArtifact:
    summary_id: str
    attachment_id: str
    adapter: str
    text: str
    source_checksum: str
    created_at: str
    is_source_content: bool = False


@dataclass
class AttachmentRecord:
    attachment_id: str
    original_name: str
    media_type: str
    extension: str
    size_bytes: int
    checksum: str
    storage_path: str
    duplicate_of: str | None
    classification: str
    owner_id: str
    resident_id: str
    source_kind: str
    source_id: str
    message_id: str | None = None
    task_id: str | None = None
    session_id: str | None = None
    conversation_id: str | None = None
    redaction_state: str = "none"
    retention_state: str = "active"
    created_at: str = field(default_factory=_now)
    summaries: list[SummaryArtifact] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class AttachmentRejected(ValueError):
    """Raised when an attachment fails safe intake validation."""


class ResidentAttachmentExchange:
    def __init__(self, *, policy: AttachmentPolicy | None = None, now: Callable[[], str] | None = None) -> None:
        self.policy = policy or AttachmentPolicy()
        self.now = now or _now
        self.records: dict[str, AttachmentRecord] = {}
        self.checksum_index: dict[str, str] = {}
        self.audit_events: list[dict[str, Any]] = []

    def intake(self, *, name: str, content: bytes, source: AttachmentSource, classification: str, media_type: str | None = None, metadata: dict[str, Any] | None = None) -> AttachmentRecord:
        ext = PurePosixPath(name).suffix.lower()
        self._validate(name=name, content=content, extension=ext, media_type=media_type)
        checksum = sha256(content).hexdigest()
        duplicate_of = self.checksum_index.get(checksum)
        attachment_id = f"att_{checksum[:16]}"
        expected_media_type = self.policy.allowed_extensions[ext]
        detected_media_type = media_type or mimetypes.types_map.get(ext) or expected_media_type
        path = self.storage_path(source, attachment_id, checksum, ext)
        record = AttachmentRecord(
            attachment_id=attachment_id,
            original_name=PurePosixPath(name).name,
            media_type=detected_media_type,
            extension=ext,
            size_bytes=len(content),
            checksum=checksum,
            storage_path=path,
            duplicate_of=duplicate_of,
            classification=classification,
            owner_id=source.owner_id,
            resident_id=source.resident_id,
            source_kind=source.source_kind,
            source_id=source.source_id,
            message_id=source.message_id,
            task_id=source.task_id,
            session_id=source.session_id,
            conversation_id=source.conversation_id,
            created_at=self.now(),
            metadata={"source_linked": True, "expected_media_type": expected_media_type, **(metadata or {})},
        )
        self.records[attachment_id] = record
        self.checksum_index.setdefault(checksum, attachment_id)
        self._audit("attachment_intake", record, duplicate_of=duplicate_of)
        return record

    def add_summary(self, attachment_id: str, *, adapter: str, text: str) -> SummaryArtifact:
        record = self._record(attachment_id)
        kind = "image" if record.media_type.startswith("image/") else "document"
        if adapter not in {"image_summary", "document_summary", f"{kind}_summary"}:
            raise AttachmentRejected(f"unsupported summary adapter for {record.media_type}: {adapter}")
        summary = SummaryArtifact(
            summary_id=f"sum_{record.checksum[:12]}_{len(record.summaries) + 1}",
            attachment_id=attachment_id,
            adapter=adapter,
            text=text,
            source_checksum=record.checksum,
            created_at=self.now(),
            is_source_content=False,
        )
        record.summaries.append(summary)
        self._audit("attachment_summary_created", record, adapter=adapter, source_content=False)
        return summary

    def read(self, attachment_id: str, *, actor_id: str, purpose: str, include_sensitive: bool = False) -> dict[str, Any]:
        record = self._record(attachment_id)
        self._guard_access(record, include_sensitive)
        self._audit("attachment_read", record, actor_id=actor_id, purpose=purpose, sensitive=record.classification in SENSITIVE_CLASSIFICATIONS)
        return self._safe_payload(record, include_download=False)

    def download(self, attachment_id: str, *, actor_id: str, purpose: str, include_sensitive: bool = False) -> dict[str, Any]:
        record = self._record(attachment_id)
        self._guard_access(record, include_sensitive)
        self._audit("attachment_download", record, actor_id=actor_id, purpose=purpose, sensitive=record.classification in SENSITIVE_CLASSIFICATIONS)
        return {**self._safe_payload(record, include_download=True), "download_allowed": True}

    def export_manifest(self, attachment_ids: Iterable[str], *, actor_id: str, purpose: str, include_sensitive: bool = False) -> dict[str, Any]:
        items = [self.read(aid, actor_id=actor_id, purpose=purpose, include_sensitive=include_sensitive) for aid in attachment_ids]
        manifest = {"kind": "resident_attachment_export", "created_at": self.now(), "items": items, "content_included": False}
        self.audit_events.append({"event": "attachment_export", "actor_id": actor_id, "purpose": purpose, "count": len(items), "created_at": self.now()})
        return manifest

    def archive(self, attachment_id: str, *, actor_id: str, reason: str, state: str = "archived") -> AttachmentRecord:
        if state not in RETENTION_STATES - {"active"}:
            raise AttachmentRejected(f"unsupported retention state: {state}")
        record = self._record(attachment_id)
        record.retention_state = state
        if state == "redacted":
            record.redaction_state = "redacted"
        self._audit("attachment_retention_changed", record, actor_id=actor_id, reason=reason, retention_state=state)
        return record

    def office_payload(self, attachment_id: str) -> dict[str, Any]:
        record = self._record(attachment_id)
        return {"kind": "office_attachment_card", "attachment": self._safe_payload(record, include_download=True), "open_webui_compatible": True, "source_content_included": False}

    def storage_path(self, source: AttachmentSource, attachment_id: str, checksum: str, extension: str) -> str:
        return "/".join([
            self.policy.root,
            _slug(source.owner_id),
            _slug(source.resident_id),
            _slug(source.source_kind),
            _slug(source.source_id),
            checksum[:2],
            f"{attachment_id}{extension}",
        ])

    def _validate(self, *, name: str, content: bytes, extension: str, media_type: str | None) -> None:
        if not name or PurePosixPath(name).name in {"", ".", ".."} or "\x00" in name:
            raise AttachmentRejected("invalid attachment name")
        if extension in self.policy.dangerous_extensions:
            raise AttachmentRejected(f"dangerous extension rejected: {extension}")
        if extension not in self.policy.allowed_extensions:
            raise AttachmentRejected(f"unsupported extension: {extension}")
        if not content:
            raise AttachmentRejected("empty attachments are not accepted")
        if len(content) > self.policy.max_bytes:
            raise AttachmentRejected("attachment exceeds maximum size")
        expected = self.policy.allowed_extensions[extension]
        if media_type and media_type != expected:
            raise AttachmentRejected(f"media type {media_type} does not match {extension} ({expected})")

    def _guard_access(self, record: AttachmentRecord, include_sensitive: bool) -> None:
        if record.retention_state in {"deleted", "redacted"}:
            raise AttachmentRejected(f"attachment is {record.retention_state}")
        if record.classification in SENSITIVE_CLASSIFICATIONS and not include_sensitive:
            raise AttachmentRejected("sensitive attachment access requires explicit authorization")

    def _safe_payload(self, record: AttachmentRecord, *, include_download: bool) -> dict[str, Any]:
        return {
            "attachment_id": record.attachment_id,
            "original_name": record.original_name,
            "media_type": record.media_type,
            "size_bytes": record.size_bytes,
            "checksum": record.checksum,
            "storage_path": record.storage_path,
            "classification": record.classification,
            "owner_id": record.owner_id,
            "resident_id": record.resident_id,
            "links": {"message_id": record.message_id, "task_id": record.task_id, "session_id": record.session_id, "conversation_id": record.conversation_id, "source_kind": record.source_kind, "source_id": record.source_id},
            "retention_state": record.retention_state,
            "redaction_state": record.redaction_state,
            "duplicate_of": record.duplicate_of,
            "summaries": [s.__dict__ for s in record.summaries],
            "download_path": record.storage_path if include_download else None,
            "source_content_included": False,
        }

    def _record(self, attachment_id: str) -> AttachmentRecord:
        if attachment_id not in self.records:
            raise KeyError(attachment_id)
        return self.records[attachment_id]

    def _audit(self, event: str, record: AttachmentRecord, **extra: Any) -> None:
        self.audit_events.append({"event": event, "attachment_id": record.attachment_id, "classification": record.classification, "created_at": self.now(), **extra})
