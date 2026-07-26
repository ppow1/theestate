"""Read-only Office adapter for the staged engineering dashboard stack."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CONFIG_PATH = "config/engineering_campaign_dashboard.json"
CACHE_PATH = "runtime/steward/engineering_campaign_dashboard_last_valid.json"
AUDIT_PATH = "runtime/audit/engineering_campaign_dashboard.jsonl"
ALLOWED_ROLES = frozenset({"steward", "estate_operator"})


def _canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def _load_config(root: Path) -> dict[str, Any]:
    defaults = {"enabled": False, "provider_manifest": "collaboration/workstreams/WP-4222/fixtures/providers.json",
                "refresh_policy": "manual", "freshness_threshold_seconds": 86400,
                "last_known_valid": True, "diagnostic_verbosity": "safe", "access_roles": sorted(ALLOWED_ROLES)}
    path = root / CONFIG_PATH
    if not path.is_file():
        return defaults
    value = json.loads(path.read_text(encoding="utf-8"))
    return {**defaults, **value}


def _integration_module(root: Path):
    path = root / "collaboration/workstreams/WP-4222/dashboard_integration/integration.py"
    spec = importlib.util.spec_from_file_location("estate_wp4222_integration", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("WP-4222 integration provider unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _audit(root: Path, event: dict[str, Any]) -> None:
    path = root / AUDIT_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {"timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"), **event}
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")


def _safe_error(exc: Exception) -> str:
    text = str(exc).lower()
    if "incompatible" in text or "mismatch" in text:
        return "provider_incompatible"
    if "schema" in text or "invalid" in text or "malformed" in text:
        return "provider_snapshot_invalid"
    return "provider_unavailable"


def _operator_diagnostics(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Expose compatibility metadata without provider paths or content."""
    return [{key: value for key, value in row.items() if key != "detail"} | {"detail": "loaded read-only" if row.get("status") == "healthy" else row.get("code", "unavailable")}
            for row in rows]


def load_engineering_campaign_dashboard(root: str | Path, *, role: str = "estate_operator", refresh: bool = False,
                                        write: bool = False) -> dict[str, Any]:
    """Compose WP-4222 without scanning sources or granting mutation authority."""
    root = Path(root).resolve()
    config = _load_config(root)
    if role not in set(config["access_roles"]) or role not in ALLOWED_ROLES:
        if write:
            _audit(root, {"event": "access_denied", "role": role})
        return {"available": False, "state": "unauthorized", "read_only": True, "diagnostics": ["authorization_failed"]}
    if not config["enabled"]:
        return {"available": False, "state": "unsupported", "read_only": True, "diagnostics": ["dashboard_disabled"]}
    cache = root / CACHE_PATH
    try:
        module = _integration_module(root)
        registry = module.load_manifest(root / config["provider_manifest"])
        integration = module.compose_dashboard(registry)
        integration["provider_diagnostics"] = _operator_diagnostics(integration.get("provider_diagnostics", []))
        snapshot = integration["dashboard_snapshot"]
        generated = datetime.fromisoformat(snapshot["generation_time"].replace("Z", "+00:00"))
        age = max(0, int((datetime.now(timezone.utc) - generated).total_seconds()))
        freshness = "stale" if age > int(config["freshness_threshold_seconds"]) else snapshot["freshness_status"]
        response = {"available": True, "state": "stale" if freshness == "stale" else integration["health"],
                    "read_only": True, "advisory_only": True, "current": True, "last_known_valid": False,
                    "refresh_policy": config["refresh_policy"], "freshness_status": freshness,
                    "age_seconds": age, "integration": integration, "dashboard_snapshot": snapshot,
                    "provenance": {"source_queue_generation_id": snapshot["source_queue_generation_identifier"],
                        "source_revision": snapshot["source_revision"], "dashboard_snapshot_id": snapshot["snapshot_identifier"],
                        "schema_version": snapshot["snapshot_schema_version"], "generation_time": snapshot["generation_time"],
                        "content_hash": snapshot["deterministic_content_hash"], "references": snapshot["source_provenance"]}}
        response["response_content_hash"] = hashlib.sha256(_canonical(response)).hexdigest()
        if write and (refresh or not cache.is_file()):
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_bytes(_canonical(response))
            _audit(root, {"event": "refresh_succeeded" if refresh else "dashboard_access", "state": response["state"],
                          "snapshot_id": snapshot["snapshot_identifier"], "source_revision": snapshot["source_revision"]})
        return response
    except Exception as exc:
        diagnostic = _safe_error(exc)
        if write:
            _audit(root, {"event": "refresh_failed" if refresh else "dashboard_access_failed", "diagnostic": diagnostic})
        if config["last_known_valid"] and cache.is_file():
            try:
                prior = json.loads(cache.read_text(encoding="utf-8"))
                prior.update({"state": "unavailable", "current": False, "last_known_valid": True,
                              "diagnostics": ["current_source_unavailable", diagnostic]})
                return prior
            except (OSError, json.JSONDecodeError):
                pass
        return {"available": False, "state": "unavailable", "current": False, "last_known_valid": False,
                "read_only": True, "advisory_only": True, "diagnostics": ["no_valid_snapshot", diagnostic]}


def dashboard_operation(root: str | Path, operation: str, *, role: str, panel_id: str | None = None) -> dict[str, Any]:
    allowed = {"snapshot", "panel", "summary", "health", "compatibility", "diagnostics", "refresh"}
    if operation not in allowed:
        return {"ok": False, "state": "unsupported", "read_only": True}
    dashboard = load_engineering_campaign_dashboard(root, role=role, refresh=operation == "refresh", write=True)
    if dashboard.get("state") == "unauthorized":
        return dashboard
    snapshot = dashboard.get("dashboard_snapshot") or {}
    if operation == "panel":
        panel = (snapshot.get("panels") or {}).get(panel_id)
        return {"ok": panel is not None, "state": panel.get("state") if panel else "unsupported", "panel": panel,
                "provenance": dashboard.get("provenance"), "read_only": True}
    if operation == "summary":
        return {"ok": dashboard.get("available", False), "state": dashboard.get("state"),
                "operator_summary": snapshot.get("executive_summary"), "provenance": dashboard.get("provenance"), "read_only": True}
    if operation in {"health", "compatibility", "diagnostics"}:
        integration = dashboard.get("integration") or {}
        return {"ok": dashboard.get("available", False), "state": dashboard.get("state"),
                "freshness_status": dashboard.get("freshness_status"), "provider_diagnostics": integration.get("provider_diagnostics", []),
                "diagnostics": dashboard.get("diagnostics", []), "provenance": dashboard.get("provenance"), "read_only": True}
    return {"ok": dashboard.get("available", False), **dashboard}
