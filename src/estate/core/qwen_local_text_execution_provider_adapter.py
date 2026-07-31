"""Bounded local Qwen text-generation adapter for the existing Ollama service.

This adapter is intentionally separate from the Codex bridge.  It performs
only loopback HTTP text generation, writes only explicitly declared outputs,
and records a bounded provider receipt without storing the prompt contents.
"""
from __future__ import annotations

import hashlib
import json
import ipaddress
import socket
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from estate.core.execution_provider_adapter import (
    AdapterValidationStatus,
    ExecutionProviderAdapter,
    ExecutionProviderAdapterRequest,
    ExecutionProviderAdapterResult,
    utc_now,
)
from estate.core.paths import ESTATE_ROOT

PROVIDER_ID = "qwen.local.text"
ADAPTER_ID = "qwen-local-ollama-text-adapter"
ADAPTER_VERSION = "1.0.0"
SUPPORTED_CAPABILITIES = {"documentation_draft", "text_generation", "bounded_repository_read"}
RECEIPT_DIR = Path("runtime/engineering_adapter_receipts")


def _root(root: str | Path | None) -> Path:
    return Path(root) if root is not None else ESTATE_ROOT


def _parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo is not None else None
    except ValueError:
        return None


def _is_loopback_endpoint(value: str) -> bool:
    parsed = urlparse(value)
    if (parsed.scheme != "http" or parsed.path not in {"", "/"} or parsed.query
            or parsed.fragment or parsed.username or parsed.password):
        return False
    host = (parsed.hostname or "").lower()
    if host == "localhost":
        return True
    try:
        return bool(host) and ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


class QwenLocalTextExecutionProviderAdapter(ExecutionProviderAdapter):
    adapter_id = ADAPTER_ID
    provider_id = PROVIDER_ID
    provider_type = "execution"

    def __init__(self, *, root: str | Path | None = None, config_path: str | Path | None = None,
                 http_call: Callable[..., tuple[int, dict[str, Any]]] | None = None) -> None:
        self.root = _root(root)
        self.config_path = Path(config_path) if config_path else self.root / "config/providers/qwen_local_text.json"
        self.http_call = http_call or self._http_call

    def _config(self) -> dict[str, Any]:
        try:
            config = json.loads(self.config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"Qwen provider configuration is unavailable or malformed: {exc}") from exc
        if not isinstance(config, dict):
            raise ValueError("Qwen provider configuration must be a JSON object")
        required = ("provider_id", "adapter_id", "adapter_version", "endpoint_type", "endpoint_address", "model_identity", "context_limit", "timeout_seconds", "supported_capabilities", "health_check", "output_limits", "network_policy", "evidence_freshness_seconds")
        missing = [key for key in required if key not in config or config[key] in (None, "", [])]
        if missing:
            raise ValueError(f"Qwen provider configuration is missing: {', '.join(missing)}")
        if config["provider_id"] != PROVIDER_ID or config["adapter_id"] != ADAPTER_ID or config["adapter_version"] != ADAPTER_VERSION:
            raise ValueError("Qwen provider configuration identity does not match the registered adapter")
        if config["endpoint_type"] != "ollama-http" or config["network_policy"] != "loopback_only" or not _is_loopback_endpoint(config["endpoint_address"]):
            raise ValueError("Qwen endpoint must be an HTTP loopback Ollama endpoint")
        if not isinstance(config["model_identity"], str) or not config["model_identity"].lower().startswith("qwen"):
            raise ValueError("configured model identity must be a Qwen-family model")
        if (not isinstance(config["supported_capabilities"], list)
                or not config["supported_capabilities"]
                or not set(config["supported_capabilities"]).issubset(SUPPORTED_CAPABILITIES)):
            raise ValueError("Qwen configuration contains unsupported capabilities")
        for key in ("context_limit", "timeout_seconds", "evidence_freshness_seconds"):
            if not isinstance(config[key], int) or isinstance(config[key], bool) or config[key] < 1:
                raise ValueError(f"Qwen configuration requires a positive integer {key}")
        limits = config["output_limits"]
        if (not isinstance(limits, dict)
                or not all(isinstance(limits.get(key), int) and not isinstance(limits.get(key), bool) and limits[key] > 0
                           for key in ("max_output_tokens", "max_artifact_bytes"))):
            raise ValueError("Qwen output limits must be positive integers")
        if config["health_check"] != {"method": "GET", "path": "/api/tags", "requires_model_present": True}:
            raise ValueError("Qwen health check does not match the governed Ollama contract")
        return config

    @staticmethod
    def _http_call(method: str, url: str, payload: dict[str, Any] | None, timeout: int) -> tuple[int, dict[str, Any]]:
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        request = Request(url, data=body, method=method, headers={"Content-Type": "application/json"} if body else {})
        class _NoRedirect(HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, new):
                raise HTTPError(req.full_url, code, "redirects are prohibited", headers, fp)

        with build_opener(_NoRedirect()).open(request, timeout=timeout) as response:  # loopback URL is validated first
            raw = response.read(1_000_001)
        if len(raw) > 1_000_000:
            raise ValueError("Qwen service response exceeds the bounded transport limit")
        return int(response.status), json.loads(raw.decode("utf-8"))

    def _metadata_errors(self, request: ExecutionProviderAdapterRequest, config: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        metadata = request.metadata
        capability = str(metadata.get("requested_capability") or "")
        if capability not in SUPPORTED_CAPABILITIES or capability not in config["supported_capabilities"]:
            errors.append("requested capability is unsupported by qwen.local.text")
        if metadata.get("sandbox", "workspace-write") not in {"read-only", "workspace-write"}:
            errors.append("Qwen adapter accepts only read-only or workspace-write boundaries")
        for key in ("shell_authority", "automatic_merge_authority", "institutional_acceptance_authority"):
            if metadata.get(key) not in {False, None}:
                errors.append(f"{key} is prohibited")
        if metadata.get("cancel_requested") is True:
            errors.append("cancellation requested before Qwen invocation")
        if metadata.get("authorized_model_identity") and metadata["authorized_model_identity"] != config["model_identity"]:
            errors.append("configured model differs from the authorized model")
        if not metadata.get("authorization_reference"):
            errors.append("authorization evidence is required")
        observed = _parse_time(metadata.get("evidence_observed_at")); expires = _parse_time(metadata.get("evidence_expires_at")); now = datetime.now(timezone.utc)
        if observed is None or expires is None:
            errors.append("fresh qualification and health evidence timestamps are required")
        elif (observed > now or expires <= now or expires <= observed
              or (now - observed).total_seconds() > int(config["evidence_freshness_seconds"])):
            errors.append("qualification or health evidence is stale")
        if not request.expected_outputs or not request.write_scope_paths:
            errors.append("exact expected output and write scope are required")
        if set(request.expected_outputs) != set(request.write_scope_paths):
            errors.append("Qwen adapter requires write scopes to equal exact expected outputs")
        for path in request.expected_outputs:
            normalized = str(path).replace("\\", "/")
            if not normalized or normalized.startswith("/") or ":" in normalized[:3] or ".." in normalized.split("/"):
                errors.append(f"invalid expected output path: {path}")
            if not normalized.startswith("docs/"):
                errors.append(f"Qwen output is outside the permitted documentation boundary: {path}")
        return errors

    def validate_request(self, request: ExecutionProviderAdapterRequest) -> AdapterValidationStatus:
        base = request.validate(); errors = list(base.errors); warnings = list(base.warnings)
        if not self.supports(request):
            errors.append("request does not target qwen.local.text execution")
        try:
            config = self._config()
            errors.extend(self._metadata_errors(request, config))
        except ValueError as exc:
            errors.append(str(exc))
        return AdapterValidationStatus(status="accepted" if not errors else "blocked", errors=errors, warnings=warnings)

    def supports(self, request: ExecutionProviderAdapterRequest) -> bool:
        return request.provider_id == PROVIDER_ID and request.provider_type in {"execution", "qwen-local-text"}

    def dry_run(self, request: ExecutionProviderAdapterRequest) -> ExecutionProviderAdapterResult:
        validation = self.validate_request(request); now = utc_now()
        return ExecutionProviderAdapterResult(adapter_request_id=request.adapter_request_id, dispatch_id=request.dispatch_id, provider_id=PROVIDER_ID, status="dry_run_completed" if validation.ok else "blocked", started_at=now, finished_at=utc_now(), summary="Qwen local adapter request validated without provider invocation.", validation_status="passed" if validation.ok else "failed", errors=validation.errors, warnings=validation.warnings, metadata={"adapter_id": ADAPTER_ID, "adapter_version": ADAPTER_VERSION, "live_provider_called": False})

    def submit(self, request: ExecutionProviderAdapterRequest) -> ExecutionProviderAdapterResult:
        started = utc_now(); validation = self.validate_request(request)
        if not validation.ok:
            return ExecutionProviderAdapterResult(adapter_request_id=request.adapter_request_id, dispatch_id=request.dispatch_id, provider_id=PROVIDER_ID, status="blocked", started_at=started, finished_at=utc_now(), summary="Qwen local adapter request blocked before provider invocation.", validation_status="failed", errors=validation.errors, warnings=validation.warnings, metadata={"adapter_id": ADAPTER_ID, "adapter_version": ADAPTER_VERSION, "live_provider_called": False})
        config = self._config(); endpoint = config["endpoint_address"].rstrip("/"); metadata = request.metadata
        try:
            health_status, health = self.http_call("GET", endpoint + config["health_check"]["path"], None, int(config["timeout_seconds"]))
            names = {str(item.get("name") or item.get("model")) for item in health.get("models", [])} if isinstance(health, dict) else set()
            if health_status >= 400 or config["model_identity"] not in names:
                raise ValueError("configured Qwen model is not present in the healthy local service")
            prompt = str(metadata.get("prompt_text") or "")
            if not prompt:
                raise ValueError("bounded prompt_text is required")
            if len(prompt.encode("utf-8")) > int(config["context_limit"]) * 4:
                raise ValueError("Qwen prompt exceeds the configured context bound")
            if metadata.get("cancel_requested") is True:
                raise ValueError("cancellation requested before Qwen generation")
            status, response = self.http_call("POST", endpoint + "/api/generate", {"model": config["model_identity"], "prompt": prompt, "stream": False, "options": {"num_ctx": config.get("context_limit"), "num_predict": config["output_limits"]["max_output_tokens"]}}, int(config["timeout_seconds"]))
            text = response.get("response") if isinstance(response, dict) else None
            actual_model = response.get("model") if isinstance(response, dict) else None
            if status >= 400 or not isinstance(text, str) or not text.strip():
                raise ValueError("Qwen returned a malformed or incomplete response")
            if actual_model != config["model_identity"]:
                raise ValueError("Qwen service returned a model identity different from the authorized model")
            eval_count = response.get("eval_count")
            if eval_count is not None and (not isinstance(eval_count, int) or eval_count > int(config["output_limits"]["max_output_tokens"])):
                raise ValueError("Qwen output exceeds the configured token limit")
            encoded = text.strip().encode("utf-8")
            if len(encoded) > int(config["output_limits"]["max_artifact_bytes"]):
                raise ValueError("Qwen output exceeds the configured artifact limit")
            for output in request.expected_outputs:
                target = (self.root / output).resolve(); target.relative_to(self.root.resolve()); target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(encoded)
            artifacts = [str(path).replace("\\", "/") for path in request.expected_outputs]
            receipt_path = self.root / RECEIPT_DIR / f"qwen-{request.adapter_request_id}.json"; receipt_path.parent.mkdir(parents=True, exist_ok=True)
            receipt = {"schema_version": "estate.provider-receipt.v1", "provider_id": PROVIDER_ID, "adapter_id": ADAPTER_ID, "adapter_version": ADAPTER_VERSION, "endpoint_type": config["endpoint_type"], "authorized_model_identity": config["model_identity"], "actual_model_identity": actual_model or config["model_identity"], "request_id": request.adapter_request_id, "dispatch_id": request.dispatch_id, "grace_objective_id": metadata.get("grace_objective_id"), "capability_inquiry_reference": metadata.get("capability_inquiry_reference"), "helen_assessment_reference": metadata.get("helen_assessment_reference"), "source_commit": metadata.get("source_commit"), "sandbox": metadata.get("sandbox"), "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(), "artifacts": [{"path": path, "sha256": hashlib.sha256((self.root / path).read_bytes()).hexdigest()} for path in artifacts], "started_at": started, "completed_at": utc_now(), "timeout_state": "completed_within_limit", "cancellation_state": "not_requested", "provider_result_state": "completed", "validation_result": "passed", "endpoint_local": True, "error_details": []}
            receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"); receipt_ref = str(receipt_path.relative_to(self.root)).replace("\\", "/"); artifacts.append(receipt_ref)
            return ExecutionProviderAdapterResult(adapter_request_id=request.adapter_request_id, dispatch_id=request.dispatch_id, provider_id=PROVIDER_ID, status="completed", started_at=started, finished_at=utc_now(), summary="Qwen local text generation completed within the governed loopback boundary.", artifacts=artifacts, validation_status="passed", metadata={"adapter_id": ADAPTER_ID, "adapter_version": ADAPTER_VERSION, "provider_receipt": receipt_ref, "receipt_reference": receipt_ref, "actual_model_identity": actual_model or config["model_identity"], "live_provider_called": True, "endpoint_local": True})
        except (OSError, HTTPError, URLError, TimeoutError, socket.timeout, ValueError, KeyError, json.JSONDecodeError) as exc:
            return ExecutionProviderAdapterResult(adapter_request_id=request.adapter_request_id, dispatch_id=request.dispatch_id, provider_id=PROVIDER_ID, status="failed", started_at=started, finished_at=utc_now(), summary="Qwen local provider invocation failed closed.", validation_status="failed", errors=[str(exc)], metadata={"adapter_id": ADAPTER_ID, "adapter_version": ADAPTER_VERSION, "live_provider_called": True, "endpoint_local": True})
