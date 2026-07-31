"""Canonical Draft 2020-12 validation for governed authority records."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource


SCHEMA_FILES = (
    "engineering/commission_execution_authority_v1.schema.json",
    "engineering/commission_ptm_evidence_v1.schema.json",
    "engineering/engineering_authorization_v1.schema.json",
    "dispatch/execution_metadata_v1.schema.json",
    "execution_provider_adapter_request_v1.schema.json",
    "operations_control/operations_decision_v1.schema.json",
    "providers/qwen_local_text_execution_extension_v1.schema.json",
    "providers/provider_receipt_v1.schema.json",
)


def schema_root(root: str | Path | None = None) -> Path:
    if root is not None:
        candidate = Path(root) / "schemas"
        if (candidate / SCHEMA_FILES[0]).exists():
            return candidate
    return Path(__file__).resolve().parents[3] / "schemas"


def load_registry(root: str | Path | None = None) -> tuple[Registry, dict[str, dict[str, Any]]]:
    base = schema_root(root)
    schemas: dict[str, dict[str, Any]] = {}
    resources: list[tuple[str, Resource]] = []
    for relative in SCHEMA_FILES:
        payload = json.loads((base / relative).read_text(encoding="utf-8"))
        schema_id = payload.get("$id")
        if not isinstance(schema_id, str) or not schema_id:
            raise ValueError(f"schema {relative} has no canonical $id")
        if schema_id in schemas:
            raise ValueError(f"duplicate schema id: {schema_id}")
        Draft202012Validator.check_schema(payload)
        schemas[schema_id] = payload
        resources.append((schema_id, Resource.from_contents(payload)))
    return Registry().with_resources(resources), schemas


def validation_errors(payload: dict[str, Any], schema_id: str, root: str | Path | None = None) -> list[str]:
    registry, schemas = load_registry(root)
    schema = schemas.get(schema_id)
    if schema is None:
        return [f"schema is not registered: {schema_id}"]
    validator = Draft202012Validator(schema, registry=registry, format_checker=FormatChecker())
    return [error.message for error in validator.iter_errors(payload)]


def require_valid(payload: dict[str, Any], schema_id: str, root: str | Path | None = None) -> None:
    errors = validation_errors(payload, schema_id, root)
    if errors:
        raise ValueError(f"{schema_id} validation failed: {'; '.join(errors)}")


def canonical_record_digest(payload: dict[str, Any], field: str = "record_digest") -> str:
    unsigned = {key: value for key, value in payload.items() if key != field}
    return hashlib.sha256(json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
