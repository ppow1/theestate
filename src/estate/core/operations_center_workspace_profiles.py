"""Operations Center workspace profile persistence and resolution."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from estate.core.operator_activity_stream import load_operator_activity_profiles
from estate.core.paths import ESTATE_ROOT

PROFILES_OUTPUT = "runtime/steward/operations_center_workspace_profiles.json"
LAYOUT_VERSION = "layout-framework-v1"
PROFILE_VERSION = 1
DEFAULT_PROFILE = "mission-control"
AVAILABLE_PANELS = {
    "home", "mission-control", "validation", "roadmap", "projects", "work-packages",
    "mailboxes", "recalls", "daily-board", "parking", "search", "settings", "about",
    "alfred", "helen", "resident-conversations",
}


def _root(root: str | Path | None = None) -> Path:
    return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _profile(name: str, label: str, active_tab: str, tab_order: list[str], *, visible_panels: list[str] | None = None, activity_visible: bool = True, operator_profile: str = "default", verbosity: str = "normal") -> dict[str, Any]:
    visible = set(visible_panels or tab_order)
    return {
        "name": name,
        "label": label,
        "version": PROFILE_VERSION,
        "layout_version": LAYOUT_VERSION,
        "active_tab": active_tab,
        "tab_order": tab_order,
        "visible_panels": {panel: panel in visible for panel in sorted(AVAILABLE_PANELS)},
        "panel_arrangements": {"left_navigation": "expanded", "activity_console_dock": "bottom", "activity_console_visible": activity_visible},
        "operator_activity": {"profile": operator_profile, "verbosity": verbosity},
        "compatibility": {"minimum_layout_version": LAYOUT_VERSION, "unavailable_panel_behavior": "skip_and_report"},
        "updated_at": _now(),
    }


def default_workspace_profiles() -> dict[str, dict[str, Any]]:
    return {
        "mission-control": _profile("mission-control", "Mission Control", "mission-control", ["home", "mission-control", "projects", "validation", "mailboxes", "recalls", "search", "settings"], operator_profile="default"),
        "validation": _profile("validation", "Validation", "validation", ["validation", "work-packages", "projects", "search", "settings"], visible_panels=["validation", "work-packages", "projects", "search", "settings"], operator_profile="default", verbosity="detailed"),
        "expansion-planning": _profile("expansion-planning", "Expansion Planning", "roadmap", ["roadmap", "parking", "daily-board", "projects", "search", "settings"], operator_profile="default"),
        "active-projects": _profile("active-projects", "Active Projects", "projects", ["projects", "work-packages", "daily-board", "validation", "search", "settings"], operator_profile="default", verbosity="detailed"),
        "administration": _profile("administration", "Administration", "settings", ["settings", "mailboxes", "about", "search"], visible_panels=["settings", "mailboxes", "about", "search"], activity_visible=False, operator_profile="default"),
    }


def load_workspace_profiles(root: str | Path | None = None) -> dict[str, Any]:
    root = _root(root)
    profiles = default_workspace_profiles()
    warnings: list[dict[str, Any]] = []
    path = root / PROFILES_OUTPUT
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            stored = data.get("profiles", {}) if isinstance(data, dict) else {}
            if isinstance(stored, dict):
                profiles.update({k: v for k, v in stored.items() if isinstance(v, dict)})
        except Exception as exc:  # corrupt local profile store should not break dashboard
            warnings.append({"type": "profile_store_unreadable", "message": str(exc), "path": PROFILES_OUTPUT})
    return {"version": PROFILE_VERSION, "profiles": profiles, "warnings": warnings, "path": PROFILES_OUTPUT}


def resolve_workspace_profile(root: str | Path | None = None, *, profile_name: str = DEFAULT_PROFILE, available_panels: set[str] | None = None) -> dict[str, Any]:
    loaded = load_workspace_profiles(root)
    profiles = loaded["profiles"]
    selected = profiles.get(profile_name) or profiles[DEFAULT_PROFILE]
    available = available_panels or AVAILABLE_PANELS
    missing = [panel for panel in selected.get("tab_order", []) if panel not in available]
    restored_order = [panel for panel in selected.get("tab_order", []) if panel in available]
    active = selected.get("active_tab") if selected.get("active_tab") in available else (restored_order[0] if restored_order else "home")
    operator_profiles = load_operator_activity_profiles(root)
    op = selected.get("operator_activity") or {}
    op_name = op.get("profile", "default") if op.get("profile", "default") in operator_profiles else "default"
    warnings = list(loaded.get("warnings", []))
    warnings.extend({"type": "unavailable_panel", "panel": panel, "message": "Configured panel is unavailable and was skipped."} for panel in missing)
    return {
        "selected_profile": selected.get("name", profile_name),
        "profile": {**selected, "active_tab": active, "tab_order": restored_order, "operator_activity": {**op, "profile": op_name}},
        "available_profiles": sorted(profiles),
        "profile_store": PROFILES_OUTPUT,
        "warnings": warnings,
        "compatibility": {"layout_version": LAYOUT_VERSION, "profile_version": PROFILE_VERSION, "compatible": selected.get("layout_version") == LAYOUT_VERSION},
    }


def save_workspace_profile(root: str | Path | None = None, *, name: str, base_profile: str = DEFAULT_PROFILE, active_tab: str | None = None) -> dict[str, Any]:
    root = _root(root)
    loaded = load_workspace_profiles(root)
    profiles = loaded["profiles"]
    profile = dict(profiles.get(base_profile) or profiles[DEFAULT_PROFILE])
    profile["name"] = name
    profile["label"] = name.replace("-", " ").title()
    if active_tab:
        profile["active_tab"] = active_tab
        if active_tab not in profile.get("tab_order", []):
            profile["tab_order"] = [active_tab, *profile.get("tab_order", [])]
    profile["updated_at"] = _now()
    profiles[name] = profile
    path = root / PROFILES_OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"version": PROFILE_VERSION, "layout_version": LAYOUT_VERSION, "profiles": profiles}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return resolve_workspace_profile(root, profile_name=name)
