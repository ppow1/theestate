"""Canonical PTM waiver-authority registry loading and validation."""

from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from .ptm_policy import _time
from .ptm_production_readiness import PtmReadinessError, digest

REGISTRY_PATH = Path("config/ptm/waiver_authorities.json")
REGISTRY_SCHEMA_PATH = Path("schemas/ptm/waiver_authorities_v1.schema.json")


def load_waiver_registry(root: Path, *, observed_at: str | None = None) -> dict[str, Any]:
    root = Path(root).resolve()
    try:
        registry = json.loads((root / REGISTRY_PATH).read_text(encoding="utf-8"))
        schema = json.loads((root / REGISTRY_SCHEMA_PATH).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PtmReadinessError("waiver authority registry missing or malformed") from exc
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(registry), key=lambda error: list(error.path))
    if errors:
        raise PtmReadinessError("waiver registry schema invalid: " + errors[0].message)
    unsigned = dict(registry)
    declared = unsigned.pop("registry_digest", None)
    computed = digest(unsigned)
    if declared not in (None, computed):
        raise PtmReadinessError("waiver registry digest mismatch")
    registry["registry_digest"] = computed
    if observed_at is not None and _time(observed_at) < _time(registry["effective_at"]):
        raise PtmReadinessError("waiver authority registry is not yet effective")
    return registry


def validate_waiver_authority(registry: dict[str, Any], waiver: dict[str, Any], *, objective_id: str, package_id: str | None, task_id: str, observed_at: str) -> list[str]:
    errors: list[str] = []
    authority_id = waiver.get("granting_authority")
    authority = next((item for item in registry["authorities"] if item["authority_id"] == authority_id), None)
    if authority is None:
        return ["waiver authority is not registered"]
    now = _time(observed_at)
    if authority.get("revoked") or (authority.get("expires_at") and _time(authority["expires_at"]) <= now) or _time(authority["effective_at"]) > now:
        errors.append("waiver authority is expired, revoked, or not effective")
    if waiver.get("waiver_type", "dependency") not in authority["permitted_waiver_types"]:
        errors.append("waiver type is not permitted by authority")
    scope = waiver.get("scope") or {}
    if authority.get("scope_policy") != "exact_objective_package_task" or scope.get("objective_id") != objective_id or scope.get("task_id") != task_id or (package_id is not None and scope.get("package_id") != package_id):
        errors.append("waiver scope is not exact or does not match")
    if not waiver.get("expires_at"):
        errors.append("waiver requires finite expiry")
    else:
        try:
            if _time(waiver["expires_at"]) <= now or _time(waiver["expires_at"]) - _time(waiver["granted_at"]) > timedelta(seconds=86400):
                errors.append("waiver expiry is invalid or exceeds 24 hours")
        except (KeyError, ValueError, PtmReadinessError):
            errors.append("waiver timestamps invalid")
    if waiver.get("authority_registry_id") != registry["registry_id"] or waiver.get("authority_registry_version") != registry["registry_version"] or waiver.get("authority_registry_digest") != registry["registry_digest"]:
        errors.append("waiver authority registry reference mismatch")
    return errors
