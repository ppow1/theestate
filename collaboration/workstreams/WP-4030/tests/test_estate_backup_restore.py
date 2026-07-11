from pathlib import Path

import importlib.util
import sys


def load_module():
    path = Path(__file__).resolve().parents[1] / "src" / "estate_backup_restore.py"
    spec = importlib.util.spec_from_file_location("estate_backup_restore", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


mod = load_module()
BackupPlan = mod.BackupPlan
EstateBackupService = mod.EstateBackupService
ScopeEntry = mod.ScopeEntry


def write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def scope():
    return [
        ScopeEntry("residents", "resident_identity"),
        ScopeEntry("continuity", "continuity"),
        ScopeEntry("journals", "journal"),
        ScopeEntry("mail", "mail"),
        ScopeEntry("sessions", "session"),
        ScopeEntry("tasks", "task"),
        ScopeEntry("lifecycle", "lifecycle"),
        ScopeEntry("knowledge", "knowledge_metadata"),
        ScopeEntry("config", "configuration"),
        ScopeEntry("models", "configuration"),
        ScopeEntry("generated_outputs", "knowledge_metadata"),
    ]


def seed(root: Path) -> None:
    for rel in [
        "residents/ada.json", "continuity/ada.json", "journals/ada.md", "mail/inbox.json",
        "sessions/current.json", "tasks/queue.json", "lifecycle/state.json",
        "knowledge/index.json", "config/runtime.json",
    ]:
        write(root, rel, f"content:{rel}")
    write(root, "models/local.gguf", "model-bytes")
    write(root, "generated_outputs/transcript.txt", "generated")


def test_full_manifest_is_deterministic_source_linked_and_references_large_outputs(tmp_path):
    source = tmp_path / "source"
    backups = tmp_path / "backups"
    seed(source)
    service = EstateBackupService(source, backups)

    manifest_a = service.create_backup("full-a", BackupPlan("full", scope()))
    manifest_b = service.create_backup("full-b", BackupPlan("full", scope()))

    comparable_a = {k: v for k, v in manifest_a.items() if k != "backup_id"}
    comparable_b = {k: v for k, v in manifest_b.items() if k != "backup_id"}
    assert comparable_a == comparable_b
    assert manifest_a["source_root"] == str(source.resolve())
    assert set(manifest_a["coverage"]) == set(mod.COVERAGE_AREAS)
    assert {r["path"] for r in manifest_a["references"]} == {"generated_outputs/transcript.txt", "models/local.gguf"}
    assert not (backups / "full-a" / "data" / "models" / "local.gguf").exists()


def test_integrity_verification_detects_missing_and_corrupt_files(tmp_path):
    source = tmp_path / "source"
    backups = tmp_path / "backups"
    seed(source)
    service = EstateBackupService(source, backups)
    service.create_backup("full", BackupPlan("full", scope()))
    manifest_path = backups / "full" / "manifest.json"
    assert service.verify_backup(manifest_path)["ok"]

    (backups / "full" / "data" / "config" / "runtime.json").write_text("corrupt", encoding="utf-8")
    (backups / "full" / "data" / "mail" / "inbox.json").unlink()
    errors = {e["error"] for e in service.verify_backup(manifest_path)["errors"]}
    assert errors == {"checksum_mismatch", "missing"}


def test_selective_restore_dry_run_collision_and_approved_overwrite(tmp_path):
    source = tmp_path / "source"
    backups = tmp_path / "backups"
    restore = tmp_path / "restore"
    seed(source)
    service = EstateBackupService(source, backups)
    service.create_backup("full", BackupPlan("full", scope()))
    manifest_path = backups / "full" / "manifest.json"
    write(restore, "config/runtime.json", "active")

    dry = service.restore(manifest_path, restore, select=["config/runtime.json"], dry_run=True)
    assert dry["collisions"] and dry["partial_failure"]
    assert (restore / "config" / "runtime.json").read_text(encoding="utf-8") == "active"

    restored = service.restore(manifest_path, restore, select=["config/runtime.json"], dry_run=False, approve_overwrite=True)
    assert restored["ok"]
    assert (restore / "config" / "runtime.json").read_text(encoding="utf-8") == "content:config/runtime.json"
    assert not (restore / "mail" / "inbox.json").exists()


def test_incremental_plan_records_only_changes_and_unchanged_references(tmp_path):
    source = tmp_path / "source"
    backups = tmp_path / "backups"
    seed(source)
    service = EstateBackupService(source, backups)
    service.create_backup("base", BackupPlan("full", scope()))
    write(source, "tasks/queue.json", "changed")

    inc = service.create_backup("inc", BackupPlan("incremental", scope(), since_manifest=backups / "base" / "manifest.json"))
    assert [f["path"] for f in inc["files"]] == ["tasks/queue.json"]
    assert any(r["reason"] == "unchanged_since_base_manifest" for r in inc["references"])


def test_disaster_recovery_rehearsal_and_truthful_partial_failure(tmp_path):
    source = tmp_path / "source"
    backups = tmp_path / "backups"
    seed(source)
    service = EstateBackupService(source, backups)
    manifest = service.create_backup("full", BackupPlan("full", scope() + [ScopeEntry("missing", "configuration")]))
    assert manifest["partial_failure"]
    report = service.disaster_recovery_rehearsal(backups / "full" / "manifest.json", tmp_path / "drill")
    assert report["ok"]
