"""Staged resident context assembly pipeline for WP-4024.

This module is intentionally uninstalled.  It consumes existing Estate sources
and caller-provided source snapshots, applies privacy/classification filtering
before assembly, and returns bounded, source-linked context with omission
metadata instead of silently truncating or fabricating unavailable context.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import json
from typing import Any, Iterable

CLASSIFICATION_RANK = {
    "public": 0,
    "metadata_only": 1,
    "estate internal": 2,
    "confidential": 3,
    "restricted": 4,
    "protected": 5,
    "private character material": 6,
}

PROHIBITED_TAGS = {
    "unrestricted_journal",
    "journal_unrestricted",
    "protected_private_character_material",
    "private_character_material",
    "unrelated_record",
}


@dataclass(frozen=True)
class SourceItem:
    id: str
    kind: str
    title: str
    body: str = ""
    resident_id: str | None = None
    classification: str = "Estate Internal"
    path: str | None = None
    modified_at: str | None = None
    tags: tuple[str, ...] = ()
    approved: bool = True
    relevance: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AssemblyRequest:
    resident_id: str
    task: str
    max_chars: int = 6000
    clearance: str = "Estate Internal"
    now: str = "2026-07-11T00:00:00Z"
    stale_after_days: int = 30
    query_terms: tuple[str, ...] = ()


class ResidentContextAssembler:
    """Build deterministic, filtered resident context packets."""

    def __init__(self, repo_root: str | Path = ".") -> None:
        self.repo_root = Path(repo_root)

    def assemble(self, request: AssemblyRequest, extra_sources: Iterable[SourceItem] = ()) -> dict[str, Any]:
        resident = self._load_resident(request.resident_id)
        candidates = [
            self._profile_source(resident),
            *self._load_office_state(request.resident_id),
            SourceItem(
                id="request.current_task",
                kind="current_task",
                title="Current task and blockers",
                body=request.task,
                resident_id=request.resident_id,
                classification="Estate Internal",
                relevance=10_000,
            ),
            *extra_sources,
        ]

        accepted: list[dict[str, Any]] = []
        omitted: list[dict[str, str]] = []
        for source in candidates:
            reason = self._omission_reason(source, request)
            if reason:
                omitted.append({"id": source.id, "title": source.title, "reason": reason})
                continue
            accepted.append(self._render_source(source, request))

        accepted.sort(key=lambda s: (-s["relevance"], s["kind"], s["id"]))
        included, budget_omissions = self._apply_budget(accepted, request.max_chars)
        omitted.extend(budget_omissions)
        omitted.sort(key=lambda item: item["id"])

        return {
            "schema_version": "estate.resident_context_packet.v1.staged",
            "resident_id": request.resident_id,
            "resident_name": resident.get("name"),
            "assembled_at": request.now,
            "budget": {
                "max_chars": request.max_chars,
                "used_chars": sum(item["char_count"] for item in included),
                "strategy": "stable relevance desc, then kind, then id; no partial truncation",
            },
            "classification_filter": {
                "clearance": request.clearance,
                "privacy_first": True,
                "prohibited_tags": sorted(PROHIBITED_TAGS),
            },
            "sections": included,
            "omitted_sources": omitted,
        }

    def _load_resident(self, resident_id: str) -> dict[str, Any]:
        residents = self._read_json("data/registry/residents.json")
        for resident in residents:
            if resident.get("id") == resident_id:
                return resident
        raise ValueError(f"resident not found: {resident_id}")

    def _load_office_state(self, resident_id: str) -> list[SourceItem]:
        personnel = self._read_json("data/registry/personnel.json")
        return [
            SourceItem(
                id=f"personnel.{entry.get('employee_id')}",
                kind="office_role_state",
                title=f"Office state for {entry.get('display_name')}",
                body=json.dumps({
                    "title": entry.get("current_title"),
                    "office": entry.get("current_office"),
                    "status": entry.get("status"),
                    "mailbox_id": entry.get("mailbox_id"),
                }, sort_keys=True),
                resident_id=resident_id,
                classification=entry.get("security_clearance", "metadata_only"),
                path="data/registry/personnel.json",
                relevance=9000,
            )
            for entry in personnel
            if entry.get("resident_id") == resident_id
        ]

    def _profile_source(self, resident: dict[str, Any]) -> SourceItem:
        return SourceItem(
            id=f"resident.{resident['id']}",
            kind="canonical_resident_profile",
            title=f"Canonical profile for {resident.get('name')}",
            body=json.dumps(resident, sort_keys=True),
            resident_id=resident["id"],
            classification=resident.get("classification", "Estate Internal"),
            path="data/registry/residents.json",
            modified_at=resident.get("registered_at") or resident.get("created"),
            relevance=9500,
        )

    def _omission_reason(self, source: SourceItem, request: AssemblyRequest) -> str | None:
        lowered_tags = {tag.lower() for tag in source.tags}
        if lowered_tags & PROHIBITED_TAGS:
            return "privacy boundary: prohibited source category"
        if not source.approved and source.kind == "continuity_artifact":
            return "continuity artifact is not approved"
        if source.resident_id and source.resident_id != request.resident_id:
            return "source belongs to a different resident"
        if CLASSIFICATION_RANK.get(source.classification.lower(), 3) > CLASSIFICATION_RANK.get(request.clearance.lower(), 2):
            return "classification exceeds requester clearance"
        if source.kind == "knowledge_index_record" and not self._matches_query(source, request):
            return "knowledge record is not relevant to request terms"
        if not source.body and source.kind not in {"source_citation"}:
            return "source unavailable or empty"
        return None

    def _matches_query(self, source: SourceItem, request: AssemblyRequest) -> bool:
        if not request.query_terms:
            return True
        haystack = f"{source.title} {source.body} {' '.join(source.tags)}".lower()
        return any(term.lower() in haystack for term in request.query_terms)

    def _render_source(self, source: SourceItem, request: AssemblyRequest) -> dict[str, Any]:
        stale = self._is_stale(source.modified_at, request.now, request.stale_after_days)
        text = source.body
        citation = {"id": source.id, "path": source.path, "classification": source.classification}
        return {
            "id": source.id,
            "kind": source.kind,
            "title": source.title,
            "text": text,
            "source_citation": citation,
            "stale_warning": stale,
            "relevance": source.relevance,
            "char_count": len(text),
        }

    def _apply_budget(self, sources: list[dict[str, Any]], max_chars: int) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
        used = 0
        included: list[dict[str, Any]] = []
        omitted: list[dict[str, str]] = []
        for source in sources:
            if used + source["char_count"] <= max_chars:
                included.append(source)
                used += source["char_count"]
            else:
                omitted.append({"id": source["id"], "title": source["title"], "reason": "deterministic context budget exceeded"})
        return included, omitted

    def _is_stale(self, modified_at: str | None, now: str, stale_after_days: int) -> bool:
        if not modified_at:
            return False
        try:
            modified = self._parse_time(modified_at)
            current = self._parse_time(now)
        except ValueError:
            return True
        return (current - modified).days > stale_after_days

    def _parse_time(self, value: str) -> datetime:
        normalized = value.replace("Z", "+00:00")
        if "T" not in normalized and "+" not in normalized:
            normalized = normalized.replace(" ", "T") + "+00:00"
        parsed = datetime.fromisoformat(normalized)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)

    def _read_json(self, relative_path: str) -> Any:
        with (self.repo_root / relative_path).open(encoding="utf-8") as handle:
            return json.load(handle)
