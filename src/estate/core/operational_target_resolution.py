"""Canonical operational target resolution."""
from __future__ import annotations
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from estate.core.operational_targets import OperationalTarget
from estate.core.operational_targets_runtime import OperationalTargetRuntime

METHODS = {"canonical_id","alias","repository_full_name","local_path","environment_name","not_found","ambiguous"}

def _norm(s: str) -> str:
    return str(s).strip().lower()

def _norm_path(s: str) -> str:
    try:
        return str(Path(s).expanduser().resolve()).replace("\\", "/").lower()
    except OSError:
        return str(Path(s).expanduser()).replace("\\", "/").lower()

@dataclass
class OperationalTargetResolutionResult:
    requested_identifier: str
    resolved: bool
    canonical_target_id: str | None
    resolution_method: str
    target: dict[str, Any] | None = None
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

class OperationalTargetResolver:
    def __init__(self, root=None):
        self.runtime = OperationalTargetRuntime(root)

    def resolve(self, identifier: str) -> OperationalTargetResolutionResult:
        requested = str(identifier or "").strip()
        targets = self.runtime.load_targets()
        exact = [t for t in targets if t.target_id == requested]
        if exact:
            return self._ok(requested, exact[0], "canonical_id")
        norm = _norm(requested)
        checks: list[tuple[str, list[OperationalTarget]]] = []
        checks.append(("alias", [t for t in targets if norm in {_norm(a) for a in getattr(t, "aliases", [])}]))
        checks.append(("repository_full_name", [t for t in targets if t.repository_full_name and _norm(t.repository_full_name) == norm]))
        checks.append(("local_path", [t for t in targets if t.local_path and _norm_path(t.local_path) == _norm_path(requested)]))
        checks.append(("environment_name", [t for t in targets if requested in getattr(t, "environment_names", [])]))
        matches: list[tuple[str, OperationalTarget]] = []
        for method, found in checks:
            matches.extend((method, t) for t in found)
        unique = {(t.target_id, method): (method, t) for method, t in matches}
        target_ids = {t.target_id for _, t in unique.values()}
        if len(target_ids) == 1:
            method, target = next(iter(unique.values()))
            return self._ok(requested, target, method)
        if len(target_ids) > 1:
            return OperationalTargetResolutionResult(requested, False, None, "ambiguous", errors=["ambiguous target identifier"], warnings=sorted(target_ids))
        return OperationalTargetResolutionResult(requested, False, None, "not_found", errors=[f"unknown target {requested}"])

    def _ok(self, requested: str, target: OperationalTarget, method: str) -> OperationalTargetResolutionResult:
        return OperationalTargetResolutionResult(requested, True, target.target_id, method, target.to_dict())
