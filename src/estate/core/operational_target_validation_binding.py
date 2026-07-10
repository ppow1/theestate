"""Validation binding checks for operational targets."""
from __future__ import annotations
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from estate.core.operational_target_resolution import OperationalTargetResolver

REQUIRED_CAPABILITIES = {"git", "validation", "audit"}
BLOCKING_STATES = {"paused", "disabled", "retired", "blocked", "import_candidate"}

@dataclass
class OperationalTargetValidationBindingResult:
    ready: bool
    canonical_target_id: str | None
    repository_full_name: str | None = None
    source_path: str | None = None
    base_branch: str | None = None
    workspace_root: str | None = None
    validation_root: str | None = None
    missing_requirements: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    resolution: dict[str, Any] | None = None
    def to_dict(self) -> dict[str, Any]: return asdict(self)

class OperationalTargetValidationBinder:
    def __init__(self, root=None): self.resolver = OperationalTargetResolver(root)
    def bind(self, identifier: str) -> OperationalTargetValidationBindingResult:
        res = self.resolver.resolve(identifier)
        if not res.resolved or not res.target:
            return OperationalTargetValidationBindingResult(False, None, missing_requirements=[res.resolution_method], warnings=res.errors, resolution=res.to_dict())
        t = res.target; missing: list[str] = []
        if t.get("watch_state") in BLOCKING_STATES: missing.append(f"state:{t.get('watch_state')}")
        caps = set(t.get("capabilities") or [])
        for cap in sorted(REQUIRED_CAPABILITIES - caps): missing.append(f"capability:{cap}")
        source = t.get("local_path") or t.get("workspace_root")
        if not source: missing.append("local_path_or_workspace_source")
        if not t.get("base_branch"): missing.append("base_branch")
        if not t.get("workspace_root"): missing.append("workspace_root")
        if not t.get("validation_root"): missing.append("validation_root")
        return OperationalTargetValidationBindingResult(not missing, t.get("target_id"), t.get("repository_full_name"), source, t.get("base_branch"), t.get("workspace_root"), t.get("validation_root"), missing, [], res.to_dict())
