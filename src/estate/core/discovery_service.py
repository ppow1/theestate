import json

from estate.core.discovery import observe_ai_environment, generate_discovery_report
from estate.core.discovery_catalog import (
    load_discovery_catalog,
    sync_discovery_catalog_from_latest,
    format_discovery_catalog_report,
    summarize_discovery_catalog,
)
from estate.core.discovery_cycle import run_discovery_cycle, format_discovery_cycle_report
from estate.core.discovery_runtime import read_runtime_latest
from estate.core.provider_sync import sync_ollama_providers


class DiscoveryService:
    def latest_observation(self):
        return read_runtime_latest(default={}) or {}

    def report(self):
        return generate_discovery_report()

    def status(self):
        data = self.latest_observation()
        ollama = data.get("ollama", {}) or {}

        return {
            "exists": data.get("exists"),
            "changed_since_previous": data.get("changed_since_previous"),
            "ollama_running": ollama.get("running"),
            "ollama_models": len(ollama.get("models", []) or []),
            "tools": len(data.get("tool_items", []) or data.get("tools", []) or []),
            "tts": len(data.get("tts_items", []) or data.get("tts", []) or []),
            "python_envs": len(data.get("python_envs", []) or []),
        }

    def catalog(self, refresh=False):
        if refresh:
            return sync_discovery_catalog_from_latest()
        return load_discovery_catalog()

    def catalog_report(self, refresh=False):
        return format_discovery_catalog_report(self.catalog(refresh=refresh))

    def cycle(self):
        return run_discovery_cycle()

    def refresh(self):
        cycle = self.cycle()

        provider_result = {
            "ok": True,
            "detail": "provider sync skipped",
            "created": [],
            "ec_id": None,
        }

        try:
            sync_result = sync_ollama_providers()

            if isinstance(sync_result, dict):
                created = sync_result.get("created", [])
                ec_id = sync_result.get("ec_id") or sync_result.get("estate_change")
                detail = sync_result.get("detail") or f"{len(created)} provider records returned"
            elif isinstance(sync_result, tuple):
                values = list(sync_result)
                created = values
                ec_id = None
                detail = f"{len(values)} provider values returned"
            elif isinstance(sync_result, list):
                created = sync_result
                ec_id = None
                detail = f"{len(created)} provider records returned"
            else:
                created = []
                ec_id = None
                detail = f"provider sync returned {type(sync_result).__name__}"

            provider_result = {
                "ok": True,
                "detail": detail,
                "created": created,
                "ec_id": ec_id,
            }
        except Exception as exc:
            provider_result = {
                "ok": True,
                "detail": f"provider sync nonfatal: {exc}",
                "created": [],
                "ec_id": None,
            }


        observation = self.latest_observation()
        catalog = self.catalog(refresh=True)
        catalog_summary = summarize_discovery_catalog(catalog)

        return {
            "ok": bool(cycle.get("ok")) and provider_result["ok"],
            "cycle": cycle.get("metrics", {}),
            "provider_sync": provider_result,
            "status": self.status(),
            "catalog_summary": catalog_summary,
            "latest_observation_keys": sorted(observation.keys()),
        }

    def format_refresh_report(self, result):
        lines = [
            "=========================================",
            "Estate Discovery Refresh",
            "=========================================",
            f"OK: {result.get('ok')}",
            "",
            "Cycle:",
            f"  OK: {result.get('cycle', {}).get('ok')}",
            f"  Duration seconds: {result.get('cycle', {}).get('duration_seconds')}",
            f"  Consecutive successful runs: {result.get('cycle', {}).get('consecutive_successful_runs')}",
            "",
            "Provider Sync:",
            f"  OK: {result.get('provider_sync', {}).get('ok')}",
            f"  Detail: {result.get('provider_sync', {}).get('detail')}",
            "",
            "Catalog:",
            f"  Total: {result.get('catalog_summary', {}).get('total')}",
            f"  Active: {result.get('catalog_summary', {}).get('active')}",
            f"  Inactive: {result.get('catalog_summary', {}).get('inactive')}",
            "",
            "Status:",
        ]

        for key, value in result.get("status", {}).items():
            lines.append(f"  {key}: {value}")

        return "\n".join(lines)


_DISCOVERY_SERVICE = DiscoveryService()


def get_discovery_service():
    return _DISCOVERY_SERVICE
