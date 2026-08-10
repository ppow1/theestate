from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from estate.core.operational_events import OperationalEvent, validate_iso_timestamp
from estate.core.operational_status import record_operational_event
from estate.core.paths import ESTATE_ROOT
from estate.core.provider_catalog import load_provider_catalog

ALLOWED_HEALTH_STATUSES = {"available", "degraded", "saturated", "out_of_quota", "blocked", "offline", "unknown"}
ALLOWED_CLASSIFICATIONS = {"Public", "Estate Internal", "Restricted", "Steward Only", "Local Only"}
SENSITIVE_CLASSIFICATIONS = {"Restricted", "Steward Only", "Local Only"}
ATTENTION_STATUSES = {"degraded", "saturated", "out_of_quota", "blocked", "offline"}
HEALTH_RECORDS_DIR = Path("runtime/providers/health/records")
HEALTH_STATUS_DIR = Path("runtime/providers/health/status")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _require_str(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} is required")
    return value


def _string_list(data: dict[str, Any], key: str) -> list[str]:
    value = data.get(key) or []
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{key} must be a list of strings")
    return value


@dataclass
class ProviderHealthRecord:
    health_id: str
    provider_id: str
    checked_at: str
    reported_by: str
    status: str
    message: str
    classification: str
    source: str = "manual"
    expires_at: str | None = None
    capabilities_available: list[str] = field(default_factory=list)
    capabilities_unavailable: list[str] = field(default_factory=list)
    requires_attention: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, *, provider_id: str, status: str, reported_by: str, message: str, classification: str = "Estate Internal", **kwargs: Any) -> "ProviderHealthRecord":
        return cls(health_id=f"ph-{uuid4().hex}", provider_id=provider_id, checked_at=utc_now_iso(), reported_by=reported_by, status=status, message=message, classification=classification, requires_attention=status in ATTENTION_STATUSES, **kwargs)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProviderHealthRecord":
        if not isinstance(data, dict):
            raise ValueError("provider health record must be an object")
        rec = cls(
            health_id=_require_str(data, "health_id"), provider_id=_require_str(data, "provider_id"), checked_at=_require_str(data, "checked_at"),
            reported_by=_require_str(data, "reported_by"), status=_require_str(data, "status"), message=_require_str(data, "message"), classification=_require_str(data, "classification"),
            source=data.get("source") or "manual", expires_at=data.get("expires_at"), capabilities_available=_string_list(data, "capabilities_available"), capabilities_unavailable=_string_list(data, "capabilities_unavailable"),
            requires_attention=bool(data.get("requires_attention", False)), metadata=data.get("metadata") or {},
        )
        rec.validate()
        return rec

    def validate(self) -> None:
        for key in ["health_id", "provider_id", "checked_at", "reported_by", "status", "message", "classification", "source"]:
            if not isinstance(getattr(self, key), str) or not getattr(self, key).strip():
                raise ValueError(f"{key} is required")
        if self.status not in ALLOWED_HEALTH_STATUSES:
            raise ValueError(f"unknown health status '{self.status}'")
        if self.classification not in ALLOWED_CLASSIFICATIONS:
            raise ValueError(f"unknown classification '{self.classification}'")
        validate_iso_timestamp(self.checked_at, "checked_at")
        if self.expires_at:
            validate_iso_timestamp(self.expires_at, "expires_at")
        if not isinstance(self.metadata, dict):
            raise ValueError("metadata must be an object")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


def safe_message(record: ProviderHealthRecord) -> str:
    if record.classification in SENSITIVE_CLASSIFICATIONS and record.metadata.get("summary_safe") is not True:
        return "Sensitive provider health message redacted."
    return record.message


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _record_path(root: Path, record: ProviderHealthRecord) -> Path:
    safe_id = record.provider_id.replace("/", "_")
    return root / HEALTH_RECORDS_DIR / f"{record.checked_at[:10]}_{safe_id}_{record.health_id}.json"


def load_health_records(root: Path | None = None) -> list[ProviderHealthRecord]:
    base = (root or ESTATE_ROOT) / HEALTH_RECORDS_DIR
    if not base.exists():
        return []
    
    records = []
    for p in sorted(base.glob("*.json")):
        data = json.loads(p.read_text(encoding="utf-8"))
        if "health_id" in data:
            records.append(ProviderHealthRecord.from_dict(data))
    return records


def latest_health_by_provider(root: Path | None = None) -> dict[str, ProviderHealthRecord]:
    latest: dict[str, ProviderHealthRecord] = {}
    for rec in load_health_records(root):
        if rec.provider_id not in latest or rec.checked_at >= latest[rec.provider_id].checked_at:
            latest[rec.provider_id] = rec
    return latest


def _catalog(root: Path):
    try:
        return load_provider_catalog(root / "config" / "providers" / "catalog.json")
    except Exception:
        return None


def validate_provider(provider_id: str, *, root: Path | None = None, force: bool = False) -> tuple[Any | None, str | None]:
    catalog = _catalog(root or ESTATE_ROOT)
    if catalog is None:
        return None, "Provider catalog unavailable; recording manual status without catalog validation."
    try:
        provider = catalog.get_provider(provider_id)
    except KeyError as exc:
        if force:
            return None, f"Unknown provider recorded by force: {provider_id}"
        raise ValueError(str(exc)) from exc
    if provider.status in {"deprecated", "blocked"} and not force:
        raise ValueError(f"provider '{provider_id}' is {provider.status}; use --force to record status")
    return provider, None


def write_health_record(record: ProviderHealthRecord, root: Path | None = None, *, validate_catalog: bool = True, force: bool = False) -> dict[str, Path | str | None]:
    root = root or ESTATE_ROOT
    record.validate()
    warning = None
    if validate_catalog:
        _, warning = validate_provider(record.provider_id, root=root, force=force)
    path = _record_path(root, record)
    _write_json(path, record.to_dict())
    latest_path = root / HEALTH_STATUS_DIR / "latest.json"
    _write_json(latest_path, {pid: rec.to_dict() for pid, rec in latest_health_by_provider(root).items()})
    summary = generate_provider_health_summary(root=root, write=True)
    if record.status in ATTENTION_STATUSES:
        event = OperationalEvent.create(event_type="Worker Blocked" if record.status in {"blocked", "offline"} else "Checkpoint Reached", state="Blocked" if record.status in {"blocked", "offline"} else "Waiting", classification=record.classification, message=safe_message(record), provider_id=record.provider_id, requires_attention=record.requires_attention, artifact_paths=[str(path.relative_to(root))], metadata={"provider_health_id": record.health_id, "summary_safe": record.metadata.get("summary_safe", False)})
        record_operational_event(event, root=root)
    return {"record": path, "latest": latest_path, "summary_json": root / HEALTH_STATUS_DIR / "summary.json", "summary_md": root / HEALTH_STATUS_DIR / "summary.md", "warning": warning}


def generate_provider_health_summary(root: Path | None = None, *, write: bool = False) -> dict[str, Any]:
    root = root or ESTATE_ROOT
    health = latest_health_by_provider(root)
    from estate.core.provider_capacity import latest_capacity_by_provider
    capacity = latest_capacity_by_provider(root)
    catalog = _catalog(root)
    catalog_ids = {p.provider_id for p in catalog.providers} if catalog else set()
    ids = sorted(set(health) | set(capacity) | catalog_ids)
    providers = []
    for pid in ids:
        h = health.get(pid)
        c = capacity.get(pid)
        descriptor = None
        if catalog:
            try: descriptor = catalog.get_provider(pid)
            except KeyError: descriptor = None
        providers.append({"provider_id": pid, "display_name": getattr(descriptor, "display_name", None), "provider_type": getattr(descriptor, "provider_type", None), "health_status": h.status if h else "unknown", "capacity_state": c.capacity_state if c else "unknown", "active_jobs": c.active_jobs if c else 0, "max_jobs": c.max_jobs if c else None, "quota_remaining": c.quota_remaining if c else None, "quota_resets_at": c.quota_resets_at if c else None, "queue_depth": c.queue_depth if c else 0, "requires_attention": bool((h and h.requires_attention) or (h and h.status in ATTENTION_STATUSES)), "last_checked_at": max([x for x in [h.checked_at if h else None, c.checked_at if c else None] if x], default=None), "safe_message": safe_message(h) if h else ""})
    counts = Counter(p["health_status"] for p in providers)
    summary = {"generated_at": utc_now_iso(), "provider_count": len(providers), "available_count": counts.get("available", 0), "degraded_count": counts.get("degraded", 0), "saturated_count": counts.get("saturated", 0), "blocked_count": counts.get("blocked", 0), "out_of_quota_count": counts.get("out_of_quota", 0), "unknown_count": counts.get("unknown", 0), "providers": providers}
    if write:
        _write_json(root / HEALTH_STATUS_DIR / "summary.json", summary)
        (root / HEALTH_STATUS_DIR / "summary.md").write_text(format_provider_health_summary(summary), encoding="utf-8")
    return summary


def format_provider_health_summary(summary: dict[str, Any]) -> str:
    lines = ["# Provider Health Summary", "", f"Generated: {summary.get('generated_at')}", f"Providers: {summary.get('provider_count', 0)}", "", "Provider ID | Health | Capacity | Active/Max | Queue | Attention | Message"]
    for p in summary.get("providers", []):
        lines.append(f"{p['provider_id']} | {p['health_status']} | {p['capacity_state']} | {p['active_jobs']}/{p.get('max_jobs') or '?'} | {p['queue_depth']} | {p['requires_attention']} | {p.get('safe_message','')}")
    return "\n".join(lines).rstrip() + "\n"
