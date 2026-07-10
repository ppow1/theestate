"""Shared multi-repository operational runtime.

The runtime coordinates target state for existing discovery, cleanroom/audit,
scheduler, and Office surfaces.  It deliberately writes scoped artifacts and
continues processing when one target fails.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from estate.core.multi_repository_targets import MultiRepositoryOperationalTarget, default_multi_repository_targets, target_record
from estate.core.operational_targets import utc_now_iso
from estate.core.paths import ESTATE_ROOT

BASE = Path("runtime/multi_repository")
REGISTRY = BASE / "targets.json"
STATUS = BASE / "status" / "latest.json"


def _root(root: Path | None = None) -> Path:
    return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


def _write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


class MultiRepositoryOperationalRuntime:
    """File-backed controller for multiple governed repositories."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = _root(root)

    @property
    def registry_path(self) -> Path:
        return self.root / REGISTRY

    def ensure_registry(self) -> None:
        if not self.registry_path.exists():
            self.write_targets(default_multi_repository_targets(self.root))

    def load_targets(self) -> list[MultiRepositoryOperationalTarget]:
        self.ensure_registry()
        return [MultiRepositoryOperationalTarget.from_dict(item) for item in (_read(self.registry_path).get("targets") or [])]

    def write_targets(self, targets: list[MultiRepositoryOperationalTarget]) -> None:
        _write(self.registry_path, {"schema_version": "multi_repository_operational_targets.v1", "updated_at": utc_now_iso(), "targets": [t.to_dict() for t in targets]})

    def get(self, target_id: str) -> MultiRepositoryOperationalTarget:
        for target in self.load_targets():
            if target.target_id == target_id or target_id in target.aliases:
                return target
        raise ValueError(f"unknown multi-repository target {target_id}")

    def set_mode(self, target_id: str, mode: str) -> dict[str, Any]:
        targets = self.load_targets(); changed = None
        for target in targets:
            if target.target_id == target_id:
                target.mode = mode
                target.read_only_observation = mode == "observe_only"
                target.validate()
                changed = target
        if changed is None:
            raise ValueError(f"unknown multi-repository target {target_id}")
        self.write_targets(targets)
        self.write_status()
        return changed.to_dict()

    def isolated_paths(self, target_id: str) -> dict[str, str]:
        target = self.get(target_id)
        return {kind: str(target.scoped_path(self.root, kind)) for kind in ("cursor", "workspace", "evidence", "holds", "verdicts")}

    def run_cycle(self, handler: Callable[[MultiRepositoryOperationalTarget], dict[str, Any]]) -> dict[str, Any]:
        results = []
        for target in self.load_targets():
            if not target.active:
                results.append(target_record(target, state="disabled"))
                continue
            try:
                result = handler(target)
                results.append({**target_record(target, state=result.get("state", "observed")), "result": result})
            except Exception as exc:  # isolate target failure, do not stop siblings
                results.append(target_record(target, state="failed", error=str(exc)))
        payload = {"schema_version": "multi_repository_cycle.v1", "generated_at": utc_now_iso(), "results": results, "summary": {"target_count": len(results), "failed_count": sum(1 for r in results if r["state"] == "failed"), "active_count": sum(1 for r in results if r["state"] != "disabled")}}
        _write(self.root / BASE / "cycles" / "latest.json", payload)
        self.write_status(extra={"last_cycle": payload})
        return payload

    def office_status(self) -> dict[str, Any]:
        targets = self.load_targets()
        grouped: dict[str, list[dict[str, Any]]] = {}
        for target in targets:
            grouped.setdefault(target.department_owner, []).append({**target.to_dict(), "isolated_paths": self.isolated_paths(target.target_id)})
        return {"schema_version": "multi_repository_office_status.v1", "generated_at": utc_now_iso(), "repositories_by_department": grouped, "summary": {"repository_count": len(targets), "department_count": len(grouped), "observe_only_count": sum(1 for t in targets if t.mode == "observe_only")}}

    def write_status(self, *, extra: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = self.office_status()
        if extra:
            payload.update(extra)
        _write(self.root / STATUS, payload)
        return payload
