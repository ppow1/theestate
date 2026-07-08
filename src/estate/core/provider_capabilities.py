from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

DEFAULT_CAPABILITY_IDS = {
    "planning",
    "architecture_review",
    "governance_draft",
    "work_package_draft",
    "documentation_draft",
    "repository_implementation",
    "code_review",
    "test_execution",
    "audit_execution",
    "validation_receipt",
    "local_reasoning",
    "classification_review",
    "web_research",
    "connector_context_read",
}


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
class ProviderCapability:
    capability_id: str
    display_name: str
    category: str
    description: str | None = None
    input_artifacts: list[str] = field(default_factory=list)
    output_artifacts: list[str] = field(default_factory=list)
    requires_approval: bool = False
    requires_validation: bool = False
    supports_offline: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProviderCapability":
        if not isinstance(data, dict):
            raise ValueError("capability must be a JSON object")
        metadata = data.get("metadata") or {}
        if not isinstance(metadata, dict):
            raise ValueError("metadata must be an object")
        description = data.get("description")
        if description is not None and not isinstance(description, str):
            raise ValueError("description must be a string")
        capability = cls(
            capability_id=_require_str(data, "capability_id"),
            display_name=_require_str(data, "display_name"),
            category=_require_str(data, "category"),
            description=description,
            input_artifacts=_list_value(data, "input_artifacts"),
            output_artifacts=_list_value(data, "output_artifacts"),
            requires_approval=bool(data.get("requires_approval", False)),
            requires_validation=bool(data.get("requires_validation", False)),
            supports_offline=bool(data.get("supports_offline", False)),
            metadata=metadata,
        )
        capability.validate()
        return capability

    def validate(self) -> None:
        for key in ("capability_id", "display_name", "category"):
            if not isinstance(getattr(self, key), str) or not getattr(self, key).strip():
                raise ValueError(f"{key} is required")
        for key in ("input_artifacts", "output_artifacts"):
            value = getattr(self, key)
            if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
                raise ValueError(f"{key} must be a list of strings")
        if not isinstance(self.metadata, dict):
            raise ValueError("metadata must be an object")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
