from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

SCHEMA = "estate.office_workspace_personalization.v1"
PINNABLE_KINDS = {"project", "work_package", "resident", "artifact"}
DEFAULT_QUICK_ACTIONS = ("open_daily_board", "new_work_package", "search_office")
DEFAULT_LAYOUT = "default"


@dataclass(frozen=True)
class WorkspaceDefaults:
    workspace_id: str
    layout_id: str = DEFAULT_LAYOUT
    visible_sections: tuple[str, ...] = ("overview", "projects", "work_packages", "residents", "artifacts", "actions")
    section_order: tuple[str, ...] = ("overview", "projects", "work_packages", "residents", "artifacts", "actions")
    quick_actions: tuple[str, ...] = DEFAULT_QUICK_ACTIONS
    preferences: Mapping[str, Any] = field(default_factory=lambda: {"density": "comfortable", "theme": "system"})


def _unique(items: Iterable[str]) -> list[str]:
    result: list[str] = []
    for item in items:
        if isinstance(item, str) and item and item not in result:
            result.append(item)
    return result


def _default_state(defaults: WorkspaceDefaults) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "staged_not_installed": True,
        "workspace_id": defaults.workspace_id,
        "active_layout_id": defaults.layout_id,
        "saved_layouts": {
            defaults.layout_id: {
                "layout_id": defaults.layout_id,
                "visible_sections": list(defaults.visible_sections),
                "section_order": list(defaults.section_order),
                "preferences": copy.deepcopy(dict(defaults.preferences)),
            }
        },
        "pins": {kind: [] for kind in sorted(PINNABLE_KINDS)},
        "favorite_residents": [],
        "quick_actions": list(defaults.quick_actions),
        "recovered_from_malformed_state": False,
        "recovery_notes": [],
    }


def restore_defaults(defaults: WorkspaceDefaults) -> dict[str, Any]:
    return _default_state(defaults)


def recover_state(raw_state: Mapping[str, Any] | None, defaults: WorkspaceDefaults) -> dict[str, Any]:
    state = _default_state(defaults)
    notes: list[str] = []
    if not isinstance(raw_state, Mapping):
        state["recovered_from_malformed_state"] = True
        state["recovery_notes"] = ["state was missing or not an object; restored defaults"]
        return state

    if raw_state.get("schema") != SCHEMA:
        notes.append("schema missing or unsupported")
    state["workspace_id"] = raw_state.get("workspace_id") if isinstance(raw_state.get("workspace_id"), str) else defaults.workspace_id

    saved_layouts = raw_state.get("saved_layouts")
    if isinstance(saved_layouts, Mapping):
        clean_layouts: dict[str, dict[str, Any]] = {}
        for layout_id, layout in saved_layouts.items():
            if not isinstance(layout_id, str) or not isinstance(layout, Mapping):
                notes.append("ignored malformed layout")
                continue
            clean_layouts[layout_id] = {
                "layout_id": layout_id,
                "visible_sections": _unique(layout.get("visible_sections", defaults.visible_sections)),
                "section_order": _unique(layout.get("section_order", defaults.section_order)),
                "preferences": copy.deepcopy(layout.get("preferences")) if isinstance(layout.get("preferences"), Mapping) else {},
            }
        if clean_layouts:
            state["saved_layouts"] = clean_layouts
    else:
        notes.append("saved_layouts malformed; defaults retained")

    active_layout_id = raw_state.get("active_layout_id")
    if isinstance(active_layout_id, str) and active_layout_id in state["saved_layouts"]:
        state["active_layout_id"] = active_layout_id
    elif active_layout_id is not None:
        notes.append("active_layout_id missing from saved_layouts; default selected")

    pins = raw_state.get("pins")
    if isinstance(pins, Mapping):
        state["pins"] = {kind: _unique(pins.get(kind, [])) for kind in sorted(PINNABLE_KINDS)}
    else:
        notes.append("pins malformed; defaults retained")

    state["favorite_residents"] = _unique(raw_state.get("favorite_residents", []))
    state["quick_actions"] = _unique(raw_state.get("quick_actions", defaults.quick_actions)) or list(defaults.quick_actions)
    state["recovered_from_malformed_state"] = bool(notes)
    state["recovery_notes"] = notes
    return state


def save_layout(state: Mapping[str, Any], layout_id: str, *, visible_sections: Iterable[str], section_order: Iterable[str], preferences: Mapping[str, Any] | None = None) -> dict[str, Any]:
    new_state = copy.deepcopy(dict(state))
    new_state.setdefault("saved_layouts", {})[layout_id] = {
        "layout_id": layout_id,
        "visible_sections": _unique(visible_sections),
        "section_order": _unique(section_order),
        "preferences": copy.deepcopy(dict(preferences or {})),
    }
    new_state["active_layout_id"] = layout_id
    return new_state


def set_section_order(state: Mapping[str, Any], layout_id: str, section_order: Iterable[str]) -> dict[str, Any]:
    new_state = copy.deepcopy(dict(state))
    if layout_id not in new_state.get("saved_layouts", {}):
        raise KeyError(f"unknown layout_id: {layout_id}")
    new_state["saved_layouts"][layout_id]["section_order"] = _unique(section_order)
    return new_state


def pin_item(state: Mapping[str, Any], kind: str, item_id: str) -> dict[str, Any]:
    if kind not in PINNABLE_KINDS:
        raise ValueError(f"unsupported pin kind: {kind}")
    new_state = copy.deepcopy(dict(state))
    pins = new_state.setdefault("pins", {k: [] for k in sorted(PINNABLE_KINDS)})
    pins.setdefault(kind, [])
    if item_id not in pins[kind]:
        pins[kind].append(item_id)
    return new_state


def unpin_item(state: Mapping[str, Any], kind: str, item_id: str) -> dict[str, Any]:
    new_state = copy.deepcopy(dict(state))
    new_state.setdefault("pins", {}).setdefault(kind, [])
    new_state["pins"][kind] = [item for item in new_state["pins"][kind] if item != item_id]
    return new_state


def set_favorite_residents(state: Mapping[str, Any], resident_ids: Iterable[str]) -> dict[str, Any]:
    new_state = copy.deepcopy(dict(state))
    new_state["favorite_residents"] = _unique(resident_ids)
    return new_state


def set_quick_actions(state: Mapping[str, Any], action_ids: Iterable[str]) -> dict[str, Any]:
    new_state = copy.deepcopy(dict(state))
    new_state["quick_actions"] = _unique(action_ids)
    return new_state


def export_state(state: Mapping[str, Any]) -> str:
    safe = copy.deepcopy(dict(state))
    safe["schema"] = SCHEMA
    safe["staged_not_installed"] = True
    return json.dumps(safe, sort_keys=True, separators=(",", ":"))


def import_state(payload: str, defaults: WorkspaceDefaults) -> dict[str, Any]:
    try:
        parsed = json.loads(payload)
    except json.JSONDecodeError:
        return recover_state(None, defaults)
    return recover_state(parsed, defaults)
