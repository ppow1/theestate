import subprocess
from pathlib import Path

from estate.core.audit_workspace_service import AuditWorkspaceConfig, AuditWorkspaceService


def git(cwd: Path, *args: str):
    return subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True, check=True)


def repo(path: Path):
    path.mkdir()
    git(path, "init", "-b", "main")
    git(path, "config", "user.email", "test@example.com")
    git(path, "config", "user.name", "Test")
    (path / "tracked.txt").write_text("one", encoding="utf-8")
    git(path, "add", ".")
    git(path, "commit", "-m", "init")
    return git(path, "rev-parse", "HEAD").stdout.strip()


def test_dirty_active_checkout_does_not_block_no_stash_and_cleanup(tmp_path):
    active = tmp_path / "active"; rev = repo(active)
    before = (active / "tracked.txt").read_text(encoding="utf-8")
    (active / "local.txt").write_text("dirty", encoding="utf-8")
    service = AuditWorkspaceService(AuditWorkspaceConfig(active, tmp_path / "workspaces", tmp_path / "external", fetch_enabled=False, retain_failed_workspaces=False))
    rec = service.prepare("audit-1", rev)
    assert rec.state == "synchronized"
    assert rec.active_checkout_dirty is True
    assert rec.revision_reachable is True
    assert Path(rec.workspace_path).exists()
    assert git(Path(rec.workspace_path), "rev-parse", "HEAD").stdout.strip() == rev
    assert git(active, "stash", "list").stdout.strip() == ""
    assert (active / "tracked.txt").read_text(encoding="utf-8") == before
    assert (active / "local.txt").read_text(encoding="utf-8") == "dirty"
    cleaned = service.cleanup(rec, success=True)
    assert cleaned.cleanup_status == "removed"
    assert not Path(rec.workspace_path).exists()
    assert (tmp_path / "external/reports/audit-1/workspace_sync.json").exists()


def test_failed_workspace_retention_is_configurable(tmp_path):
    active = tmp_path / "active"; rev = repo(active)
    keep = AuditWorkspaceService(AuditWorkspaceConfig(active, tmp_path / "keep", tmp_path / "external", fetch_enabled=False, retain_failed_workspaces=True))
    rec = keep.prepare("audit-2", rev)
    kept = keep.cleanup(rec, success=False)
    assert kept.cleanup_status == "retained_for_diagnosis"
    assert Path(kept.workspace_path).exists()
    drop = AuditWorkspaceService(AuditWorkspaceConfig(active, tmp_path / "drop", tmp_path / "external", fetch_enabled=False, retain_failed_workspaces=False))
    rec2 = drop.prepare("audit-3", rev)
    removed = drop.cleanup(rec2, success=False)
    assert removed.cleanup_status == "removed"
    assert not Path(removed.workspace_path).exists()
