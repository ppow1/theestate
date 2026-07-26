"""Local-first Operations Center Settings Manager.

Centralizes Steward-facing UI preferences without creating cloud settings,
storing secrets, or changing operational authority.
"""

from __future__ import annotations

import json
import os
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from estate.core.operations_center_workspace_profiles import AVAILABLE_PANELS, DEFAULT_PROFILE, default_workspace_profiles
from estate.core.operator_activity_stream import DEFAULT_PROFILE_NAME as DEFAULT_VERBOSITY_PROFILE, load_operator_activity_profiles
from estate.core.paths import ESTATE_ROOT

SETTINGS_OUTPUT = "runtime/steward/operations_center_settings.json"
SETTINGS_SCHEMA_VERSION = 1
SETTINGS_UI_VERSION = "operations-center-settings-v1"
THEME_OPTIONS = ["light", "dark", "system"]
ACCENT_OPTIONS = ["estate-gold", "blue", "green", "neutral"]
DENSITY_OPTIONS = ["comfortable", "compact", "spacious"]
STARTUP_TAB_OPTIONS = ["home", "mission-control", "engineering-dashboard", "alfred", "helen", "resident-conversations", "ai-services-models", "daily-board", "operational-activity", "execution-control", "projects", "roadmap", "parking", "work-packages", "mailboxes", "recalls", "notifications", "validation", "search", "settings", "help", "about"]
REFRESH_MODES = ["quiet", "manual"]
COMMAND_CONSOLE_MODES = ["inline", "collapsed"]
DEFAULT_REFRESH_SECONDS = 30
MIN_REFRESH_SECONDS = 5
MAX_REFRESH_SECONDS = 3600


def _root(root: str | Path | None = None) -> Path:
    return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def default_operations_center_settings() -> dict[str, Any]:
    panels = {panel: True for panel in sorted(AVAILABLE_PANELS | {"help"})}
    return {
        "settings_schema_version": SETTINGS_SCHEMA_VERSION,
        "ui_version": SETTINGS_UI_VERSION,
        "updated_at": None,
        "appearance": {"theme": "system", "accent": "estate-gold", "layout_density": "comfortable"},
        "workspace": {
            "default_profile": DEFAULT_PROFILE,
            "default_active_tab": "mission-control",
            "visible_panels": panels,
            "navigation_order": STARTUP_TAB_OPTIONS.copy(),
            "status_bar_visible": True,
            "bottom_activity_stream_visible": True,
        },
        "operator_visibility": {"default_verbosity_profile": DEFAULT_VERBOSITY_PROFILE, "global_verbosity": "normal", "topic_overrides": {}, "resident_overrides": {}},
        "refresh": {"mode": "quiet", "enabled": True, "quiet_refresh_seconds": DEFAULT_REFRESH_SECONDS},
        "command_console": {"mode": "inline", "open_on_start": False, "show_unavailable_commands": True},
        "persistence": {"local_only": True, "stores_secrets": False, "path": SETTINGS_OUTPUT},
    }


def _read_store(path: Path) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    if not path.exists():
        return None, [{"type": "settings_file_missing", "message": "Settings file is missing; documented defaults are active.", "path": SETTINGS_OUTPUT}]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return None, [{"type": "settings_file_unreadable", "message": str(exc), "path": SETTINGS_OUTPUT}]
    if not isinstance(data, dict):
        return None, [{"type": "settings_file_invalid", "message": "Settings file must contain a JSON object.", "path": SETTINGS_OUTPUT}]
    if isinstance(data.get("settings"), dict):
        return data["settings"], []
    return data, []


def _merge_dict(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _merge_dict(result[key], value)
        else:
            result[key] = value
    return result


def _coerce_bool(settings: dict[str, Any], section: str, key: str, default: bool, warnings: list[dict[str, Any]]) -> None:
    value = settings.get(section, {}).get(key)
    if isinstance(value, bool):
        return
    settings[section][key] = default
    warnings.append({"type": "invalid_setting", "setting": f"{section}.{key}", "message": f"Invalid boolean; using default {default}."})


def _validate(settings: dict[str, Any], root: Path, warnings: list[dict[str, Any]]) -> dict[str, Any]:
    if settings.get("settings_schema_version") != SETTINGS_SCHEMA_VERSION:
        warnings.append({"type": "settings_version_mismatch", "setting": "settings_schema_version", "message": f"Unsupported version {settings.get('settings_schema_version')}; normalized to {SETTINGS_SCHEMA_VERSION}."})
        settings["settings_schema_version"] = SETTINGS_SCHEMA_VERSION
    settings["ui_version"] = SETTINGS_UI_VERSION

    appearance = settings.setdefault("appearance", {})
    if appearance.get("theme") not in THEME_OPTIONS:
        warnings.append({"type": "invalid_setting", "setting": "appearance.theme", "message": "Invalid theme; using system."})
        appearance["theme"] = "system"
    if appearance.get("accent") not in ACCENT_OPTIONS:
        warnings.append({"type": "invalid_setting", "setting": "appearance.accent", "message": "Invalid accent; using estate-gold."})
        appearance["accent"] = "estate-gold"
    if appearance.get("layout_density") not in DENSITY_OPTIONS:
        warnings.append({"type": "invalid_setting", "setting": "appearance.layout_density", "message": "Invalid layout density; using comfortable."})
        appearance["layout_density"] = "comfortable"

    workspace = settings.setdefault("workspace", {})
    available_profiles = default_workspace_profiles()
    if workspace.get("default_profile") not in available_profiles:
        warnings.append({"type": "invalid_setting", "setting": "workspace.default_profile", "message": "Unknown workspace profile; using mission-control."})
        workspace["default_profile"] = DEFAULT_PROFILE
    visible = workspace.get("visible_panels")
    if not isinstance(visible, dict):
        visible = {}
        warnings.append({"type": "invalid_setting", "setting": "workspace.visible_panels", "message": "Visible panels must be an object; defaults were restored."})
    valid_panels = sorted(AVAILABLE_PANELS | {"help"})
    workspace["visible_panels"] = {panel: bool(visible.get(panel, True)) for panel in valid_panels}
    # Settings must remain recoverable.
    workspace["visible_panels"]["settings"] = True
    order = workspace.get("navigation_order")
    if not isinstance(order, list) or len(order) != len(set(order)) or any(item not in STARTUP_TAB_OPTIONS for item in order):
        warnings.append({"type": "invalid_setting", "setting": "workspace.navigation_order", "message": "Navigation order must be a list of unique known tab IDs; defaults were restored."})
        order = STARTUP_TAB_OPTIONS.copy()
    workspace["navigation_order"] = [item for item in order if item in STARTUP_TAB_OPTIONS] + [item for item in STARTUP_TAB_OPTIONS if item not in order]
    if workspace.get("default_active_tab") not in STARTUP_TAB_OPTIONS or not workspace["visible_panels"].get(workspace.get("default_active_tab"), True):
        warnings.append({"type": "invalid_setting", "setting": "workspace.default_active_tab", "message": "Startup tab unavailable; using settings."})
        workspace["default_active_tab"] = "settings"
    _coerce_bool(settings, "workspace", "status_bar_visible", True, warnings)
    _coerce_bool(settings, "workspace", "bottom_activity_stream_visible", True, warnings)

    operator = settings.setdefault("operator_visibility", {})
    profiles = load_operator_activity_profiles(root)
    if operator.get("default_verbosity_profile") not in profiles:
        warnings.append({"type": "invalid_setting", "setting": "operator_visibility.default_verbosity_profile", "message": "Unknown verbosity profile; using default."})
        operator["default_verbosity_profile"] = DEFAULT_VERBOSITY_PROFILE
    levels = {"quiet", "normal", "detailed", "diagnostic"}
    if operator.get("global_verbosity") not in levels:
        warnings.append({"type": "invalid_setting", "setting": "operator_visibility.global_verbosity", "message": "Invalid verbosity; using normal."})
        operator["global_verbosity"] = "normal"
    for key in ("topic_overrides", "resident_overrides"):
        value = operator.get(key)
        if not isinstance(value, dict) or any(v not in levels for v in value.values()):
            warnings.append({"type": "invalid_setting", "setting": f"operator_visibility.{key}", "message": "Verbosity overrides must map names to allowed verbosity levels; invalid overrides removed."})
            operator[key] = {}

    refresh = settings.setdefault("refresh", {})
    _coerce_bool(settings, "refresh", "enabled", True, warnings)
    if refresh.get("mode") not in REFRESH_MODES:
        warnings.append({"type": "invalid_setting", "setting": "refresh.mode", "message": "Invalid refresh mode; using quiet."})
        refresh["mode"] = "quiet"
    seconds = refresh.get("quiet_refresh_seconds")
    if not isinstance(seconds, int) or seconds < MIN_REFRESH_SECONDS or seconds > MAX_REFRESH_SECONDS:
        warnings.append({"type": "invalid_setting", "setting": "refresh.quiet_refresh_seconds", "message": f"Invalid refresh interval; using {DEFAULT_REFRESH_SECONDS}."})
        refresh["quiet_refresh_seconds"] = DEFAULT_REFRESH_SECONDS

    console = settings.setdefault("command_console", {})
    if console.get("mode") not in COMMAND_CONSOLE_MODES:
        warnings.append({"type": "invalid_setting", "setting": "command_console.mode", "message": "Invalid command console mode; using inline."})
        console["mode"] = "inline"
    _coerce_bool(settings, "command_console", "open_on_start", False, warnings)
    _coerce_bool(settings, "command_console", "show_unavailable_commands", True, warnings)

    settings["persistence"] = {"local_only": True, "stores_secrets": False, "path": SETTINGS_OUTPUT}
    return settings


def load_operations_center_settings(root: str | Path | None = None) -> dict[str, Any]:
    root = _root(root)
    defaults = default_operations_center_settings()
    stored, warnings = _read_store(root / SETTINGS_OUTPUT)
    settings = _merge_dict(defaults, stored or {})
    settings = _validate(settings, root, warnings)
    return {"version": SETTINGS_SCHEMA_VERSION, "ui_version": SETTINGS_UI_VERSION, "path": SETTINGS_OUTPUT, "settings": settings, "defaults": defaults, "warnings": warnings, "effective_source": "stored_with_safe_defaults" if stored else "documented_defaults"}


def save_operations_center_settings(root: str | Path | None = None, **updates: Any) -> dict[str, Any]:
    root = _root(root)
    loaded = load_operations_center_settings(root)
    overlay: dict[str, Any] = {"updated_at": _now()}
    for dotted_key, value in updates.items():
        if value is None:
            continue
        cursor = overlay
        parts = dotted_key.split("__")
        for part in parts[:-1]:
            cursor = cursor.setdefault(part, {})
        cursor[parts[-1]] = value
    settings = _validate(_merge_dict(loaded["settings"], overlay), root, loaded["warnings"])
    path = root / SETTINGS_OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps({"version": SETTINGS_SCHEMA_VERSION, "settings": settings}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)
    return load_operations_center_settings(root)


def reset_operations_center_settings(root: str | Path | None = None) -> dict[str, Any]:
    root = _root(root)
    return save_settings_document(root, default_operations_center_settings(), backup=False)


def save_settings_document(root: str | Path | None, settings: dict[str, Any], *, backup: bool = True) -> dict[str, Any]:
    root = _root(root)
    warnings: list[dict[str, Any]] = []
    normalized = _validate(_merge_dict(default_operations_center_settings(), settings), root, warnings)
    normalized["updated_at"] = _now()
    path = root / SETTINGS_OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    backup_path = None
    if backup and path.exists():
        backup_path = path.with_suffix(path.suffix + f".{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.bak")
        backup_path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps({"version": SETTINGS_SCHEMA_VERSION, "settings": normalized}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)
    payload = load_operations_center_settings(root)
    payload["import_backup_path"] = str(backup_path.relative_to(root)).replace("\\", "/") if backup_path else None
    payload["import_warnings"] = warnings
    return payload


def export_operations_center_settings(root: str | Path | None = None) -> dict[str, Any]:
    payload = load_operations_center_settings(root)
    return {"version": SETTINGS_SCHEMA_VERSION, "exported_at": _now(), "settings": payload["settings"], "warnings": payload.get("warnings", [])}


def import_operations_center_settings(root: str | Path | None, document: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(document, dict):
        raise ValueError("Imported settings must be a JSON object.")
    unknown = {k for k in document if k not in {"version", "settings", "exported_at", "warnings"}}
    if unknown:
        raise ValueError(f"Unknown executable or unsafe top-level fields rejected: {sorted(unknown)}")
    settings = document.get("settings")
    if not isinstance(settings, dict):
        raise ValueError("Imported settings document must contain a settings object.")
    return save_settings_document(root, settings, backup=True)
