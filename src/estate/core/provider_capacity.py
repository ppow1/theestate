from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4

from estate.core.operational_events import validate_iso_timestamp
from estate.core.paths import ESTATE_ROOT
from estate.core.provider_health import ALLOWED_CLASSIFICATIONS, HEALTH_STATUS_DIR, utc_now_iso, validate_provider, _write_json

ALLOWED_CAPACITY_STATES = {"idle", "available", "busy", "saturated", "quota_limited", "unknown"}
CAPACITY_RECORDS_DIR = Path("runtime/providers/health/records")


def _require_str(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} is required")
    return value


@dataclass
class ProviderCapacityRecord:
    capacity_id: str
    provider_id: str
    checked_at: str
    reported_by: str
    capacity_state: str
    classification: str
    active_jobs: int = 0
    max_jobs: int | None = None
    queue_depth: int = 0
    quota_remaining: int | float | str | None = None
    quota_resets_at: str | None = None
    estimated_available_at: str | None = None
    message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, *, provider_id: str, capacity_state: str, reported_by: str, classification: str = "Estate Internal", **kwargs: Any) -> "ProviderCapacityRecord":
        return cls(capacity_id=f"pc-{uuid4().hex}", provider_id=provider_id, checked_at=utc_now_iso(), reported_by=reported_by, capacity_state=capacity_state, classification=classification, **kwargs)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProviderCapacityRecord":
        if not isinstance(data, dict):
            raise ValueError("provider capacity record must be an object")
        rec = cls(
            capacity_id=_require_str(data, "capacity_id"), provider_id=_require_str(data, "provider_id"), checked_at=_require_str(data, "checked_at"), reported_by=_require_str(data, "reported_by"), capacity_state=_require_str(data, "capacity_state"), classification=_require_str(data, "classification"), active_jobs=int(data.get("active_jobs", 0)), max_jobs=data.get("max_jobs"), queue_depth=int(data.get("queue_depth", 0)), quota_remaining=data.get("quota_remaining"), quota_resets_at=data.get("quota_resets_at"), estimated_available_at=data.get("estimated_available_at"), message=data.get("message"), metadata=data.get("metadata") or {},
        )
        rec.validate(); return rec

    def validate(self) -> None:
        for key in ["capacity_id", "provider_id", "checked_at", "reported_by", "capacity_state", "classification"]:
            if not isinstance(getattr(self, key), str) or not getattr(self, key).strip():
                raise ValueError(f"{key} is required")
        if self.capacity_state not in ALLOWED_CAPACITY_STATES:
            raise ValueError(f"unknown capacity state '{self.capacity_state}'")
        if self.classification not in ALLOWED_CLASSIFICATIONS:
            raise ValueError(f"unknown classification '{self.classification}'")
        validate_iso_timestamp(self.checked_at, "checked_at")
        for ts in ["quota_resets_at", "estimated_available_at"]:
            if getattr(self, ts): validate_iso_timestamp(getattr(self, ts), ts)
        if self.active_jobs < 0 or self.queue_depth < 0:
            raise ValueError("capacity counters must be non-negative")
        if self.max_jobs is not None:
            self.max_jobs = int(self.max_jobs)
            if self.max_jobs < 0: raise ValueError("max_jobs must be non-negative")
        if not isinstance(self.metadata, dict): raise ValueError("metadata must be an object")

    def to_dict(self) -> dict[str, Any]:
        self.validate(); return asdict(self)


def _record_path(root: Path, record: ProviderCapacityRecord) -> Path:
    return root / CAPACITY_RECORDS_DIR / f"{record.checked_at[:10]}_{record.provider_id.replace('/', '_')}_{record.capacity_id}.json"


def load_capacity_records(root: Path | None = None) -> list[ProviderCapacityRecord]:
    base = (root or ESTATE_ROOT) / CAPACITY_RECORDS_DIR
    if not base.exists(): return []
    records = []
    for p in sorted(base.glob("*.json")):
        data = json.loads(p.read_text(encoding="utf-8"))
        if "capacity_id" in data: records.append(ProviderCapacityRecord.from_dict(data))
    return records


def latest_capacity_by_provider(root: Path | None = None) -> dict[str, ProviderCapacityRecord]:
    latest = {}
    for rec in load_capacity_records(root):
        if rec.provider_id not in latest or rec.checked_at >= latest[rec.provider_id].checked_at:
            latest[rec.provider_id] = rec
    return latest


def write_capacity_record(record: ProviderCapacityRecord, root: Path | None = None, *, validate_catalog: bool = True, force: bool = False) -> dict[str, Path | str | None]:
    root = root or ESTATE_ROOT
    record.validate()
    warning = None
    if validate_catalog:
        _, warning = validate_provider(record.provider_id, root=root, force=force)
    path = _record_path(root, record)
    _write_json(path, record.to_dict())
    _write_json(root / HEALTH_STATUS_DIR / "latest_capacity.json", {pid: rec.to_dict() for pid, rec in latest_capacity_by_provider(root).items()})
    from estate.core.provider_health import generate_provider_health_summary
    generate_provider_health_summary(root=root, write=True)
    return {"record": path, "latest": root / HEALTH_STATUS_DIR / "latest_capacity.json", "summary_json": root / HEALTH_STATUS_DIR / "summary.json", "summary_md": root / HEALTH_STATUS_DIR / "summary.md", "warning": warning}
