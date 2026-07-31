"""Bounded local Qwen text-generation adapter for the existing Ollama service.

This adapter is intentionally separate from the Codex bridge.  It performs
only loopback HTTP text generation, writes only explicitly declared outputs,
and records a bounded provider receipt without storing the prompt contents.
"""
from __future__ import annotations

import hashlib
import json
import ipaddress
import os
import socket
from dataclasses import dataclass
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
RECEIPT_ROOT = "runtime/engineering_adapter_receipts/"


@dataclass(frozen=True)
class _ExclusiveWriteToken:
    path: Path
    st_dev: int
    st_ino: int


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
        receipt_path = str(metadata.get("provider_receipt_path") or "").replace("\\", "/")
        if not receipt_path:
            errors.append("provider_receipt_path is required for live execution")
        elif (not receipt_path.startswith(RECEIPT_ROOT)
              or "/" in receipt_path[len(RECEIPT_ROOT):]
              or not receipt_path.endswith(".json")
              or receipt_path == RECEIPT_ROOT + ".json"):
            errors.append("provider_receipt_path must be one exact JSON file below runtime/engineering_adapter_receipts/")
        if not request.expected_outputs or not request.write_scope_paths:
            errors.append("exact expected output and write scope are required")
        if set(request.expected_outputs) != set(request.write_scope_paths):
            errors.append("Qwen adapter requires write scopes to equal exact expected outputs")
        if receipt_path and (receipt_path not in request.expected_outputs or receipt_path not in request.write_scope_paths):
            errors.append("provider_receipt_path must be included in expected outputs and authorized write scopes")
        document_outputs = [str(path).replace("\\", "/") for path in request.expected_outputs if not str(path).replace("\\", "/").startswith("runtime/")]
        if len(document_outputs) != 1:
            errors.append("Qwen requests require exactly one declared documentation artifact plus one receipt")
        for path in request.expected_outputs:
            normalized = str(path).replace("\\", "/")
            if not normalized or normalized.startswith("/") or ":" in normalized[:3] or ".." in normalized.split("/"):
                errors.append(f"invalid expected output path: {path}")
            if normalized.startswith("runtime/") and normalized != receipt_path:
                errors.append(f"runtime output is not the declared provider receipt: {path}")
            if not normalized.startswith("docs/") and normalized != receipt_path:
                errors.append(f"Qwen output is outside the permitted documentation boundary: {path}")
        if document_outputs and not document_outputs[0].startswith("docs/"):
            errors.append("the Qwen document artifact must be under docs/")
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

    def _write_receipt(self, request: ExecutionProviderAdapterRequest, config: dict[str, Any], *, started: str,
                       result_state: str, validation_result: str, timeout_state: str,
                       cancellation_state: str, actual_model: str | None, prompt: str,
                       artifacts: list[str], errors: list[str], endpoint_local: bool) -> str:
        receipt_ref = str(request.metadata["provider_receipt_path"]).replace("\\", "/")
        payload = {
            "schema_version": "estate.provider-receipt.v1", "provider_id": PROVIDER_ID,
            "adapter_id": ADAPTER_ID, "adapter_version": ADAPTER_VERSION,
            "endpoint_type": config["endpoint_type"], "authorized_model_identity": config["model_identity"],
            "actual_model_identity": actual_model, "request_id": request.adapter_request_id,
            "dispatch_id": request.dispatch_id, "grace_objective_id": request.metadata.get("grace_objective_id"),
            "capability_inquiry_reference": request.metadata.get("capability_inquiry_reference"),
            "helen_assessment_reference": request.metadata.get("helen_assessment_reference"),
            "source_commit": request.metadata.get("source_commit"), "sandbox": request.metadata.get("sandbox"),
            "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest() if prompt else None,
            "declared_artifact_paths": list(request.expected_outputs),
            "artifacts": [{"path": path, "sha256": hashlib.sha256((self.root / path).read_bytes()).hexdigest()} for path in artifacts],
            "started_at": started, "completed_at": utc_now(), "timeout_state": timeout_state,
            "cancellation_state": cancellation_state, "provider_result_state": result_state,
            "validation_result": validation_result, "endpoint_local": endpoint_local,
            "error_details": [str(error)[:500] for error in errors],
        }
        self._exclusive_write_text(self.root / receipt_ref, json.dumps(payload, indent=2, sort_keys=True) + "\n")
        return receipt_ref

    @staticmethod
    def _exclusive_write_text(target: Path, content: str) -> _ExclusiveWriteToken:
        target = target.resolve(strict=False)
        target.parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        identity = os.fstat(descriptor)
        stream = None
        close_attempted = False
        try:
            stream = os.fdopen(descriptor, "wb", buffering=0, closefd=True)
            descriptor = None
            payload = content.encode("utf-8")
            offset = 0
            while offset < len(payload):
                remaining = payload[offset:]
                written = stream.write(remaining)
                if written is None or not isinstance(written, int) or written <= 0:
                    raise OSError("exclusive write made no progress")
                if written > len(remaining):
                    raise OSError("exclusive write reported more bytes than supplied")
                offset += written
            stream.flush()
            os.fsync(stream.fileno())
            stream_descriptor = stream.fileno()
            close_attempted = True
            try:
                stream.close()
            except Exception:
                # A close failure may leave the descriptor open on Windows.  A
                # second low-level close is attempted only after close was
                # already attempted, and its error cannot mask the original.
                try:
                    os.close(stream_descriptor)
                except OSError:
                    pass
                raise
            stream = None
        except Exception:
            if stream is not None and not close_attempted:
                try:
                    stream.close()
                except OSError:
                    pass
            elif descriptor is not None:
                try:
                    os.close(descriptor)
                except OSError:
                    pass
            try:
                current = target.stat()
                if (current.st_dev, current.st_ino) == (identity.st_dev, identity.st_ino):
                    target.unlink()
            except OSError:
                pass
            raise
        return _ExclusiveWriteToken(path=target, st_dev=identity.st_dev, st_ino=identity.st_ino)

    @staticmethod
    def _remove_if_owned(token: _ExclusiveWriteToken) -> bool:
        try:
            current = token.path.stat()
        except FileNotFoundError:
            return True
        except OSError:
            return False
        if (current.st_dev, current.st_ino) != (token.st_dev, token.st_ino):
            return False
        try:
            token.path.unlink()
        except FileNotFoundError:
            return True
        except OSError:
            return False
        return True

    def _target_collision_errors(self, request: ExecutionProviderAdapterRequest) -> tuple[list[str], Path | None, Path | None]:
        document_path = next((str(path).replace("\\", "/") for path in request.expected_outputs if not str(path).replace("\\", "/").startswith("runtime/")), None)
        receipt_ref = str(request.metadata.get("provider_receipt_path") or "").replace("\\", "/")
        if not document_path or not receipt_ref:
            return [], None, None
        root = self.root.resolve()
        document_target = (self.root / document_path).resolve(strict=False)
        receipt_target = (self.root / receipt_ref).resolve(strict=False)
        errors: list[str] = []
        try:
            document_target.relative_to(root); receipt_target.relative_to(root)
        except ValueError:
            return ["declared output resolves outside the repository root"], document_target, receipt_target
        if document_target == receipt_target or document_target in receipt_target.parents or receipt_target in document_target.parents:
            errors.append("document and provider receipt targets must be distinct non-shadowing files")
        for label, target in (("documentation artifact", document_target), ("provider receipt", receipt_target)):
            if target.exists():
                errors.append(f"{label} target already exists; governed outputs are create-once")
            for parent in target.parents:
                if parent == root:
                    break
                if parent.exists() and not parent.is_dir():
                    errors.append(f"{label} parent path is shadowed by an existing file")
                    break
        return errors, document_target, receipt_target

    def submit(self, request: ExecutionProviderAdapterRequest) -> ExecutionProviderAdapterResult:
        started = utc_now(); validation = self.validate_request(request)
        if not validation.ok:
            return ExecutionProviderAdapterResult(adapter_request_id=request.adapter_request_id, dispatch_id=request.dispatch_id, provider_id=PROVIDER_ID, status="blocked", started_at=started, finished_at=utc_now(), summary="Qwen local adapter request blocked before provider invocation.", validation_status="failed", errors=validation.errors, warnings=validation.warnings, metadata={"adapter_id": ADAPTER_ID, "adapter_version": ADAPTER_VERSION, "live_provider_called": False})
        config = self._config(); target_errors, document_target, _ = self._target_collision_errors(request)
        if target_errors:
            return ExecutionProviderAdapterResult(adapter_request_id=request.adapter_request_id, dispatch_id=request.dispatch_id, provider_id=PROVIDER_ID, status="blocked", started_at=started, finished_at=utc_now(), summary="Qwen local adapter request blocked by governed output collision.", validation_status="failed", errors=target_errors, metadata={"adapter_id": ADAPTER_ID, "adapter_version": ADAPTER_VERSION, "live_provider_called": False})
        endpoint = config["endpoint_address"].rstrip("/"); metadata = request.metadata; prompt = str(metadata.get("prompt_text") or ""); actual_model = None; document_path = next(path for path in request.expected_outputs if not str(path).replace("\\", "/").startswith("runtime/")); document_token = None
        try:
            health_status, health = self.http_call("GET", endpoint + config["health_check"]["path"], None, int(config["timeout_seconds"]))
            names = {str(item.get("name") or item.get("model")) for item in health.get("models", [])} if isinstance(health, dict) else set()
            if health_status >= 400 or config["model_identity"] not in names:
                raise ValueError("configured Qwen model is not present in the healthy local service")
            if not prompt:
                raise ValueError("bounded prompt_text is required")
            if len(prompt.encode("utf-8")) > int(config["context_limit"]) * 4:
                raise ValueError("Qwen prompt exceeds the configured context bound")
            status, response = self.http_call("POST", endpoint + "/api/generate", {"model": config["model_identity"], "prompt": prompt, "stream": False, "options": {"num_ctx": config.get("context_limit"), "num_predict": config["output_limits"]["max_output_tokens"]}}, int(config["timeout_seconds"]))
            text = response.get("response") if isinstance(response, dict) else None; actual_model = response.get("model") if isinstance(response, dict) else None
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
            target = document_target or (self.root / document_path).resolve(); target.relative_to(self.root.resolve())
            try:
                document_token = self._exclusive_write_text(target, encoded.decode("utf-8"))
            except Exception as exc:
                raise OSError(f"document persistence failed: {str(exc)[:400]}") from exc
            try:
                receipt_ref = self._write_receipt(request, config, started=started, result_state="completed", validation_result="passed", timeout_state="completed_within_limit", cancellation_state="not_requested", actual_model=actual_model, prompt=prompt, artifacts=[document_path], errors=[], endpoint_local=True)
            except Exception as exc:
                rollback_warning = ""
                if document_token is not None and not self._remove_if_owned(document_token):
                    rollback_warning = "; document rollback skipped because file identity changed or cleanup failed"
                raise OSError(f"success receipt persistence failed: {str(exc)[:400]}{rollback_warning}") from exc
            artifacts = [document_path, receipt_ref]
            return ExecutionProviderAdapterResult(adapter_request_id=request.adapter_request_id, dispatch_id=request.dispatch_id, provider_id=PROVIDER_ID, status="completed", started_at=started, finished_at=utc_now(), summary="Qwen local text generation completed within the governed loopback boundary.", artifacts=artifacts, validation_status="passed", metadata={"adapter_id": ADAPTER_ID, "adapter_version": ADAPTER_VERSION, "provider_receipt": receipt_ref, "receipt_reference": receipt_ref, "actual_model_identity": actual_model, "live_provider_called": True, "endpoint_local": True})
        except (OSError, HTTPError, URLError, TimeoutError, socket.timeout, ValueError, KeyError, json.JSONDecodeError) as exc:
            timeout_state = "timed_out" if isinstance(exc, (TimeoutError, socket.timeout)) or "timed out" in str(exc).lower() else "completed_within_limit"
            error_details = [str(exc)[:500]]
            receipt_ref = None
            try:
                receipt_ref = self._write_receipt(request, config, started=started, result_state="failed", validation_result="failed", timeout_state=timeout_state, cancellation_state="requested" if metadata.get("cancel_requested") else "not_requested", actual_model=actual_model, prompt=prompt, artifacts=[], errors=error_details, endpoint_local=True)
            except Exception as receipt_error:
                receipt_ref = None
                error_details.append(f"failure receipt persistence failed: {str(receipt_error)[:400]}")
            artifacts = [receipt_ref] if receipt_ref else []
            return ExecutionProviderAdapterResult(adapter_request_id=request.adapter_request_id, dispatch_id=request.dispatch_id, provider_id=PROVIDER_ID, status="failed", started_at=started, finished_at=utc_now(), summary="Qwen local provider invocation failed closed.", artifacts=artifacts, validation_status="failed", errors=error_details, metadata={"adapter_id": ADAPTER_ID, "adapter_version": ADAPTER_VERSION, "provider_receipt": receipt_ref, "receipt_reference": receipt_ref, "actual_model_identity": actual_model, "live_provider_called": True, "endpoint_local": True})
