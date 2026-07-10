from __future__ import annotations

import copy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

ACTIVE = "active"
AVAILABLE = "available"
OFF_DUTY = "off_duty"
BLOCKED = "blocked"
STALE = "stale"
ATTENTION_REQUIRED = "attention_required"
MISSING_EVIDENCE = "missing_evidence"


def parse_utc(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


@dataclass(frozen=True)
class DrillDownLink:
    kind: str
    label: str
    uri: str

    def to_dict(self) -> dict[str, str]:
        return {"kind": self.kind, "label": self.label, "uri": self.uri}


@dataclass(frozen=True)
class EvidenceReference:
    id: str
    title: str
    uri: str
    observed_at: str
    supports: str
    verified: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "uri": self.uri,
            "observed_at": self.observed_at,
            "supports": self.supports,
            "verified": self.verified,
        }


@dataclass(frozen=True)
class ResidentPresenceInput:
    resident_id: str
    resident_name: str
    office: str
    duty_state: str
    status: str
    updated_at: str
    active_assignment: str | None = None
    last_completed_duty: str | None = None
    blocker: str | None = None
    attention_required: bool = False
    assignment_uri: str | None = None
    conversation_uri: str | None = None
    mailbox_uri: str | None = None
    work_package_uri: str | None = None
    evidence: tuple[EvidenceReference, ...] = field(default_factory=tuple)
    extra_links: tuple[DrillDownLink, ...] = field(default_factory=tuple)


def _base_links(record: ResidentPresenceInput) -> list[DrillDownLink]:
    links: list[DrillDownLink] = []
    for kind, label, uri in (
        ("assignment", "Active assignment", record.assignment_uri),
        ("conversation", "Conversation", record.conversation_uri),
        ("mailbox", "Mailbox", record.mailbox_uri),
        ("work_package", "Work package", record.work_package_uri),
    ):
        if uri:
            links.append(DrillDownLink(kind=kind, label=label, uri=uri))
    links.extend(record.extra_links)
    return links


def build_presence_card(record: ResidentPresenceInput, *, as_of: str, stale_after_minutes: int = 60) -> dict[str, Any]:
    age_minutes = (parse_utc(as_of) - parse_utc(record.updated_at)).total_seconds() / 60
    stale = age_minutes > stale_after_minutes
    evidence = [item.to_dict() for item in record.evidence]
    missing_evidence = len(evidence) == 0
    attention_reasons: list[str] = []
    if record.attention_required:
        attention_reasons.append("source marked attention_required")
    if record.blocker:
        attention_reasons.append("blocker present")
    if stale:
        attention_reasons.append("presence stale")
    if missing_evidence:
        attention_reasons.append("missing supporting evidence")

    display_status = STALE if stale else record.status
    if record.blocker:
        display_status = BLOCKED
    elif attention_reasons:
        display_status = ATTENTION_REQUIRED

    return {
        "schema": "estate.resident_presence.v1",
        "staged_not_installed": True,
        "resident_id": record.resident_id,
        "resident_name": record.resident_name,
        "office": record.office,
        "duty_state": record.duty_state,
        "status": display_status,
        "source_status": record.status,
        "updated_at": record.updated_at,
        "as_of": as_of,
        "freshness": {"age_minutes": age_minutes, "stale": stale, "stale_after_minutes": stale_after_minutes},
        "active_assignment": record.active_assignment,
        "last_completed_duty": record.last_completed_duty,
        "blocker": record.blocker,
        "attention_required": bool(attention_reasons),
        "attention_reasons": attention_reasons,
        "drill_down_links": [link.to_dict() for link in _base_links(record)],
        "evidence": evidence,
        "missing_evidence": missing_evidence,
        "truthfulness_guardrails": {
            "fabricated_activity": False,
            "hidden_monitoring": False,
            "authority_expansion": False,
            "note": "Card only reflects supplied resident presence inputs and cited evidence.",
        },
    }


def build_presence_surface(records: Iterable[ResidentPresenceInput], *, as_of: str, stale_after_minutes: int = 60) -> list[dict[str, Any]]:
    cards = [build_presence_card(record, as_of=as_of, stale_after_minutes=stale_after_minutes) for record in records]
    return sorted(cards, key=lambda card: (card["office"], card["resident_name"], card["resident_id"]))


def filter_presence(
    cards: Iterable[Mapping[str, Any]],
    *,
    resident: str | None = None,
    office: str | None = None,
    status: str | None = None,
    attention_state: bool | None = None,
) -> list[dict[str, Any]]:
    filtered: list[dict[str, Any]] = []
    resident_query = resident.lower() if resident else None
    for card in cards:
        if resident_query and resident_query not in f"{card.get('resident_id', '')} {card.get('resident_name', '')}".lower():
            continue
        if office and card.get("office") != office:
            continue
        if status and card.get("status") != status:
            continue
        if attention_state is not None and bool(card.get("attention_required")) is not attention_state:
            continue
        filtered.append(copy.deepcopy(dict(card)))
    return filtered


def open_drill_down(card: Mapping[str, Any], kind: str) -> dict[str, Any]:
    for link in card.get("drill_down_links", []):
        if link.get("kind") == kind:
            return {"openable": True, "kind": kind, "uri": link.get("uri"), "label": link.get("label")}
    return {"openable": False, "kind": kind, "reason": "no link supplied by source record"}
