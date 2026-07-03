import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from estate.core.paths import REGISTRY_DIR

DEFAULT_REGISTRY_PATH = REGISTRY_DIR / "interaction_adapters.json"
REQUIRED_FIELDS = {
    "adapter_id",
    "display_name",
    "adapter_type",
    "status",
    "local_first",
    "provider",
    "configuration_required",
    "secrets_required",
    "authority_boundary",
    "source_of_truth_boundary",
    "related_workspace",
    "notes",
}


class InteractionAdapterRegistryError(ValueError):
    """Raised when an interaction adapter registry is malformed."""


@dataclass(frozen=True)
class InteractionAdapter:
    adapter_id: str
    display_name: str
    adapter_type: str
    status: str
    local_first: bool
    provider: str
    configuration_required: bool
    secrets_required: bool
    authority_boundary: str
    source_of_truth_boundary: str
    related_workspace: str | None
    notes: str

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> "InteractionAdapter":
        missing = REQUIRED_FIELDS - set(payload)
        if missing:
            raise InteractionAdapterRegistryError(
                f"adapter entry missing required fields: {sorted(missing)}"
            )
        return cls(**{field: payload[field] for field in REQUIRED_FIELDS})


def load_interaction_adapter_registry(path: str | Path | None = None) -> dict[str, Any]:
    registry_path = Path(path) if path is not None else DEFAULT_REGISTRY_PATH
    if not registry_path.exists():
        return {
            "ok": False,
            "reason": "interaction_adapter_registry_missing",
            "path": str(registry_path),
            "adapters": [],
        }
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    adapters = [
        InteractionAdapter.from_mapping(entry) for entry in payload.get("adapters", [])
    ]
    adapter_ids = [adapter.adapter_id for adapter in adapters]
    duplicates = sorted(
        {adapter_id for adapter_id in adapter_ids if adapter_ids.count(adapter_id) > 1}
    )
    if duplicates:
        raise InteractionAdapterRegistryError(
            f"duplicate interaction adapter IDs: {duplicates}"
        )
    return {
        "ok": True,
        "path": str(registry_path),
        "version": payload.get("version"),
        "adapters": adapters,
    }


def adapters_by_type(
    adapter_type: str, path: str | Path | None = None
) -> list[InteractionAdapter]:
    registry = load_interaction_adapter_registry(path)
    if not registry["ok"]:
        return []
    return [
        adapter
        for adapter in registry["adapters"]
        if adapter.adapter_type == adapter_type
    ]


def get_interaction_adapter(
    adapter_id: str, path: str | Path | None = None
) -> InteractionAdapter | None:
    registry = load_interaction_adapter_registry(path)
    if not registry["ok"]:
        return None
    return next(
        (
            adapter
            for adapter in registry["adapters"]
            if adapter.adapter_id == adapter_id
        ),
        None,
    )
