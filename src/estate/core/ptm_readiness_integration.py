"""Shared PTM readiness binding and revalidation for lifecycle consumers.

Consumers validate PTM authority through this module; they do not calculate
dependency readiness or create alternate readiness records.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from estate.core.ptm_policy import load_freshness_policy
from estate.core.ptm_production_readiness import (
    PtmProductionReadinessResolver,
    PtmReadinessError,
    _load_events,
    read_readiness,
)
from estate.core.ptm_waiver_authority import load_waiver_registry


class PtmReadinessGateError(PermissionError):
    """A bounded PTM authority or freshness failure."""


@dataclass(frozen=True)
class PtmReadinessBinding:
    readiness_resolution_id: str
    readiness_projection_path: str
    readiness_projection_digest: str
    readiness_state: str
    objective_id: str
    enabling_project_id: str | None
    task_or_package_id: str
    source_high_watermark: str
    freshness_policy_id: str | None
    freshness_policy_version: str | None
    freshness_policy_digest: str | None
    waiver_registry_id: str | None
    waiver_registry_version: str | None
    waiver_registry_digest: str | None
    evaluated_at: str
    expires_at: str
    dependency_evidence_references: tuple[str, ...]
    waiver_references: tuple[Mapping[str, Any], ...]

    @classmethod
    def from_record(cls, record: Mapping[str, Any]) -> "PtmReadinessBinding":
        return cls(
            readiness_resolution_id=str(record["resolution_id"]),
            readiness_projection_path=str(record["projection_path"]),
            readiness_projection_digest=str(record["projection_digest"]),
            readiness_state=str(record["readiness_state"]),
            objective_id=str(record["objective_id"]),
            enabling_project_id=record.get("enabling_project_id"),
            task_or_package_id=str(record["task_id"]),
            source_high_watermark=str(record["source_high_watermark"]),
            freshness_policy_id=record.get("freshness_policy_id"),
            freshness_policy_version=record.get("freshness_policy_version"),
            freshness_policy_digest=record.get("freshness_policy_digest"),
            waiver_registry_id=record.get("waiver_authority_registry_id"),
            waiver_registry_version=record.get("waiver_authority_registry_version"),
            waiver_registry_digest=record.get("waiver_authority_registry_digest"),
            evaluated_at=str(record["evaluated_at"]),
            expires_at=str(record["expires_at"]),
            dependency_evidence_references=tuple(
                str(item.get("source_path") or item.get("dependency_id"))
                for item in record.get("source_references", [])
                if item.get("source_path") or item.get("dependency_id")
            ),
            waiver_references=tuple(item for item in record.get("waiver_references", []) if isinstance(item, Mapping)),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self) | {
            "dependency_evidence_references": list(self.dependency_evidence_references),
            "waiver_references": [dict(item) for item in self.waiver_references],
        }


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse(value: str) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("PTM timestamp has no timezone")
    return parsed.astimezone(timezone.utc)


def _latest_source_event(root: Path, record: Mapping[str, Any]) -> str | None:
    candidates = []
    for event in _load_events(root):
        if event.get("event_type") != "task.readiness_inputs":
            continue
        payload = event.get("payload") or {}
        if payload.get("objective_id") == record.get("objective_id") and payload.get("task_id") == record.get("task_id"):
            candidates.append(event)
    if not candidates:
        return None
    return max(candidates, key=lambda item: int(item["sequence_number"]))["event_id"]


def _validate_record(root: Path, record: Mapping[str, Any], *, expected: Mapping[str, Any] | None = None) -> PtmReadinessBinding:
    binding = PtmReadinessBinding.from_record(record)
    if binding.readiness_state not in {"ready", "waived"}:
        raise PtmReadinessGateError(f"PTM readiness is {binding.readiness_state}")
    if _parse(binding.expires_at) <= _now():
        raise PtmReadinessGateError("PTM readiness resolution is expired")
    if _latest_source_event(root, record) != binding.source_high_watermark:
        raise PtmReadinessGateError("PTM source high-watermark has changed")
    policy = load_freshness_policy(root, observed_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    registry = load_waiver_registry(root, observed_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    if binding.freshness_policy_id != policy["policy_id"] or binding.freshness_policy_version != policy["policy_version"] or binding.freshness_policy_digest != policy["policy_digest"]:
        raise PtmReadinessGateError("PTM freshness policy identity or digest drifted")
    if binding.waiver_registry_id != registry["registry_id"] or binding.waiver_registry_version != registry["registry_version"] or binding.waiver_registry_digest != registry["registry_digest"]:
        raise PtmReadinessGateError("PTM waiver registry identity or digest drifted")
    if expected:
        for field in ("objective_id", "enabling_project_id", "task_or_package_id"):
            if field in expected and expected[field] != getattr(binding, field):
                raise PtmReadinessGateError(f"PTM {field} does not match lifecycle record")
        if expected.get("readiness_resolution_id") and expected["readiness_resolution_id"] != binding.readiness_resolution_id:
            raise PtmReadinessGateError("PTM readiness resolution identity mismatch")
        if expected.get("readiness_projection_digest") and expected["readiness_projection_digest"] != binding.readiness_projection_digest:
            raise PtmReadinessGateError("PTM readiness projection digest mismatch")
        if expected.get("source_high_watermark") and expected["source_high_watermark"] != binding.source_high_watermark:
            raise PtmReadinessGateError("PTM source high-watermark mismatch")
    return binding


def resolve_and_bind(root: str | Path, *, objective_id: str, enabling_project_id: str | None, task_or_package_id: str, source_high_watermark: str, observed_at: str, resolver: PtmProductionReadinessResolver | None = None) -> PtmReadinessBinding:
    authority = resolver or PtmProductionReadinessResolver(Path(root))
    try:
        resolution = authority.resolve_engineering_readiness(
            objective_id=objective_id,
            enabling_project_id=enabling_project_id,
            task_or_package_id=task_or_package_id,
            source_high_watermark=source_high_watermark,
            observed_at=observed_at,
        )
        return _validate_record(Path(root), resolution.record, expected={"objective_id": objective_id, "enabling_project_id": enabling_project_id, "task_or_package_id": task_or_package_id})
    except (PtmReadinessError, KeyError, ValueError) as exc:
        raise PtmReadinessGateError(str(exc)) from exc


def revalidate_readiness(root: str | Path, binding: Mapping[str, Any], *, commission_id: str | None = None) -> PtmReadinessBinding:
    base = Path(root)
    try:
        record = read_readiness(base, str(binding["readiness_resolution_id"]))
        return _validate_record(base, record, expected={
            "objective_id": binding.get("objective_id"),
            "enabling_project_id": binding.get("enabling_project_id"),
            "task_or_package_id": binding.get("task_or_package_id"),
            "readiness_resolution_id": binding.get("readiness_resolution_id"),
            "readiness_projection_digest": binding.get("readiness_projection_digest"),
            "source_high_watermark": binding.get("source_high_watermark"),
        })
    except (PtmReadinessError, KeyError, ValueError, OSError) as exc:
        raise PtmReadinessGateError(f"PTM readiness revalidation failed for {commission_id or 'lifecycle record'}: {exc}") from exc


class PtmCapabilityDependencyResolver:
    """Production adapter exposing PTM resolutions to capability enablement."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def __call__(self, dependency_id: str) -> Mapping[str, Any] | None:
        dependency_path = self.root / "runtime/grace_helen_engineering/capability_enablement/dependencies" / f"{dependency_id}.json"
        if not dependency_path.exists():
            return None
        dependency = json.loads(dependency_path.read_text(encoding="utf-8"))
        canonical_id = dependency.get("canonical_ptm_dependency_id")
        if not canonical_id:
            return None
        matches = []
        readiness_dir = self.root / "runtime/ptm/readiness"
        for path in readiness_dir.glob("*.json") if readiness_dir.exists() else []:
            try:
                record = read_readiness(self.root, path.stem)
                binding = PtmReadinessBinding.from_record(record)
                revalidate_readiness(self.root, binding.to_dict())
            except (PtmReadinessError, OSError, ValueError):
                continue
            if record.get("source_high_watermark") == canonical_id or record.get("task_id") == canonical_id:
                matches.append(record)
        if not matches:
            return None
        record = max(matches, key=lambda item: item.get("evaluated_at", ""))
        state = record.get("readiness_state")
        return {
            "record_id": dependency_id,
            "original_objective_id": record.get("objective_id"),
            "enabling_project_id": dependency.get("enabling_project_id"),
            "status": "satisfied" if state in {"ready", "waived"} else state,
            "evidence_references": [record.get("projection_path")],
            "observed_at": record.get("evaluated_at"),
            "expires_at": record.get("expires_at"),
            "ptm_readiness": record,
        }
