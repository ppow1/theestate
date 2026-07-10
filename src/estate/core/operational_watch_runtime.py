"""Runtime controls for the governed Operational Watch catalog."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from estate.core.background_operations import utc_now_iso
from estate.core.background_operations_runtime import BackgroundOperationsRuntime, _write_json
from estate.core.operational_events import OperationalEvent, append_event_artifact
from estate.core.operational_watch_catalog import OperationalWatchDescriptor, default_operational_watch_descriptors, descriptor_by_id
from estate.core.paths import ESTATE_ROOT

STATE_PATH = Path("runtime/background_operations/watch_state.json")


def _root(root: Path | None = None) -> Path:
    return root or (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


class OperationalWatchRuntime:
    def __init__(self, root: Path | None = None) -> None:
        self.root = _root(root)
        self.background = BackgroundOperationsRuntime(self.root)

    @property
    def state_path(self) -> Path:
        return self.root / STATE_PATH

    def descriptors(self) -> list[OperationalWatchDescriptor]:
        return default_operational_watch_descriptors()

    def load_state(self) -> dict[str, Any]:
        if not self.state_path.exists():
            return {"schema_version": "operational_watch_state.v1", "watches": {}}
        return json.loads(self.state_path.read_text(encoding="utf-8"))

    def write_state(self, state: dict[str, Any]) -> None:
        state["schema_version"] = "operational_watch_state.v1"
        state["updated_at"] = utc_now_iso()
        _write_json(self.state_path, state)
        self._sync_background_watches(state)

    def _watch_state(self, watch_id: str) -> dict[str, Any]:
        state = self.load_state()
        return state.setdefault("watches", {}).setdefault(watch_id, {})

    def _effective(self, desc: OperationalWatchDescriptor, state: dict[str, Any]) -> dict[str, Any]:
        ws = (state.get("watches") or {}).get(desc.watch_id, {})
        overrides = ws.get("overrides") or {}
        enabled = bool(ws.get("enabled", desc.enabled_by_default)) and not ws.get("paused", False)
        cadence = int(overrides.get("cadence_seconds", desc.cadence_seconds))
        conditions = {**desc.conditions, **(overrides.get("conditions") or {})}
        return {**desc.to_dict(), "enabled": enabled, "paused": bool(ws.get("paused", False)), "runtime_state": ws, "effective_cadence_seconds": cadence, "effective_conditions": conditions}

    def list(self) -> dict[str, Any]:
        state = self.load_state()
        watches = [self._effective(d, state) for d in self.descriptors()]
        return {"schema_version": "operational_watch_catalog.v1", "generated_at": utc_now_iso(), "watches": watches, "summary": {"total_watches": len(watches), "enabled_watches": sum(1 for w in watches if w["enabled"]), "paused_watches": sum(1 for w in watches if w["paused"])}}

    def show(self, watch_id: str) -> dict[str, Any]:
        desc = descriptor_by_id(watch_id)
        return self._effective(desc, self.load_state())

    def set_enabled(self, watch_id: str, enabled: bool) -> dict[str, Any]:
        descriptor_by_id(watch_id)
        state = self.load_state(); ws = state.setdefault("watches", {}).setdefault(watch_id, {})
        ws["enabled"] = enabled; ws["paused"] = False; ws["updated_at"] = utc_now_iso()
        self.write_state(state); self._emit("watch.enabled" if enabled else "watch.disabled", watch_id)
        return self.show(watch_id)

    def pause(self, watch_id: str) -> dict[str, Any]:
        descriptor_by_id(watch_id)
        state = self.load_state(); ws = state.setdefault("watches", {}).setdefault(watch_id, {})
        ws["paused"] = True; ws["updated_at"] = utc_now_iso()
        self.write_state(state); self._emit("watch.paused", watch_id)
        return self.show(watch_id)

    def override(self, watch_id: str, overrides: dict[str, Any]) -> dict[str, Any]:
        descriptor_by_id(watch_id)
        state = self.load_state(); ws = state.setdefault("watches", {}).setdefault(watch_id, {})
        ws.setdefault("overrides", {}).update(overrides); ws["updated_at"] = utc_now_iso()
        self.write_state(state); self._emit("watch.overridden", watch_id)
        return self.show(watch_id)

    def evaluate(self, watch_id: str, *, dry_run: bool = True) -> dict[str, Any]:
        effective = self.show(watch_id)
        if not effective["enabled"]:
            return {"watch_id": watch_id, "dry_run": dry_run, "enabled": False, "would_trigger": False, "reason": "disabled_or_paused"}
        watch = descriptor_by_id(watch_id).to_background_watch(enabled=True, cadence_seconds=effective["effective_cadence_seconds"], conditions=effective["effective_conditions"])
        trigger = self.background._evaluate_watch(watch)  # bounded extension of existing Background Operations behavior
        return {"watch_id": watch_id, "dry_run": dry_run, "enabled": True, "would_trigger": bool(trigger), "trigger": trigger, "provider_execution_performed": False, "institutional_acceptance_performed": False}

    def _sync_background_watches(self, state: dict[str, Any]) -> None:
        watches = []
        for desc in self.descriptors():
            eff = self._effective(desc, state)
            watches.append(desc.to_background_watch(enabled=eff["enabled"], cadence_seconds=eff["effective_cadence_seconds"], conditions=eff["effective_conditions"], last_triggered_at=(eff["runtime_state"] or {}).get("last_triggered_at")))
        self.background.write_watches(watches)

    def _emit(self, event_type: str, watch_id: str) -> None:
        try:
            event = OperationalEvent.create(event_type="Checkpoint Reached", state="Waiting", classification="Estate Internal", message=f"Operational watch {event_type}: {watch_id}", requires_attention=False, artifact_paths=[str(STATE_PATH)], metadata={"operational_watch_event": event_type, "watch_id": watch_id})
            append_event_artifact(event, root=self.root)
        except Exception:
            pass
