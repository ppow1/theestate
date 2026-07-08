from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from estate.core.paths import ESTATE_ROOT
from estate.core.provider_capabilities import ProviderCapability

ALLOWED_PROVIDER_TYPES = {"planning", "execution", "validation", "documentation", "research", "classification", "media", "infrastructure", "mixed"}
ALLOWED_IMPLEMENTATION_KINDS = {"chatgpt", "codex", "local_llm", "python", "powershell", "github_actions", "manual", "future", "stub", "other"}
ALLOWED_STATUSES = {"designed", "implemented", "operationally_validated", "institutionalized", "deprecated", "blocked"}
ALLOWED_CLASSIFICATION_CEILINGS = {"Public", "Estate Internal", "Restricted", "Steward Only", "Local Only"}
SECRET_MARKERS = ("token", "secret", "password", "credential", "api_key", "apikey", "private_key")
CATALOG_PATH = ESTATE_ROOT / "config" / "providers" / "catalog.json"
OFFICE_STATUS_PATH = ESTATE_ROOT / "runtime" / "providers" / "catalog_status.json"


def _require_str(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} is required")
    return value


def _list_value(data: dict[str, Any], key: str) -> list[str]:
    value = data.get(key) or []
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{key} must be a list of strings")
    return value


@dataclass(frozen=True)
class ProviderDescriptor:
    provider_id: str
    display_name: str
    provider_type: str
    implementation_kind: str
    status: str
    classification_ceiling: str
    capabilities: list[str]
    allowed_context_classes: list[str] = field(default_factory=list)
    requires_boundary_review: bool = False
    supports_events: bool = False
    supports_artifacts: bool = False
    supports_validation: bool = False
    supports_offline: bool = False
    requires_network: bool = False
    cost_model: str = "unknown"
    routing_notes: str | None = None
    limitations: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProviderDescriptor":
        if not isinstance(data, dict):
            raise ValueError("provider descriptor must be a JSON object")
        metadata = data.get("metadata") or {}
        if not isinstance(metadata, dict):
            raise ValueError("metadata must be an object")
        provider = cls(
            provider_id=_require_str(data, "provider_id"),
            display_name=_require_str(data, "display_name"),
            provider_type=_require_str(data, "provider_type"),
            implementation_kind=_require_str(data, "implementation_kind"),
            status=_require_str(data, "status"),
            classification_ceiling=_require_str(data, "classification_ceiling"),
            capabilities=_list_value(data, "capabilities"),
            allowed_context_classes=_list_value(data, "allowed_context_classes"),
            requires_boundary_review=bool(data.get("requires_boundary_review", False)),
            supports_events=bool(data.get("supports_events", False)),
            supports_artifacts=bool(data.get("supports_artifacts", False)),
            supports_validation=bool(data.get("supports_validation", False)),
            supports_offline=bool(data.get("supports_offline", False)),
            requires_network=bool(data.get("requires_network", False)),
            cost_model=data.get("cost_model") or "unknown",
            routing_notes=data.get("routing_notes"),
            limitations=_list_value(data, "limitations"),
            metadata=metadata,
        )
        provider.validate()
        return provider

    def validate(self) -> None:
        if self.provider_type not in ALLOWED_PROVIDER_TYPES:
            raise ValueError(f"unknown provider type '{self.provider_type}'")
        if self.implementation_kind not in ALLOWED_IMPLEMENTATION_KINDS:
            raise ValueError(f"unknown implementation kind '{self.implementation_kind}'")
        if self.status not in ALLOWED_STATUSES:
            raise ValueError(f"unknown status '{self.status}'")
        if self.classification_ceiling not in ALLOWED_CLASSIFICATION_CEILINGS:
            raise ValueError(f"unknown classification ceiling '{self.classification_ceiling}'")
        if not self.capabilities:
            raise ValueError("capabilities is required")
        self._reject_secrets()

    def _reject_secrets(self) -> None:
        payload = json.dumps(asdict(self), sort_keys=True).lower()
        for marker in SECRET_MARKERS:
            if marker in payload:
                raise ValueError(f"provider descriptor appears to contain secret marker '{marker}'")

    def to_dict(self, office_safe: bool = False) -> dict[str, Any]:
        data = asdict(self)
        if office_safe:
            data.pop("routing_notes", None)
            data.pop("limitations", None)
        return data


class ProviderCatalog:
    def __init__(self, providers: list[ProviderDescriptor], capabilities: list[ProviderCapability]) -> None:
        self.providers = providers
        self.capabilities = capabilities
        self._providers_by_id = {provider.provider_id: provider for provider in providers}
        self._capabilities_by_id = {capability.capability_id: capability for capability in capabilities}
        if len(self._providers_by_id) != len(providers):
            raise ValueError("catalog contains duplicate provider_id values")
        for provider in providers:
            missing = [capability for capability in provider.capabilities if capability not in self._capabilities_by_id]
            if missing:
                raise ValueError(f"provider '{provider.provider_id}' references unknown capabilities: {', '.join(missing)}")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProviderCatalog":
        if not isinstance(data, dict):
            raise ValueError("provider catalog must be a JSON object")
        providers = [ProviderDescriptor.from_dict(item) for item in data.get("providers", [])]
        capabilities = [ProviderCapability.from_dict(item) for item in data.get("capabilities", [])]
        if not providers:
            raise ValueError("catalog requires at least one provider")
        if not capabilities:
            raise ValueError("catalog requires at least one capability")
        return cls(providers, capabilities)

    def get_provider(self, provider_id: str) -> ProviderDescriptor:
        try:
            return self._providers_by_id[provider_id]
        except KeyError as exc:
            raise KeyError(f"provider '{provider_id}' is not registered") from exc

    def providers_by_type(self, provider_type: str) -> list[ProviderDescriptor]:
        if provider_type not in ALLOWED_PROVIDER_TYPES:
            raise ValueError(f"unknown provider type '{provider_type}'")
        return [provider for provider in self.providers if provider.provider_type == provider_type]

    def providers_with_capability(self, capability_id: str) -> list[ProviderDescriptor]:
        return [provider for provider in self.providers if capability_id in provider.capabilities]

    def status_export(self) -> dict[str, Any]:
        by_type = Counter(provider.provider_type for provider in self.providers)
        by_status = Counter(provider.status for provider in self.providers)
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "provider_count": len(self.providers),
            "providers_by_type": dict(sorted(by_type.items())),
            "providers_by_status": dict(sorted(by_status.items())),
            "available_capabilities": sorted(self._capabilities_by_id),
            "providers": [provider.to_dict(office_safe=True) for provider in sorted(self.providers, key=lambda item: item.provider_id)],
        }


def load_provider_catalog(path: Path | None = None) -> ProviderCatalog:
    catalog_path = path or CATALOG_PATH
    return ProviderCatalog.from_dict(json.loads(catalog_path.read_text(encoding="utf-8")))


def write_office_status(catalog: ProviderCatalog | None = None, path: Path | None = None) -> Path:
    catalog = catalog or load_provider_catalog()
    output_path = path or OFFICE_STATUS_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(catalog.status_export(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path


def format_provider_list(catalog: ProviderCatalog) -> str:
    lines = ["Provider ID | Type | Status | Capabilities"]
    for provider in sorted(catalog.providers, key=lambda item: item.provider_id):
        lines.append(f"{provider.provider_id} | {provider.provider_type} | {provider.status} | {', '.join(provider.capabilities)}")
    return "\n".join(lines)
