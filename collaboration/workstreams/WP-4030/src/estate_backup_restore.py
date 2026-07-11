"""Isolated estate backup/restore staging service for WP-4030.

The module intentionally has no repository integrations.  It creates deterministic,
source-linked backup manifests, verifies checksums, and restores into caller-provided
isolated roots with dry-run collision reporting and overwrite approval.
"""
from __future__ import annotations

import fnmatch
import hashlib
import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Iterable, List, Optional, Tuple

COVERAGE_AREAS = (
    "resident_identity",
    "continuity",
    "journal",
    "mail",
    "session",
    "task",
    "lifecycle",
    "knowledge_metadata",
    "configuration",
)
EXCLUDED_KINDS = {"secret", "cache", "protected", "external_unrestricted"}
MODEL_PATTERNS = ("*.gguf", "*.safetensors", "*.pt", "*.pth", "*.onnx", "*.bin")
GENERATED_PATTERNS = ("generated_outputs/**", "outputs/**", "*.tmp")


def _posix(path: Path | str) -> str:
    return Path(path).as_posix().lstrip("/")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


@dataclass(frozen=True)
class ScopeEntry:
    source: str
    area: str
    kind: str = "record"
    include: bool = True
    explicit_large_include: bool = False

    def validate(self) -> None:
        if self.area not in COVERAGE_AREAS:
            raise ValueError(f"unsupported coverage area: {self.area}")
        if self.kind in EXCLUDED_KINDS and self.include:
            raise ValueError(f"refusing unrestricted/protected scope: {self.source} ({self.kind})")
        if Path(self.source).is_absolute() or ".." in PurePosixPath(self.source).parts:
            raise ValueError(f"scope must be relative and contained: {self.source}")


@dataclass
class BackupPlan:
    plan_type: str
    scope: List[ScopeEntry]
    since_manifest: Optional[Path] = None
    retention: Dict[str, Any] = field(default_factory=lambda: {"policy": "keep_last_7", "minimum_full": 1})

    def validate(self) -> None:
        if self.plan_type not in {"full", "incremental"}:
            raise ValueError("plan_type must be full or incremental")
        if self.plan_type == "incremental" and not self.since_manifest:
            raise ValueError("incremental plans require a source manifest")
        for entry in self.scope:
            entry.validate()


class EstateBackupService:
    def __init__(self, source_root: Path, backup_root: Path):
        self.source_root = source_root.resolve()
        self.backup_root = backup_root.resolve()

    def create_backup(self, backup_id: str, plan: BackupPlan) -> Dict[str, Any]:
        plan.validate()
        files: List[Dict[str, Any]] = []
        references: List[Dict[str, Any]] = []
        failures: List[Dict[str, str]] = []
        previous = self._load_previous(plan.since_manifest)
        data_dir = self.backup_root / backup_id / "data"

        for entry in sorted(plan.scope, key=lambda e: (e.area, e.source)):
            src = (self.source_root / entry.source).resolve()
            if not str(src).startswith(str(self.source_root)):
                failures.append({"source": entry.source, "error": "outside_source_root"})
                continue
            candidates = [src] if src.is_file() else sorted(p for p in src.rglob("*") if p.is_file()) if src.exists() else []
            if not src.exists():
                failures.append({"source": entry.source, "error": "missing_source"})
            for file_path in candidates:
                rel = _posix(file_path.relative_to(self.source_root))
                kind = self._classify(rel, entry)
                digest = _sha256(file_path)
                size = file_path.stat().st_size
                record = {"area": entry.area, "path": rel, "sha256": digest, "size": size, "source": rel}
                if kind == "reference":
                    references.append({**record, "reason": "large_model_or_generated_output_excluded"})
                    continue
                if plan.plan_type == "incremental" and previous.get(rel) == digest:
                    references.append({**record, "reason": "unchanged_since_base_manifest"})
                    continue
                dest = data_dir / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file_path, dest)
                files.append(record)

        manifest = self._manifest(backup_id, plan, files, references, failures)
        _write_json(self.backup_root / backup_id / "manifest.json", manifest)
        return manifest

    def verify_backup(self, manifest_path: Path) -> Dict[str, Any]:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        root = manifest_path.parent / "data"
        errors = []
        for item in manifest["files"]:
            path = root / item["path"]
            if not path.exists():
                errors.append({"path": item["path"], "error": "missing"})
            elif _sha256(path) != item["sha256"]:
                errors.append({"path": item["path"], "error": "checksum_mismatch"})
        return {"ok": not errors, "checked": len(manifest["files"]), "errors": errors}

    def restore(self, manifest_path: Path, restore_root: Path, *, select: Optional[Iterable[str]] = None,
                dry_run: bool = True, approve_overwrite: bool = False) -> Dict[str, Any]:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        data_root = manifest_path.parent / "data"
        selected = sorted(select or [f["path"] for f in manifest["files"]])
        selected_set = set(selected)
        actions = []
        collisions = []
        failures = []
        for item in manifest["files"]:
            if item["path"] not in selected_set:
                continue
            src = data_root / item["path"]
            dest = (restore_root / item["path"]).resolve()
            if Path(item["path"]).is_absolute() or ".." in PurePosixPath(item["path"]).parts:
                failures.append({"path": item["path"], "error": "unsafe_restore_path"})
                continue
            if dest.exists() and not approve_overwrite:
                collisions.append({"path": item["path"], "action": "would_not_overwrite_without_approval"})
                continue
            actions.append({"path": item["path"], "action": "restore" if not dry_run else "would_restore"})
            if not dry_run:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)
        return {"dry_run": dry_run, "ok": not failures and not collisions, "actions": actions,
                "collisions": collisions, "failures": failures, "partial_failure": bool(failures or collisions)}

    def disaster_recovery_rehearsal(self, manifest_path: Path, rehearsal_root: Path) -> Dict[str, Any]:
        verify = self.verify_backup(manifest_path)
        restore = self.restore(manifest_path, rehearsal_root, dry_run=False, approve_overwrite=False)
        post = {"ok": False, "checked": 0, "errors": []}
        if restore["ok"]:
            post_service = EstateBackupService(rehearsal_root, rehearsal_root / ".unused")
            post = post_service._verify_restored_manifest(manifest_path)
        return {"ok": verify["ok"] and restore["ok"] and post["ok"], "verify": verify, "restore": restore, "post_restore": post}

    def _verify_restored_manifest(self, manifest_path: Path) -> Dict[str, Any]:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        errors = []
        for item in manifest["files"]:
            restored = self.source_root / item["path"]
            if not restored.exists() or _sha256(restored) != item["sha256"]:
                errors.append({"path": item["path"], "error": "restored_integrity_failed"})
        return {"ok": not errors, "checked": len(manifest["files"]), "errors": errors}

    def _load_previous(self, path: Optional[Path]) -> Dict[str, str]:
        if not path:
            return {}
        manifest = json.loads(path.read_text(encoding="utf-8"))
        return {item["path"]: item["sha256"] for item in manifest.get("files", [])}

    def _classify(self, rel: str, entry: ScopeEntry) -> str:
        if entry.explicit_large_include:
            return "file"
        if any(fnmatch.fnmatch(rel, pattern) for pattern in MODEL_PATTERNS + GENERATED_PATTERNS):
            return "reference"
        return "file"

    def _manifest(self, backup_id: str, plan: BackupPlan, files: List[Dict[str, Any]],
                  references: List[Dict[str, Any]], failures: List[Dict[str, str]]) -> Dict[str, Any]:
        return {
            "schema": "estate.backup.manifest.v1",
            "backup_id": backup_id,
            "plan_type": plan.plan_type,
            "source_root": str(self.source_root),
            "base_manifest": str(plan.since_manifest) if plan.since_manifest else None,
            "coverage": list(COVERAGE_AREAS),
            "retention": plan.retention,
            "files": sorted(files, key=lambda i: i["path"]),
            "references": sorted(references, key=lambda i: (i["path"], i["reason"])),
            "failures": sorted(failures, key=lambda i: (i.get("source", i.get("path", "")), i["error"])),
            "partial_failure": bool(failures),
        }
