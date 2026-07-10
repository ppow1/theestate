"""Committed-configuration runtime for background operations extensions."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from estate.core.background_operations import BackgroundOperationWatch, default_background_operation_watches, utc_now_iso
from estate.core.background_operations_extensions import BackgroundOperationsExtension, CANONICAL_BOUNDARIES
from estate.core.operational_targets import default_targets
from estate.core.paths import ESTATE_ROOT

BASE = Path("runtime/background_operations/extensions")
CONFIG = Path("config/background_operations/extensions.json")
STATUS = BASE / "status.json"
STATE = BASE / "state.json"


def _root(root: Path | None = None) -> Path:
    return root or (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


def _read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


class BackgroundOperationsExtensionRuntime:
    def __init__(self, root: Path | None = None) -> None:
        self.root = _root(root)

    @property
    def config_path(self) -> Path: return self.root / CONFIG
    @property
    def state_path(self) -> Path: return self.root / STATE
    @property
    def status_path(self) -> Path: return self.root / STATUS

    def ensure_config(self) -> None:
        if self.config_path.exists(): return
        watches = default_background_operation_watches()
        estate = {
            "extension_id": "estate_builtin_monitoring", "name": "Estate built-in monitoring", "version": "1.0.0", "enabled": True,
            "classification": "Estate Internal", "capabilities": ["watch_provider", "operational_target", "evidence_processor", "status_contributor", "office_summary", "lifecycle_hook"],
            "watch_provider": {"watches": [w.to_dict() for w in watches]},
            "operational_targets": [t.to_dict() for t in default_targets(str(self.root))],
            "evidence_processors": [{"processor_id": "post_merge_audit_processor", "canonical_handler": "estate.core.post_merge_audit_runtime.PostMergeAuditRuntime"}],
            "status_contributors": [{"contributor_id": "background_operations_status", "canonical_handler": "estate.core.background_operations_runtime.load_background_operations_status"}],
            "lifecycle_hooks": [{"hook_id": "state_only", "behavior": "persist enabled/disabled/quarantined state only"}],
            "office_summary": {"label": "Estate monitoring", "surface": "operational-activity"},
        }
        cue = {
            "extension_id": "cue_mastery_monitoring", "name": "Cue Mastery monitoring", "version": "1.0.0", "enabled": True,
            "classification": "Estate Internal", "capabilities": ["watch_provider", "status_contributor", "office_summary"],
            "dependencies": ["estate_builtin_monitoring"],
            "watch_provider": {"watches": [{"watch_id": "cue_mastery_briefing_watch", "name": "Cue Mastery briefing watch", "enabled": True, "trigger_type": "artifact_status", "source_paths": ["runtime/cue_mastery/status/summary.json"], "conditions": {"watch_kind": "cue_mastery_status"}, "action_type": "staff_update_request", "cooldown_seconds": 3600, "classification": "Estate Internal", "last_triggered_at": None, "metadata": {"extension_id": "cue_mastery_monitoring"}}]},
            "status_contributors": [{"contributor_id": "cue_mastery_status", "canonical_handler": "artifact_status_only"}],
            "office_summary": {"label": "Cue Mastery monitoring", "surface": "operational-activity"},
        }
        _write(self.config_path, {"schema_version": 1, "extensions": [estate, cue], "canonical_boundaries": CANONICAL_BOUNDARIES})

    def _state_overrides(self) -> dict[str, Any]:
        return _read(self.state_path).get("extensions", {}) if self.state_path.exists() else {}

    def load_extensions(self) -> list[BackgroundOperationsExtension]:
        self.ensure_config(); data = _read(self.config_path); overrides = self._state_overrides(); out = []
        for raw in data.get("extensions", []):
            item = dict(raw); oid = item.get("extension_id")
            if oid in overrides:
                item.update({k: v for k, v in overrides[oid].items() if k in {"enabled", "state", "quarantine_reason"}})
            out.append(BackgroundOperationsExtension.from_dict(item))
        return out

    def validate(self, *, write: bool = True) -> dict[str, Any]:
        self.ensure_config(); raw = _read(self.config_path); seen = set(); valid=[]; invalid=[]
        for item in raw.get("extensions", []):
            try:
                ext = BackgroundOperationsExtension.from_dict(item)
                if ext.extension_id in seen: raise ValueError("duplicate extension_id")
                seen.add(ext.extension_id); valid.append(ext.to_dict())
            except Exception as exc:
                bad = dict(item); bad["state"] = "quarantined"; bad["quarantine_reason"] = str(exc); invalid.append(bad)
        missing=[]
        for ext in valid:
            for dep in ext.get("dependencies", []):
                if dep not in seen: missing.append({"extension_id": ext["extension_id"], "missing_dependency": dep})
        payload={"generated_at": utc_now_iso(), "valid": not invalid and not missing, "valid_extensions": valid, "quarantined_extensions": invalid, "missing_dependencies": missing, "canonical_boundaries": CANONICAL_BOUNDARIES}
        if write: _write(self.status_path, payload)
        return payload

    def inspect(self) -> dict[str, Any]:
        validation = self.validate(write=False)
        extensions = []
        for ext in self.load_extensions():
            d = ext.to_dict(); d["office_visible"] = True; extensions.append(d)
        payload={"generated_at": utc_now_iso(), "extensions": extensions, "validation": validation, "summary": {"extension_count": len(extensions), "enabled_count": sum(1 for e in extensions if e["state"] == "enabled"), "quarantined_count": len(validation["quarantined_extensions"]) + len(validation["missing_dependencies"]), "office_control_surface": "operations_surface.extension_control"}, "canonical_boundaries": CANONICAL_BOUNDARIES}
        _write(self.status_path, payload); return payload

    def set_enabled(self, extension_id: str, enabled: bool) -> dict[str, Any]:
        exts = {e.extension_id: e for e in self.load_extensions()}
        if extension_id not in exts: raise ValueError(f"unknown extension {extension_id}")
        state = self._state_overrides(); state[extension_id] = {"enabled": enabled, "state": "enabled" if enabled else "disabled", "updated_at": utc_now_iso()}
        _write(self.state_path, {"extensions": state, "updated_at": utc_now_iso()})
        return self.inspect()

    def enable(self, extension_id: str) -> dict[str, Any]: return self.set_enabled(extension_id, True)
    def disable(self, extension_id: str) -> dict[str, Any]: return self.set_enabled(extension_id, False)

    def dry_run(self) -> dict[str, Any]:
        report = self.inspect(); watches=[]; failures=[]
        for ext in self.load_extensions():
            if ext.effective_state() != "enabled": continue
            try:
                for raw in (ext.watch_provider or {}).get("watches", []):
                    w = BackgroundOperationWatch.from_dict(raw).to_dict(); w["extension_id"] = ext.extension_id; watches.append(w)
            except Exception as exc:
                failures.append({"extension_id": ext.extension_id, "state": "quarantined", "reason": str(exc)})
        report["dry_run"] = True; report["would_register_watches"] = watches; report["extension_failures"] = failures; report["provider_execution_performed"] = False; report["dispatch_execution_performed"] = False
        _write(self.status_path, report); return report

    def extension_watches(self) -> tuple[list[BackgroundOperationWatch], list[dict[str, Any]]]:
        watches=[]; failures=[]
        for ext in self.load_extensions():
            if ext.effective_state() != "enabled": continue
            try:
                for raw in (ext.watch_provider or {}).get("watches", []): watches.append(BackgroundOperationWatch.from_dict(raw))
            except Exception as exc:
                failures.append({"extension_id": ext.extension_id, "state": "quarantined", "reason": str(exc)})
        return watches, failures
