"""Governed catalog of Background Operations watches.

Committed descriptors live in this module. Mutable enable/disable/pause and
configuration overrides are runtime state and are intentionally not committed.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from estate.core.background_operations import BackgroundOperationWatch, default_background_operation_watches

WATCH_CATEGORIES = {"repository", "validation", "runtime-health", "queue", "service", "artifact-freshness"}


@dataclass
class OperationalWatchDescriptor:
    watch_id: str
    name: str
    category: str
    target: str
    trigger: str
    cadence_seconds: int
    severity: str
    action_class: str
    dependencies: list[str]
    enabled_by_default: bool
    owner: str
    source_paths: list[str]
    conditions: dict[str, Any]
    classification: str = "Estate Internal"
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_background_watch(cls, watch: BackgroundOperationWatch, *, category: str, target: str, severity: str, owner: str, dependencies: list[str] | None = None) -> "OperationalWatchDescriptor":
        return cls(
            watch_id=watch.watch_id,
            name=watch.name,
            category=category,
            target=target,
            trigger=watch.trigger_type,
            cadence_seconds=watch.cooldown_seconds,
            severity=severity,
            action_class=watch.action_type,
            dependencies=dependencies or [],
            enabled_by_default=watch.enabled,
            owner=owner,
            source_paths=list(watch.source_paths),
            conditions=dict(watch.conditions),
            classification=watch.classification,
            metadata=dict(watch.metadata),
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OperationalWatchDescriptor":
        desc = cls(**{k: data.get(k) for k in cls.__dataclass_fields__})  # type: ignore[attr-defined]
        desc.validate()
        return desc

    def validate(self) -> None:
        if self.category not in WATCH_CATEGORIES:
            raise ValueError(f"unknown watch category '{self.category}'")
        for key in ["watch_id", "name", "target", "trigger", "severity", "action_class", "owner", "classification"]:
            if not isinstance(getattr(self, key), str) or not getattr(self, key).strip():
                raise ValueError(f"{key} is required")
        if int(self.cadence_seconds) < 0:
            raise ValueError("cadence_seconds must be non-negative")
        if not isinstance(self.enabled_by_default, bool):
            raise ValueError("enabled_by_default must be boolean")
        if not isinstance(self.dependencies, list) or not isinstance(self.source_paths, list):
            raise ValueError("dependencies and source_paths must be lists")
        if not isinstance(self.conditions, dict) or not isinstance(self.metadata, dict):
            raise ValueError("conditions and metadata must be objects")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)

    def to_background_watch(self, *, enabled: bool | None = None, cadence_seconds: int | None = None, conditions: dict[str, Any] | None = None, last_triggered_at: str | None = None) -> BackgroundOperationWatch:
        return BackgroundOperationWatch(
            watch_id=self.watch_id,
            name=self.name,
            enabled=self.enabled_by_default if enabled is None else enabled,
            trigger_type=self.trigger,
            source_paths=list(self.source_paths),
            conditions=dict(self.conditions if conditions is None else conditions),
            action_type=self.action_class,
            cooldown_seconds=self.cadence_seconds if cadence_seconds is None else cadence_seconds,
            classification=self.classification,
            last_triggered_at=last_triggered_at,
            metadata={**self.metadata, "catalog_category": self.category, "owner": self.owner, "target": self.target, "severity": self.severity},
        )


_CATEGORY_BY_KIND = {
    "pending_routing_recommendation": ("queue", "provider_routing", "medium", "Traffic Controller / Operations Manager"),
    "missing_ring2_review": ("validation", "validation_reviews", "high", "Validation"),
    "stale_validation_artifact": ("artifact-freshness", "validation_artifacts", "medium", "Validation"),
    "provider_capacity_warning": ("service", "provider_capacity", "high", "Operations"),
    "worker_assignment_gap": ("queue", "worker_assignments", "medium", "Operations"),
    "pending_movement_decision": ("queue", "traffic_controller_movement", "high", "Traffic Controller"),
    "operational_target_watch_needed": ("repository", "operational_targets", "high", "Validation"),
}


def default_operational_watch_descriptors() -> list[OperationalWatchDescriptor]:
    descriptors = []
    for watch in default_background_operation_watches():
        category, target, severity, owner = _CATEGORY_BY_KIND.get(watch.conditions.get("watch_kind"), ("runtime-health", "background_operations", "medium", "Operations"))
        descriptors.append(OperationalWatchDescriptor.from_background_watch(watch, category=category, target=target, severity=severity, owner=owner))
    descriptors.append(OperationalWatchDescriptor(
        watch_id="operations_runtime_health_watch",
        name="Operations runtime health",
        category="runtime-health",
        target="operations_runtime",
        trigger="artifact_status",
        cadence_seconds=3600,
        severity="medium",
        action_class="staff_update_request",
        dependencies=["runtime/operations/status/latest.json"],
        enabled_by_default=False,
        owner="Operations",
        source_paths=["runtime/operations/status/latest.json"],
        conditions={"watch_kind": "operations_runtime_health"},
    ))
    return descriptors


def descriptor_by_id(watch_id: str) -> OperationalWatchDescriptor:
    for desc in default_operational_watch_descriptors():
        if desc.watch_id == watch_id:
            return desc
    raise KeyError(watch_id)
