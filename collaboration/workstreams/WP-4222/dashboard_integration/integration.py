"""Deterministic integration of published providers with the WP-4221 projection."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

INTEGRATION_VERSION = "estate.engineering-dashboard-integration/v1"
MANIFEST_VERSION = "estate.engineering-dashboard-provider-manifest/v1"
SUPPORTED = {
    "wp4214_duration": "estate.work-package-duration/v1",
    "wp4215_parallel": "estate.parallel-worker-plan/v1",
    "wp4217_git": "estate.local-git-readiness/v1",
    "wp4220_queue": "estate.engineering-queue/v1",
    "wp4221_projection": "estate.engineering-campaign-dashboard/v1",
}
REQUIRED = ("wp4220_queue", "wp4221_projection")


class IntegrationError(ValueError):
    """A required staged provider cannot be safely composed."""


def _canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def _digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _contract_major(value: str) -> tuple[str, str] | None:
    if not isinstance(value, str) or "/v" not in value:
        return None
    name, version = value.rsplit("/v", 1)
    return (name, version.split(".", 1)[0]) if version.split(".", 1)[0].isdigit() else None


@dataclass(frozen=True)
class Provider:
    provider_id: str
    contract_version: str
    kind: str
    path: Path
    required: bool


class ProviderRegistry:
    """Registry whose discovery is manifest-only and therefore has no runtime side effects."""

    def __init__(self, manifest_path: Path, manifest: dict[str, Any]):
        self.manifest_path = manifest_path.resolve()
        self._providers: dict[str, Provider] = {}
        entries = manifest.get("providers")
        if manifest.get("manifest_schema_version") != MANIFEST_VERSION or not isinstance(entries, list):
            raise IntegrationError("invalid provider manifest schema")
        for entry in entries:
            provider_id = entry.get("provider_id")
            if provider_id in self._providers:
                raise IntegrationError(f"duplicate provider: {provider_id}")
            if not provider_id or not isinstance(entry.get("path"), str):
                raise IntegrationError("invalid provider registration")
            self._providers[provider_id] = Provider(
                provider_id, entry.get("contract_version", ""), entry.get("kind", "json"),
                (self.manifest_path.parent / entry["path"]).resolve(),
                bool(entry.get("required", provider_id in REQUIRED)),
            )

    def discover(self) -> tuple[Provider, ...]:
        return tuple(self._providers[key] for key in sorted(self._providers))

    def get(self, provider_id: str) -> Provider | None:
        return self._providers.get(provider_id)


def load_manifest(path: str | Path) -> ProviderRegistry:
    manifest_path = Path(path)
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise IntegrationError(f"cannot load provider manifest: {exc}") from exc
    return ProviderRegistry(manifest_path, manifest)


def _load_json(provider: Provider) -> tuple[Any, str]:
    try:
        raw = provider.path.read_bytes()
        return json.loads(raw), _digest_bytes(raw)
    except (OSError, json.JSONDecodeError) as exc:
        raise IntegrationError(f"provider {provider.provider_id} cannot be loaded: {exc}") from exc


def _load_projection(provider: Provider):
    if provider.kind != "python_module" or provider.path.name != "projection.py":
        raise IntegrationError("wp4221_projection must identify the staged projection.py module")
    spec = importlib.util.spec_from_file_location("wp4221_staged_projection", provider.path)
    if spec is None or spec.loader is None:
        raise IntegrationError("wp4221 projection module is not loadable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for name in ("build_snapshot", "validate_snapshot", "PANEL_NAMES", "SNAPSHOT_VERSION"):
        if not hasattr(module, name):
            raise IntegrationError(f"wp4221 projection missing {name}")
    return module


def _diagnostic(provider: Provider, status: str, code: str, detail: str) -> dict[str, Any]:
    return {"provider_id": provider.provider_id, "required": provider.required, "status": status,
            "code": code, "detail": detail, "contract_version": provider.contract_version}


def compose_dashboard(registry: ProviderRegistry) -> dict[str, Any]:
    """Load sources once, compose existing projection, and verify no source bytes changed."""
    diagnostics: list[dict[str, Any]] = []
    loaded: dict[str, Any] = {}
    source_hashes: dict[str, str] = {}
    projection = None
    for provider_id in sorted(set(SUPPORTED) | set(REQUIRED)):
        provider = registry.get(provider_id)
        if provider is None:
            required = provider_id in REQUIRED
            diagnostics.append({"provider_id": provider_id, "required": required,
                "status": "missing", "code": "provider_not_registered", "detail": "no registry entry",
                "contract_version": SUPPORTED[provider_id]})
            continue
        expected = SUPPORTED[provider_id]
        if _contract_major(provider.contract_version) != _contract_major(expected):
            diagnostics.append(_diagnostic(provider, "incompatible", "contract_major_mismatch", f"expected {expected}"))
            continue
        if not provider.path.is_file():
            diagnostics.append(_diagnostic(provider, "missing", "artifact_not_found", str(provider.path)))
            continue
        before = _digest_bytes(provider.path.read_bytes())
        try:
            if provider_id == "wp4221_projection":
                projection = _load_projection(provider)
                if projection.SNAPSHOT_VERSION != expected:
                    raise IntegrationError(f"projection advertises {projection.SNAPSHOT_VERSION}, expected {expected}")
                loaded[provider_id] = {"module": provider.path.name}
            else:
                value, raw_hash = _load_json(provider)
                advertised = value.get("queue_schema_version") or value.get("schema_version")
                if advertised != provider.contract_version:
                    raise IntegrationError(f"artifact advertises {advertised!r}, registry declares {provider.contract_version}")
                loaded[provider_id] = value
                source_hashes[provider_id] = raw_hash
            diagnostics.append(_diagnostic(provider, "healthy", "compatible", "loaded read-only"))
        except IntegrationError as exc:
            diagnostics.append(_diagnostic(provider, "degraded", "load_or_schema_failure", str(exc)))
        if _digest_bytes(provider.path.read_bytes()) != before:
            raise IntegrationError(f"read-only violation: provider changed while loading: {provider_id}")

    fatal = [d for d in diagnostics if d["required"] and d["status"] != "healthy"]
    if fatal:
        raise IntegrationError("required provider failure: " + "; ".join(f"{d['provider_id']}:{d['code']}" for d in fatal))
    queue = loaded["wp4220_queue"]
    try:
        snapshot = projection.build_snapshot(queue)
        projection.validate_snapshot(snapshot)
    except Exception as exc:
        raise IntegrationError(f"projection composition failed: {exc}") from exc
    panels = tuple(snapshot["panel_index"])
    if panels != tuple(projection.PANEL_NAMES) or set(panels) != set(snapshot["panels"]):
        raise IntegrationError("panel discovery does not match registered projection panels")
    optional_bad = [d for d in diagnostics if not d["required"] and d["status"] != "healthy"]
    logical = {
        "integration_schema_version": INTEGRATION_VERSION,
        "dashboard_snapshot": snapshot,
        "panel_registry": [{"panel_id": name, "panel_schema_version": snapshot["panels"][name]["panel_schema_version"]} for name in panels],
        "providers": [{"provider_id": p.provider_id, "contract_version": p.contract_version, "required": p.required} for p in registry.discover()],
        "provider_diagnostics": sorted(diagnostics, key=lambda d: d["provider_id"]),
        "health": "degraded" if optional_bad or snapshot["degradation_status"] != "none" else "healthy",
        "degradation_reasons": sorted({f"{d['provider_id']}:{d['code']}" for d in optional_bad}),
        "source_hashes": source_hashes,
        "read_only": True,
        "staging_only": True,
    }
    logical["deterministic_content_hash"] = _digest_bytes(_canonical(logical))
    return logical
