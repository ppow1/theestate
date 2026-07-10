"""Extension contracts for Estate background operations.

Extensions are data-first declarations loaded from committed configuration.  The
contracts intentionally describe capabilities; they do not authorize provider,
dispatch, Traffic Controller, or institutional acceptance bypasses.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any, Protocol

from estate.core.background_operations import ALLOWED_CLASSIFICATIONS, BackgroundOperationWatch

ALLOWED_CAPABILITIES = {"watch_provider", "scheduled_job", "operational_target", "evidence_processor", "status_contributor", "lifecycle_hook", "office_summary"}
ALLOWED_STATES = {"enabled", "disabled", "quarantined"}
IDENTITY_RE = re.compile(r"^[a-z][a-z0-9_\-.]{2,63}$")
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+(?:[-+][A-Za-z0-9_.-]+)?$")
CANONICAL_BOUNDARIES = {
    "no_provider_execution": True,
    "no_dispatch_execution": True,
    "no_traffic_controller_bypass": True,
    "no_institutional_acceptance": True,
}


class WatchProvider(Protocol):
    def watches(self) -> list[BackgroundOperationWatch]: ...


class ScheduledJob(Protocol):
    def dry_run(self) -> dict[str, Any]: ...


class OperationalTargetAdapter(Protocol):
    def targets(self) -> list[dict[str, Any]]: ...


class EvidenceProcessor(Protocol):
    def process(self, evidence: dict[str, Any]) -> dict[str, Any]: ...


class StatusContributor(Protocol):
    def status(self) -> dict[str, Any]: ...


class LifecycleHook(Protocol):
    def on_enable(self, extension_id: str) -> dict[str, Any]: ...
    def on_disable(self, extension_id: str) -> dict[str, Any]: ...


@dataclass
class BackgroundOperationsExtension:
    extension_id: str
    name: str
    version: str
    enabled: bool
    classification: str
    capabilities: list[str]
    dependencies: list[str] = field(default_factory=list)
    watch_provider: dict[str, Any] | None = None
    scheduled_jobs: list[dict[str, Any]] = field(default_factory=list)
    operational_targets: list[dict[str, Any]] = field(default_factory=list)
    evidence_processors: list[dict[str, Any]] = field(default_factory=list)
    status_contributors: list[dict[str, Any]] = field(default_factory=list)
    lifecycle_hooks: list[dict[str, Any]] = field(default_factory=list)
    office_summary: dict[str, Any] = field(default_factory=dict)
    state: str | None = None
    quarantine_reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BackgroundOperationsExtension":
        values = {k: data.get(k) for k in cls.__dataclass_fields__}  # type: ignore[attr-defined]
        for key in ["dependencies", "scheduled_jobs", "operational_targets", "evidence_processors", "status_contributors", "lifecycle_hooks"]:
            if values.get(key) is None:
                values[key] = []
        for key in ["office_summary", "metadata"]:
            if values.get(key) is None:
                values[key] = {}
        ext = cls(**values)
        ext.validate()
        return ext

    def validate(self) -> None:
        if not isinstance(self.extension_id, str) or not IDENTITY_RE.match(self.extension_id):
            raise ValueError("extension_id must be a stable lowercase identity")
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("name is required")
        if not isinstance(self.version, str) or not VERSION_RE.match(self.version):
            raise ValueError("version must be semantic version text")
        if not isinstance(self.enabled, bool):
            raise ValueError("enabled must be boolean")
        if self.classification not in ALLOWED_CLASSIFICATIONS:
            raise ValueError(f"unknown classification '{self.classification}'")
        if not isinstance(self.capabilities, list) or not self.capabilities:
            raise ValueError("capabilities must be a non-empty list")
        unknown = sorted(set(self.capabilities) - ALLOWED_CAPABILITIES)
        if unknown:
            raise ValueError(f"unknown capabilities: {unknown}")
        if not isinstance(self.dependencies, list) or any(not isinstance(d, str) for d in self.dependencies):
            raise ValueError("dependencies must be a list of extension ids")
        state = self.state or ("enabled" if self.enabled else "disabled")
        if state not in ALLOWED_STATES:
            raise ValueError("state must be enabled, disabled, or quarantined")
        for key in ["scheduled_jobs", "operational_targets", "evidence_processors", "status_contributors", "lifecycle_hooks"]:
            if not isinstance(getattr(self, key), list):
                raise ValueError(f"{key} must be a list")
        if not isinstance(self.metadata, dict) or not isinstance(self.office_summary, dict):
            raise ValueError("metadata and office_summary must be objects")

    def effective_state(self) -> str:
        return self.state or ("enabled" if self.enabled else "disabled")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        payload = asdict(self)
        payload["state"] = self.effective_state()
        payload["canonical_boundaries"] = dict(CANONICAL_BOUNDARIES)
        return payload


def extension_from_watch_provider(*, extension_id: str, name: str, version: str, classification: str, watches: list[BackgroundOperationWatch], enabled: bool = True, office_summary: dict[str, Any] | None = None) -> BackgroundOperationsExtension:
    return BackgroundOperationsExtension.from_dict({
        "extension_id": extension_id, "name": name, "version": version, "enabled": enabled, "classification": classification,
        "capabilities": ["watch_provider", "office_summary"], "watch_provider": {"watches": [w.to_dict() for w in watches]}, "office_summary": office_summary or {},
    })
