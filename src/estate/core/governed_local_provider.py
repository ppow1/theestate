"""Governed local provider boundary for WP-4232-U1.

Only adapters registered in this module may execute.  The initial adapter is a
pure Python SHA-256 effect: it has no subprocess, network, filesystem, or
machine-state capability.
"""
from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from typing import Any


class ProviderAdmissionError(ValueError):
    pass


@dataclass(frozen=True)
class AdapterDescriptor:
    adapter_id: str
    version: str
    capability: str
    effect_type: str
    locality: str
    egress: bool
    spend: bool
    mutates_machine_state: bool
    deterministic: bool
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    stop_capable: bool
    rollback_capable: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


SHA256_DESCRIPTOR = AdapterDescriptor(
    adapter_id="estate.local.sha256",
    version="1.0.0",
    capability="deterministic.sha256",
    effect_type="local_hash",
    locality="in_process",
    egress=False,
    spend=False,
    mutates_machine_state=False,
    deterministic=True,
    input_schema={"type": "string", "encoding": "UTF-8", "max_bytes": 4096},
    output_schema={"type": "object", "required": ["sha256", "input_bytes"]},
    stop_capable=True,
    rollback_capable=True,
)

ADAPTERS = {SHA256_DESCRIPTOR.adapter_id: SHA256_DESCRIPTOR}


def descriptor(adapter_id: str) -> AdapterDescriptor:
    try:
        return ADAPTERS[adapter_id]
    except KeyError as exc:
        raise ProviderAdmissionError("unknown local provider adapter") from exc


def validate_admission(descriptor_value: AdapterDescriptor, admission: dict[str, Any]) -> None:
    required = {
        "adapter_id", "adapter_version", "capability", "admitting_authority",
        "authority_source", "locality_assertion", "no_egress_assertion",
        "no_spend_assertion", "deterministic_effect_assertion", "input_schema",
        "output_schema", "effect_identity_policy", "stop_capable",
        "rollback_capable",
    }
    if not required <= admission.keys():
        raise ProviderAdmissionError("provider admission is missing required assertions")
    if admission["adapter_id"] != descriptor_value.adapter_id or admission["adapter_version"] != descriptor_value.version:
        raise ProviderAdmissionError("provider adapter identity/version mismatch")
    if admission["capability"] != descriptor_value.capability:
        raise ProviderAdmissionError("provider capability mismatch")
    if admission["admitting_authority"] != "Engineering" or not isinstance(admission["authority_source"], str) or not admission["authority_source"]:
        raise ProviderAdmissionError("Engineering admission authority is required")
    if admission["locality_assertion"] != "in_process" or admission["no_egress_assertion"] is not True or admission["no_spend_assertion"] is not True or admission["deterministic_effect_assertion"] is not True:
        raise ProviderAdmissionError("locality, egress, spend, and determinism assertions failed")
    if admission["input_schema"] != descriptor_value.input_schema or admission["output_schema"] != descriptor_value.output_schema:
        raise ProviderAdmissionError("provider task schema mismatch")
    if admission["stop_capable"] is not True or admission["rollback_capable"] is not True:
        raise ProviderAdmissionError("stop and rollback capability is required")


def normalize_task_input(value: Any) -> str:
    if not isinstance(value, str) or not value:
        raise ProviderAdmissionError("task input must be a non-empty UTF-8 string")
    encoded = value.encode("utf-8")
    if len(encoded) > int(SHA256_DESCRIPTOR.input_schema["max_bytes"]):
        raise ProviderAdmissionError("task input exceeds the governed schema")
    return value


def execute_sha256(task_input: str, *, stop_requested: bool = False) -> dict[str, Any]:
    if stop_requested:
        raise ProviderAdmissionError("provider effect stopped before commit")
    normalized = normalize_task_input(task_input)
    encoded = normalized.encode("utf-8")
    digest = hashlib.sha256(encoded).hexdigest()
    return {"sha256": digest, "input_bytes": len(encoded), "encoding": "UTF-8"}
