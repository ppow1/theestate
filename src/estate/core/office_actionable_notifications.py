from __future__ import annotations

import copy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping

LOCAL_ACKNOWLEDGED = "locally_acknowledged"
AUTHORITATIVE_CLOSED = "authoritatively_closed"
OPEN = "open"
SNOOZED = "snoozed"
ASSIGNED = "assigned"
FOLLOW_UP = "follow_up_scheduled"
ROUTED = "routed"
BLOCKED = "blocked"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_utc(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


@dataclass(frozen=True)
class NotificationEvidence:
    id: str
    title: str
    source_uri: str
    created_at: str
    severity: str = "info"
    delivery_status: str = "delivered"
    delivery_error: str | None = None
    authoritative_status: str = OPEN
    payload: Mapping[str, Any] = field(default_factory=dict)


@dataclass
class ActionableNotification:
    evidence: NotificationEvidence
    local_status: str = OPEN
    assignee: str | None = None
    snoozed_until: str | None = None
    follow_up_at: str | None = None
    routed_to: str | None = None
    route_reason: str | None = None
    local_acknowledged_at: str | None = None
    authoritative_closed_at: str | None = None
    action_log: list[dict[str, Any]] = field(default_factory=list)

    def to_snapshot(self) -> dict[str, Any]:
        return {
            "schema": "estate.actionable_notification.v1",
            "installed_by_wp_0531": True,
            "evidence": evidence_to_dict(self.evidence),
            "local_status": self.local_status,
            "assignee": self.assignee,
            "snoozed_until": self.snoozed_until,
            "follow_up_at": self.follow_up_at,
            "routed_to": self.routed_to,
            "route_reason": self.route_reason,
            "local_acknowledged_at": self.local_acknowledged_at,
            "authoritative_closed_at": self.authoritative_closed_at,
            "action_log": copy.deepcopy(self.action_log),
        }

    @classmethod
    def from_snapshot(cls, snapshot: Mapping[str, Any]) -> "ActionableNotification":
        return cls(
            evidence=evidence_from_dict(snapshot["evidence"]),
            local_status=str(snapshot.get("local_status", OPEN)),
            assignee=snapshot.get("assignee"),
            snoozed_until=snapshot.get("snoozed_until"),
            follow_up_at=snapshot.get("follow_up_at"),
            routed_to=snapshot.get("routed_to"),
            route_reason=snapshot.get("route_reason"),
            local_acknowledged_at=snapshot.get("local_acknowledged_at"),
            authoritative_closed_at=snapshot.get("authoritative_closed_at"),
            action_log=copy.deepcopy(list(snapshot.get("action_log", []))),
        )


def evidence_to_dict(evidence: NotificationEvidence) -> dict[str, Any]:
    return {
        "id": evidence.id,
        "title": evidence.title,
        "source_uri": evidence.source_uri,
        "created_at": evidence.created_at,
        "severity": evidence.severity,
        "delivery_status": evidence.delivery_status,
        "delivery_error": evidence.delivery_error,
        "authoritative_status": evidence.authoritative_status,
        "payload": copy.deepcopy(dict(evidence.payload)),
    }


def evidence_from_dict(data: Mapping[str, Any]) -> NotificationEvidence:
    return NotificationEvidence(
        id=str(data["id"]),
        title=str(data["title"]),
        source_uri=str(data["source_uri"]),
        created_at=str(data["created_at"]),
        severity=str(data.get("severity", "info")),
        delivery_status=str(data.get("delivery_status", "delivered")),
        delivery_error=data.get("delivery_error"),
        authoritative_status=str(data.get("authoritative_status", OPEN)),
        payload=copy.deepcopy(dict(data.get("payload", {}))),
    )


def build_center(evidence_items: list[NotificationEvidence]) -> dict[str, ActionableNotification]:
    return {item.id: ActionableNotification(evidence=item) for item in sorted(evidence_items, key=lambda item: (item.created_at, item.id))}


def _log(notification: ActionableNotification, action: str, message: str, **details: Any) -> None:
    notification.action_log.append({"at": utc_now(), "action": action, "message": message, "details": details})


def acknowledge(notification: ActionableNotification, steward: str) -> dict[str, Any]:
    if notification.evidence.authoritative_status == AUTHORITATIVE_CLOSED:
        notification.local_status = LOCAL_ACKNOWLEDGED
        notification.local_acknowledged_at = utc_now()
        _log(notification, "acknowledged", "Local acknowledgement recorded; authoritative closure was already present.", steward=steward)
        return {"state": LOCAL_ACKNOWLEDGED, "authoritative_closed": True}
    notification.local_status = LOCAL_ACKNOWLEDGED
    notification.local_acknowledged_at = utc_now()
    _log(notification, "acknowledged", "Local acknowledgement only; source item remains open until canonical closure.", steward=steward)
    return {"state": LOCAL_ACKNOWLEDGED, "authoritative_closed": False, "warning": "local acknowledgement is not authoritative closure"}


def close_authoritatively(notification: ActionableNotification, source_receipt: str) -> dict[str, Any]:
    if not source_receipt:
        notification.local_status = BLOCKED
        _log(notification, "closure_blocked", "Authoritative closure requires a source receipt.")
        return {"state": BLOCKED, "closed": False, "reason": "missing source receipt"}
    notification.authoritative_closed_at = utc_now()
    notification.evidence = NotificationEvidence(**(evidence_to_dict(notification.evidence) | {"authoritative_status": AUTHORITATIVE_CLOSED}))
    _log(notification, "authoritatively_closed", "Canonical source closure receipt recorded.", source_receipt=source_receipt)
    return {"state": AUTHORITATIVE_CLOSED, "closed": True}


def snooze(notification: ActionableNotification, until: str, reason: str) -> dict[str, Any]:
    if parse_utc(until) <= datetime.now(timezone.utc):
        notification.local_status = BLOCKED
        _log(notification, "snooze_blocked", "Snooze target must be in the future.", until=until)
        return {"state": BLOCKED, "snoozed": False, "reason": "snooze target is not in the future"}
    notification.local_status = SNOOZED
    notification.snoozed_until = until
    _log(notification, "snoozed", "Notification snoozed locally.", until=until, reason=reason)
    return {"state": SNOOZED, "snoozed": True}


def assign(notification: ActionableNotification, assignee: str) -> dict[str, Any]:
    if not assignee.strip():
        notification.local_status = BLOCKED
        _log(notification, "assignment_blocked", "Assignment requires a non-empty assignee.")
        return {"state": BLOCKED, "assigned": False, "reason": "missing assignee"}
    notification.assignee = assignee
    notification.local_status = ASSIGNED
    _log(notification, "assigned", "Notification assigned for follow-through.", assignee=assignee)
    return {"state": ASSIGNED, "assigned": True}


def schedule_follow_up(notification: ActionableNotification, when: str) -> dict[str, Any]:
    if parse_utc(when) <= datetime.now(timezone.utc):
        notification.local_status = BLOCKED
        _log(notification, "follow_up_blocked", "Follow-up date must be in the future.", when=when)
        return {"state": BLOCKED, "scheduled": False, "reason": "follow-up date is not in the future"}
    notification.follow_up_at = when
    notification.local_status = FOLLOW_UP
    _log(notification, "follow_up_scheduled", "Follow-up date recorded.", when=when)
    return {"state": FOLLOW_UP, "scheduled": True}


def route(notification: ActionableNotification, destination: str, reason: str) -> dict[str, Any]:
    if not destination.strip():
        notification.local_status = BLOCKED
        _log(notification, "route_blocked", "Routing requires a destination.")
        return {"state": BLOCKED, "routed": False, "reason": "missing route destination"}
    notification.routed_to = destination
    notification.route_reason = reason
    notification.local_status = ROUTED
    _log(notification, "routed", "Notification routed through canonical routing intent.", destination=destination, reason=reason)
    return {"state": ROUTED, "routed": True}


def open_source(notification: ActionableNotification) -> dict[str, Any]:
    _log(notification, "open_source", "Source URI exposed for canonical evidence review.", source_uri=notification.evidence.source_uri)
    return {"openable": True, "source_uri": notification.evidence.source_uri}


def attention_indicators(notification: ActionableNotification, as_of: str, warn_after_hours: int = 24, escalate_after_hours: int = 72) -> dict[str, Any]:
    age_hours = (parse_utc(as_of) - parse_utc(notification.evidence.created_at)).total_seconds() / 3600
    delivery_failed = notification.evidence.delivery_status != "delivered"
    return {
        "age_hours": age_hours,
        "aged": age_hours >= warn_after_hours,
        "escalated": age_hours >= escalate_after_hours or delivery_failed,
        "delivery_failed": delivery_failed,
        "delivery_error": notification.evidence.delivery_error,
        "blocked": notification.local_status == BLOCKED,
    }


def refresh(center: Mapping[str, ActionableNotification], evidence_items: list[NotificationEvidence]) -> dict[str, ActionableNotification]:
    refreshed = {key: ActionableNotification.from_snapshot(value.to_snapshot()) for key, value in sorted(center.items())}
    for evidence in sorted(evidence_items, key=lambda item: (item.created_at, item.id)):
        if evidence.id in refreshed:
            existing = refreshed[evidence.id]
            existing.evidence = evidence
            _log(existing, "refreshed", "Existing actionable notification refreshed from evidence.")
        else:
            refreshed[evidence.id] = ActionableNotification(evidence=evidence)
    return dict(sorted(refreshed.items()))
