"""Multi-repository operational target models.

This module extends the existing operational target concept without creating a
new orchestrator, event bus, or audit system.  A target describes where state
for one governed repository lives and which existing capabilities may observe
or validate it.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from estate.core.operational_targets import CAPABILITIES, utc_now_iso

WATCH_PROFILES = {"estate", "cue-mastery", "generic", "manual"}
MODES = {"enabled", "disabled", "observe_only"}


def _slug(value: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "-" for ch in value).strip("-") or "target"


@dataclass
class MultiRepositoryOperationalTarget:
    """Configuration for one governed repository under shared operations."""

    target_id: str
    display_name: str
    repository_url: str
    repository_path: str | None
    base_branch: str
    workspace_root: str
    evidence_root: str
    enabled_capabilities: list[str]
    watch_profile: str
    validation_binding: dict[str, Any]
    department_owner: str
    mode: str = "enabled"
    aliases: list[str] = field(default_factory=list)
    read_only_observation: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.target_id or not self.display_name:
            raise ValueError("target_id and display_name are required")
        if not self.repository_url:
            raise ValueError("repository_url is required")
        if not self.base_branch:
            raise ValueError("base_branch is required")
        if not self.workspace_root or not self.evidence_root:
            raise ValueError("workspace_root and evidence_root are required")
        if self.watch_profile not in WATCH_PROFILES:
            raise ValueError(f"unknown watch_profile '{self.watch_profile}'")
        if self.mode not in MODES:
            raise ValueError(f"unknown mode '{self.mode}'")
        unknown = [c for c in self.enabled_capabilities if c not in CAPABILITIES]
        if unknown:
            raise ValueError(f"unknown capabilities {unknown}")
        if self.mode == "observe_only":
            self.read_only_observation = True
        if self.aliases is None:
            self.aliases = []
        if self.validation_binding is None:
            self.validation_binding = {"kind": "none"}
        if self.metadata is None:
            self.metadata = {}

    @property
    def active(self) -> bool:
        return self.mode in {"enabled", "observe_only"}

    @property
    def audit_enabled(self) -> bool:
        return self.mode == "enabled" and "audit" in self.enabled_capabilities and not self.read_only_observation

    def scoped_path(self, root: Path, kind: str) -> Path:
        base = {"cursor": "runtime/merge_discovery/targets", "workspace": self.workspace_root, "evidence": self.evidence_root, "holds": "runtime/operational_targets/holds", "verdicts": "runtime/post_merge_audit/verdicts/by_target"}[kind]
        return Path(base) / self.target_id if Path(base).is_absolute() else root / base / self.target_id

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        data = asdict(self)
        data["active"] = self.active
        data["audit_enabled"] = self.audit_enabled
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MultiRepositoryOperationalTarget":
        allowed = {k for k in cls.__dataclass_fields__}
        obj = cls(**{k: data.get(k) for k in allowed})  # type: ignore[arg-type]
        obj.validate()
        return obj


def default_multi_repository_targets(root: str | Path) -> list[MultiRepositoryOperationalTarget]:
    root = Path(root)
    runtime = root / "runtime" / "multi_repository"
    return [
        MultiRepositoryOperationalTarget(
            target_id="estate-main", display_name="Estate Main", repository_url="https://github.com/ppow1/theestate.git", repository_path=str(root), base_branch="main",
            workspace_root=str(runtime / "workspaces" / "estate-main"), evidence_root=str(runtime / "evidence" / "estate-main"),
            enabled_capabilities=["git", "validation", "audit"], watch_profile="estate", validation_binding={"kind": "estate_work_package", "recipe_prefix": "WP-"}, department_owner="Estate", aliases=["estate", "theestate"], mode="enabled"),
        MultiRepositoryOperationalTarget(
            target_id="cue-mastery", display_name="Cue Mastery", repository_url="https://github.com/ppow1/cue-mastery.git", repository_path=None, base_branch="main",
            workspace_root=str(runtime / "workspaces" / "cue-mastery"), evidence_root=str(runtime / "evidence" / "cue-mastery"),
            enabled_capabilities=["git", "validation", "audit"], watch_profile="cue-mastery", validation_binding={"kind": "external", "recipe": None}, department_owner="Engineering", aliases=["cue", "cuemastery"], mode="observe_only", read_only_observation=True),
    ]


def target_record(target: MultiRepositoryOperationalTarget, *, state: str = "ready", error: str | None = None) -> dict[str, Any]:
    return {"target_id": target.target_id, "display_name": target.display_name, "department_owner": target.department_owner, "mode": target.mode, "read_only_observation": target.read_only_observation, "enabled_capabilities": list(target.enabled_capabilities), "watch_profile": target.watch_profile, "validation_binding": dict(target.validation_binding), "state": state, "error": error, "generated_at": utc_now_iso()}
