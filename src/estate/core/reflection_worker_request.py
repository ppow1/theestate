"""Create governed worker requests for reflection and continuity work.

The request artifact is a local collaboration message. It delegates bounded work
without granting constitutional authority, queue control, provider execution, or
approval power to the recipient.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from estate.core.paths import ESTATE_ROOT


REQUIRED_FIELDS = (
    "request_id",
    "worker",
    "office",
    "assignment",
    "authority_reference",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _root(root: str | Path | None) -> Path:
    return Path(root) if root is not None else ESTATE_ROOT


def _slug(value: str) -> str:
    slug = "".join(ch.lower() if ch.isalnum() else "_" for ch in str(value))
    return "_".join(part for part in slug.split("_") if part) or "request"


def _clean_list(values: Iterable[str] | None) -> list[str]:
    return [str(value).strip() for value in (values or []) if str(value).strip()]


def build_reflection_worker_request(
    *,
    request_id: str,
    worker: str,
    office: str,
    assignment: str,
    authority_reference: str,
    deliverables: Iterable[str] | None = None,
    constraints: Iterable[str] | None = None,
    related_artifacts: Iterable[str] | None = None,
    created_by: str = "Chief Architect",
) -> dict:
    """Build a deterministic, non-authoritative worker-request payload."""

    values = {
        "request_id": request_id,
        "worker": worker,
        "office": office,
        "assignment": assignment,
        "authority_reference": authority_reference,
    }
    missing = [name for name in REQUIRED_FIELDS if not str(values[name] or "").strip()]
    if missing:
        raise ValueError(f"missing required input(s): {', '.join(missing)}")

    return {
        "schema_version": "1.0",
        "request_id": str(request_id).strip(),
        "created_at": _now(),
        "created_by": str(created_by).strip() or "Chief Architect",
        "destination": str(worker).strip(),
        "office": str(office).strip(),
        "status": "open",
        "requires_ack": True,
        "ack_status": "pending",
        "authority_reference": str(authority_reference).strip(),
        "assignment": str(assignment).strip(),
        "deliverables": _clean_list(deliverables),
        "constraints": _clean_list(constraints),
        "related_artifacts": _clean_list(related_artifacts),
        "authority_boundaries": {
            "may_approve_renewal": False,
            "may_grant_constitutional_authority": False,
            "may_control_operational_queues": False,
            "may_execute_providers": False,
            "may_merge_code": False,
        },
    }


def write_reflection_worker_request(
    *,
    request_id: str,
    worker: str,
    office: str,
    assignment: str,
    authority_reference: str,
    deliverables: Iterable[str] | None = None,
    constraints: Iterable[str] | None = None,
    related_artifacts: Iterable[str] | None = None,
    created_by: str = "Chief Architect",
    root: str | Path | None = None,
) -> Path:
    """Write one request artifact, rejecting conflicting duplicate identifiers."""

    base = _root(root)
    payload = build_reflection_worker_request(
        request_id=request_id,
        worker=worker,
        office=office,
        assignment=assignment,
        authority_reference=authority_reference,
        deliverables=deliverables,
        constraints=constraints,
        related_artifacts=related_artifacts,
        created_by=created_by,
    )
    path = (
        base
        / "collaboration"
        / "messages"
        / f"reflection_worker_request_{_slug(request_id)}.json"
    )
    path.parent.mkdir(parents=True, exist_ok=True)

    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        comparable_existing = dict(existing)
        comparable_payload = dict(payload)
        comparable_existing.pop("created_at", None)
        comparable_payload.pop("created_at", None)
        if comparable_existing == comparable_payload:
            return path
        raise ValueError(f"conflicting request already exists: {path}")

    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(rendered, encoding="utf-8")
    temporary.replace(path)
    return path
