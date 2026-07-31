"""Provider-neutral execution provider adapter contract.

This module defines the seam between Orchestrator/dispatch records and concrete
execution providers. It performs deterministic validation only; provider work is
left to concrete adapters outside this contract.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field, fields
from datetime import datetime, timezone
import json
from pathlib import Path
from pathlib import PurePosixPath
from typing import Any
from uuid import uuid4
from jsonschema import Draft202012Validator, FormatChecker

from estate.core.orchestrator_intake import ALLOWED_CLASSIFICATIONS
from estate.core.authority_schema_runtime import load_registry

ADAPTER_RESULT_STATUSES = {"accepted", "dry_run_completed", "blocked", "failed", "completed"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _coerce_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, tuple):
        return [str(item) for item in value]
    if isinstance(value, str):
        return [value] if value.strip() else []
    return [str(value)]


def _required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required")
    return value


def _normalize_path(value: str) -> str:
    text = str(value).replace("\\", "/").strip()
    while "//" in text:
        text = text.replace("//", "/")
    return text.rstrip("/") or "."


def _paths_overlap(left: str, right: str) -> bool:
    left_norm = _normalize_path(left)
    right_norm = _normalize_path(right)
    if left_norm == "." or right_norm == ".":
        return True
    left_path = PurePosixPath(left_norm)
    right_path = PurePosixPath(right_norm)
    return left_path == right_path or left_path in right_path.parents or right_path in left_path.parents


@dataclass
class AdapterValidationStatus:
    status: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors and self.status == "accepted"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ExecutionProviderAdapterRequest:
    adapter_request_id: str
    dispatch_id: str
    provider_id: str
    provider_type: str
    profile_label: str | None = None
    work_package_id: str | None = None
    work_package_path: str | None = None
    prompt_source: str | None = None
    prompt_source_type: str | None = None
    prompt_source_digest: str | None = None
    classification: str = "Estate Internal"
    read_scope_paths: list[str] = field(default_factory=list)
    write_scope_paths: list[str] = field(default_factory=list)
    blocked_scope_paths: list[str] = field(default_factory=list)
    expected_outputs: list[str] = field(default_factory=list)
    validation_required: bool = True
    boundary_review_reference: str | None = None
    decision_reference: str | None = None
    authorization_reference: str | None = None
    grace_objective_id: str | None = None
    grace_action_id: str | None = None
    helen_determination_id: str | None = None
    engineering_commission_id: str | None = None
    engineering_authorization_id: str | None = None
    adapter_reference: str | None = None
    ptm_readiness: dict[str, Any] = field(default_factory=dict)
    provider_extension: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, **kwargs: Any) -> "ExecutionProviderAdapterRequest":
        kwargs.setdefault("adapter_request_id", f"adapter-{uuid4().hex[:12]}")
        kwargs.setdefault("created_at", utc_now())
        return cls.from_dict(kwargs)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExecutionProviderAdapterRequest":
        if not isinstance(data, dict):
            raise ValueError("adapter request must be a JSON object")
        allowed = {f.name for f in fields(cls)}
        values = {k: v for k, v in data.items() if k in allowed}
        for key in ("read_scope_paths", "write_scope_paths", "blocked_scope_paths", "expected_outputs"):
            values[key] = _coerce_list(values.get(key))
        values["metadata"] = values.get("metadata") if isinstance(values.get("metadata"), dict) else {}
        req = cls(**values)
        req.validate()
        return req

    @classmethod
    def from_dispatch_record(cls, record: Any, *, adapter_request_id: str | None = None, profile_label: str | None = None, prompt_source: str | None = None, metadata: dict[str, Any] | None = None) -> "ExecutionProviderAdapterRequest":
        data = record.to_dict() if hasattr(record, "to_dict") else dict(record)
        provider_id = data.get("provider_id") or (data.get("metadata") or {}).get("provider")
        provider_type = data.get("provider_type") or (data.get("metadata") or {}).get("provider_type") or provider_id
        return cls.create(
            adapter_request_id=adapter_request_id or f"adapter-{data.get('dispatch_id', uuid4().hex[:12])}",
            dispatch_id=data.get("dispatch_id"),
            provider_id=provider_id,
            provider_type=provider_type,
            profile_label=profile_label or (data.get("metadata") or {}).get("profile_label"),
            work_package_id=data.get("work_package_id"),
            work_package_path=data.get("work_package_path"),
            prompt_source=prompt_source or data.get("work_package_path"),
            prompt_source_type=(data.get("metadata") or {}).get("prompt_source_type"),
            prompt_source_digest=(data.get("metadata") or {}).get("prompt_source_digest"),
            classification=data.get("classification"),
            read_scope_paths=data.get("allowed_paths") or [],
            write_scope_paths=(data.get("metadata") or {}).get("write_scope_paths") or [],
            blocked_scope_paths=data.get("forbidden_paths") or [],
            expected_outputs=data.get("expected_outputs") or [],
            validation_required=bool(data.get("validation_required", True)),
            boundary_review_reference=data.get("boundary_review_reference"),
            decision_reference=data.get("decision_reference"),
            authorization_reference=(data.get("metadata") or {}).get("authorization_reference"),
            grace_objective_id=(data.get("metadata") or {}).get("grace_objective_id"),
            grace_action_id=(data.get("metadata") or {}).get("grace_action_id"),
            helen_determination_id=(data.get("metadata") or {}).get("helen_determination_id"),
            engineering_commission_id=(data.get("metadata") or {}).get("engineering_commission_id"),
            engineering_authorization_id=(data.get("metadata") or {}).get("engineering_authorization_id"),
            adapter_reference=(data.get("metadata") or {}).get("adapter_reference"),
            ptm_readiness=(data.get("metadata") or {}).get("ptm_readiness") or {},
            provider_extension=(data.get("metadata") or {}).get("provider_extension") or data.get("provider_extension") or {},
            metadata={**(data.get("metadata") or {}), **(metadata or {})},
        )

    def validate(self) -> AdapterValidationStatus:
        errors: list[str] = []
        warnings: list[str] = []
        for key in ("adapter_request_id", "dispatch_id", "provider_id", "provider_type", "created_at"):
            try:
                _required_text(getattr(self, key), key)
            except ValueError as exc:
                errors.append(str(exc))
        if self.classification not in ALLOWED_CLASSIFICATIONS:
            errors.append(f"classification must be one of {sorted(ALLOWED_CLASSIFICATIONS)}")
        for write_path in self.write_scope_paths:
            for blocked_path in self.blocked_scope_paths:
                if _paths_overlap(write_path, blocked_path):
                    errors.append(f"write path '{write_path}' conflicts with blocked path '{blocked_path}'")
        if not self.prompt_source:
            if (self.metadata or {}).get("technical_execution") is True:
                errors.append("prompt_source is required for technical execution")
            else:
                warnings.append("prompt_source is not set")
        if (self.metadata or {}).get("technical_execution") is True:
            for metadata_key, field_name in (("provider_id", "provider_id"), ("adapter_reference", "adapter_reference"), ("prompt_source_digest", "prompt_source_digest"), ("prompt_source_type", "prompt_source_type"), ("grace_objective_id", "grace_objective_id"), ("grace_action_id", "grace_action_id"), ("helen_determination_id", "helen_determination_id"), ("engineering_commission_id", "engineering_commission_id"), ("engineering_authorization_id", "engineering_authorization_id"), ("authorization_reference", "authorization_reference")):
                if metadata_key in self.metadata:
                    expected = getattr(self, field_name)
                    if self.metadata[metadata_key] != expected:
                        errors.append(f"metadata {metadata_key} conflicts with canonical adapter field")
            if not self.read_scope_paths:
                errors.append("allowed_read_paths are required for technical execution")
            if not self.write_scope_paths:
                errors.append("allowed_write_paths are required for technical execution")
            if not self.expected_outputs:
                errors.append("expected_outputs are required for technical execution")
            def within(output: str, scope: str) -> bool:
                output_parts = tuple(str(output).replace("\\", "/").strip("/").split("/"))
                scope_parts = tuple(str(scope).replace("\\", "/").strip("/").split("/"))
                return output_parts == scope_parts or output_parts[:len(scope_parts)] == scope_parts
            if not all(any(within(output, scope) for scope in self.write_scope_paths) for output in self.expected_outputs):
                errors.append("expected_outputs must remain within allowed_write_paths for technical execution")
            if not self.decision_reference:
                errors.append("decision_reference is required for technical execution")
            for field_name in ("prompt_source_type", "prompt_source_digest", "authorization_reference", "grace_objective_id", "grace_action_id", "helen_determination_id", "engineering_commission_id", "engineering_authorization_id"):
                if not getattr(self, field_name):
                    errors.append(f"{field_name} is required for technical execution")
            if not self.ptm_readiness:
                errors.append("ptm_readiness is required for technical execution")
            if self.provider_id == "qwen.local.text" and not self.provider_extension:
                errors.append("provider_extension is required for Qwen technical execution")
            schema_path = Path(__file__).resolve().parents[3] / "schemas/execution_provider_adapter_request_v1.schema.json"
            try:
                registry, schemas = load_registry(schema_path.parents[1])
                schema = schemas["estate.execution-provider-adapter.request.v1"]
                errors.extend(error.message for error in Draft202012Validator(schema, registry=registry, format_checker=FormatChecker()).iter_errors(asdict(self)))
            except (OSError, ValueError) as exc:
                errors.append(f"technical adapter request schema unavailable: {exc}")
        status = "accepted" if not errors else "blocked"
        return AdapterValidationStatus(status=status, errors=errors, warnings=warnings)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ExecutionProviderAdapterResult:
    adapter_request_id: str
    dispatch_id: str
    provider_id: str
    status: str
    started_at: str
    finished_at: str | None = None
    summary: str = ""
    artifacts: list[str] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)
    validation_status: str = "not_run"
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if self.status not in ADAPTER_RESULT_STATUSES:
            raise ValueError(f"status must be one of {sorted(ADAPTER_RESULT_STATUSES)}")
        for key in ("adapter_request_id", "dispatch_id", "provider_id", "started_at"):
            _required_text(getattr(self, key), key)

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


class ExecutionProviderAdapter(ABC):
    adapter_id: str
    provider_id: str
    provider_type: str

    def supports(self, request: ExecutionProviderAdapterRequest) -> bool:
        return request.provider_id == self.provider_id and request.provider_type == self.provider_type

    def validate_request(self, request: ExecutionProviderAdapterRequest) -> AdapterValidationStatus:
        return request.validate()

    @abstractmethod
    def dry_run(self, request: ExecutionProviderAdapterRequest) -> ExecutionProviderAdapterResult:
        raise NotImplementedError

    @abstractmethod
    def submit(self, request: ExecutionProviderAdapterRequest) -> ExecutionProviderAdapterResult:
        raise NotImplementedError


class DeterministicDryRunExecutionProviderAdapter(ExecutionProviderAdapter):
    def __init__(self, provider_id: str = "dry-run-provider", provider_type: str = "dry-run", adapter_id: str = "deterministic-dry-run-adapter") -> None:
        self.adapter_id = adapter_id
        self.provider_id = provider_id
        self.provider_type = provider_type

    def supports(self, request: ExecutionProviderAdapterRequest) -> bool:
        return request.provider_id == self.provider_id and request.provider_type in {self.provider_type, "dry-run"}

    def dry_run(self, request: ExecutionProviderAdapterRequest) -> ExecutionProviderAdapterResult:
        started = utc_now()
        validation = self.validate_request(request)
        status = "dry_run_completed" if validation.ok else "blocked"
        return ExecutionProviderAdapterResult(
            adapter_request_id=request.adapter_request_id,
            dispatch_id=request.dispatch_id,
            provider_id=request.provider_id,
            status=status,
            started_at=started,
            finished_at=utc_now(),
            summary="Deterministic dry-run validated adapter request without provider execution." if validation.ok else "Adapter request blocked during deterministic validation.",
            artifacts=[],
            events=[{"event_type": "adapter_dry_run", "at": started, "provider_id": request.provider_id, "status": status}],
            validation_status="passed" if validation.ok else "failed",
            errors=validation.errors,
            warnings=validation.warnings,
            metadata={"adapter_id": self.adapter_id, "provider_type": self.provider_type, "live_provider_called": False},
        )

    def submit(self, request: ExecutionProviderAdapterRequest) -> ExecutionProviderAdapterResult:
        validation = self.validate_request(request)
        return ExecutionProviderAdapterResult(
            adapter_request_id=request.adapter_request_id,
            dispatch_id=request.dispatch_id,
            provider_id=request.provider_id,
            status="accepted" if validation.ok else "blocked",
            started_at=utc_now(),
            finished_at=utc_now(),
            summary="Deterministic adapter accepted request for handoff validation only; no provider work was submitted.",
            validation_status="passed" if validation.ok else "failed",
            errors=validation.errors,
            warnings=validation.warnings,
            metadata={"adapter_id": self.adapter_id, "live_provider_called": False, "submit_mode": "contract_only"},
        )
