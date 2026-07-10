"""Disposable clean-room workspaces for post-merge audits."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from datetime import datetime, timezone

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

WORKSPACE_STATES = {"requested","preparing","synchronized","validating","ring2_pending","completed","blocked","failed","cleaning","archived"}


def _git(path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=path, text=True, capture_output=True, check=False)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


@dataclass
class AuditWorkspaceConfig:
    active_checkout_path: Path
    workspace_root: Path
    evidence_root: Path
    base_branch: str = "main"
    remote: str = "origin"
    fetch_enabled: bool = True
    retain_failed_workspaces: bool = True
    workspace_method: str = "git_worktree"


@dataclass
class AuditWorkspaceRecord:
    audit_id: str
    state: str
    workspace_path: str
    active_checkout_path: str
    remote_ref: str | None
    resolved_commit: str | None
    base_branch: str
    fetch_performed: bool
    workspace_method: str
    cleanup_status: str = "not_started"
    active_checkout_dirty: bool = False
    isolated_workspace_dirty: bool = False
    branch_sync_status: str = "unknown"
    revision_reachable: bool = False
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class AuditWorkspaceService:
    def __init__(self, config: AuditWorkspaceConfig) -> None:
        self.config = config

    def prepare(self, audit_id: str, requested_revision: str | None) -> AuditWorkspaceRecord:
        workspace = self.config.workspace_root / audit_id
        rec = AuditWorkspaceRecord(
            audit_id=audit_id,
            state="requested",
            workspace_path=str(workspace),
            active_checkout_path=str(self.config.active_checkout_path),
            remote_ref=f"{self.config.remote}/{self.config.base_branch}",
            resolved_commit=None,
            base_branch=self.config.base_branch,
            fetch_performed=False,
            workspace_method=self.config.workspace_method,
        )
        source = self.config.active_checkout_path
        try:
            rec.state = "preparing"
            status = _git(source, "status", "--porcelain")
            if status.returncode == 0 and status.stdout.strip():
                rec.active_checkout_dirty = True
                rec.warnings.append("active_checkout_dirty_reported_not_blocking")
                rec.warnings.append("active_tree_dirty_reported_not_repaired")
            elif status.returncode != 0:
                rec.errors.append("active_checkout_not_git_worktree")
                rec.state = "blocked"
                return rec

            if self.config.fetch_enabled:
                fetch = _git(source, "fetch", "--quiet", self.config.remote)
                rec.fetch_performed = True
                if fetch.returncode != 0:
                    rec.warnings.append("fetch_failed:" + (fetch.stderr.strip() or fetch.stdout.strip()))

            remote_ref = f"{self.config.remote}/{self.config.base_branch}"
            remote = _git(source, "rev-parse", "--verify", remote_ref)
            rec.branch_sync_status = "remote_ref_resolved" if remote.returncode == 0 else "remote_ref_unavailable"

            revision = requested_revision or remote_ref
            resolved = _git(source, "rev-parse", "--verify", f"{revision}^{{commit}}")
            if resolved.returncode != 0:
                rec.errors.append("requested_revision_unresolvable")
                rec.state = "blocked"
                return rec
            commit = resolved.stdout.strip()
            rec.resolved_commit = commit
            base = remote_ref if remote.returncode == 0 else self.config.base_branch
            reachable = _git(source, "merge-base", "--is-ancestor", commit, base)
            rec.revision_reachable = reachable.returncode == 0
            if not rec.revision_reachable:
                rec.errors.append("requested_revision_not_reachable_from_base")
                rec.state = "blocked"
                return rec

            if workspace.exists():
                self._remove_workspace(workspace)
            workspace.parent.mkdir(parents=True, exist_ok=True)
            add = _git(source, "worktree", "add", "--detach", str(workspace), commit)
            if add.returncode != 0:
                rec.errors.append("worktree_add_failed:" + (add.stderr.strip() or add.stdout.strip()))
                rec.state = "failed"
                return rec
            iso_status = _git(workspace, "status", "--porcelain")
            rec.isolated_workspace_dirty = bool(iso_status.stdout.strip()) if iso_status.returncode == 0 else True
            rec.state = "synchronized"
            self._write_sync_evidence(rec)
            return rec
        except Exception as exc:
            rec.errors.append(str(exc)); rec.state = "failed"; return rec

    def cleanup(self, rec: AuditWorkspaceRecord, *, success: bool) -> AuditWorkspaceRecord:
        rec.state = "cleaning"
        path = Path(rec.workspace_path)
        if (not success) and self.config.retain_failed_workspaces:
            rec.cleanup_status = "retained_for_diagnosis"; rec.state = "archived"; return rec
        try:
            self._remove_workspace(path)
            rec.cleanup_status = "removed"; rec.state = "completed" if success else "failed"
        except Exception as exc:
            rec.cleanup_status = "cleanup_failed"; rec.errors.append(str(exc)); rec.state = "failed"
        return rec

    def _remove_workspace(self, path: Path) -> None:
        if not path.exists():
            return
        rm = _git(self.config.active_checkout_path, "worktree", "remove", "--force", str(path))
        if rm.returncode != 0 and path.exists():
            shutil.rmtree(path)

    def _write_sync_evidence(self, rec: AuditWorkspaceRecord) -> None:
        _write_json(self.config.evidence_root / "reports" / rec.audit_id / "workspace_sync.json", {**rec.to_dict(), "recorded_at": utc_now_iso()})
