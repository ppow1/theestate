"""Runtime helpers for clean-room audit workspaces."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from estate.core.audit_workspace_service import AuditWorkspaceConfig, AuditWorkspaceService


def _safe_path(value: Any, root: Path) -> Path:
    p = Path(value)
    if os.name != "nt" and not p.is_absolute():
        return root / p
    return p

def config_from_target(target: Any, root: Path, *, workspace_root: Path | None = None, evidence_root: Path | None = None, retain_failed_workspaces: bool = True) -> AuditWorkspaceConfig:
    active = Path(getattr(target, "local_path", None) or root)
    tid = getattr(target, "target_id", "target")
    ws = workspace_root or _safe_path(getattr(target, "workspace_root", None) or (root / "runtime/post_merge_audit/workspaces" / tid), root)
    ev = evidence_root or _safe_path(getattr(target, "validation_root", None) or (root / "runtime/post_merge_audit/evidence"), root)
    meta = getattr(target, "metadata", {}) or {}
    return AuditWorkspaceConfig(active, ws, ev, getattr(target, "base_branch", "main"), meta.get("remote", "origin"), bool(meta.get("fetch_enabled", True)), retain_failed_workspaces)


def prepare_audit_workspace(target: Any, root: Path, audit_id: str, revision: str | None, **kwargs: Any):
    return AuditWorkspaceService(config_from_target(target, root, **kwargs)).prepare(audit_id, revision)
