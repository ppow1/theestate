"""Runtime artifact helpers for the execution provider adapter contract."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from estate.core.execution_provider_adapter import (
    DeterministicDryRunExecutionProviderAdapter,
    ExecutionProviderAdapterRequest,
    ExecutionProviderAdapterResult,
    utc_now,
)
from estate.core.paths import ESTATE_ROOT

RUNTIME_DIR = Path("runtime/execution_adapters")
REQUESTS_DIR = RUNTIME_DIR / "requests"
RESULTS_DIR = RUNTIME_DIR / "results"
STATUS_DIR = RUNTIME_DIR / "status"
LATEST_STATUS = STATUS_DIR / "latest.json"
SUMMARY_STATUS = STATUS_DIR / "summary.json"


def _root(root: str | Path | None = None) -> Path:
    if root is not None:
        return Path(root)
    return ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd()


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def write_adapter_request(request: ExecutionProviderAdapterRequest, root: str | Path | None = None) -> Path:
    return _write_json(_root(root) / REQUESTS_DIR / f"{request.adapter_request_id}.json", request.to_dict())


def load_adapter_request(path: str | Path) -> ExecutionProviderAdapterRequest:
    return ExecutionProviderAdapterRequest.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def write_adapter_result(result: ExecutionProviderAdapterResult, root: str | Path | None = None) -> Path:
    return _write_json(_root(root) / RESULTS_DIR / f"{result.adapter_request_id}.json", result.to_dict())


def load_adapter_result(path: str | Path) -> ExecutionProviderAdapterResult:
    return ExecutionProviderAdapterResult(**json.loads(Path(path).read_text(encoding="utf-8")))


def write_status_artifacts(result: ExecutionProviderAdapterResult, root: str | Path | None = None) -> dict[str, str]:
    base = _root(root)
    latest = result.to_dict()
    latest["updated_at"] = utc_now()
    summary = {
        "updated_at": latest["updated_at"],
        "latest_adapter_request_id": result.adapter_request_id,
        "latest_dispatch_id": result.dispatch_id,
        "latest_provider_id": result.provider_id,
        "latest_status": result.status,
        "latest_validation_status": result.validation_status,
        "blocked_count": 1 if result.status == "blocked" else 0,
        "failed_count": 1 if result.status == "failed" else 0,
        "live_provider_called": bool(result.metadata.get("live_provider_called", False)),
    }
    latest_path = _write_json(base / LATEST_STATUS, latest)
    summary_path = _write_json(base / SUMMARY_STATUS, summary)
    return {"latest_status_path": str(latest_path), "summary_status_path": str(summary_path)}


def validate_adapter_request_file(path: str | Path) -> dict[str, Any]:
    request = load_adapter_request(path)
    validation = request.validate()
    return {"request": request.to_dict(), "validation": validation.to_dict()}


def run_dry_run_adapter(request: ExecutionProviderAdapterRequest, root: str | Path | None = None) -> dict[str, Any]:
    request_path = write_adapter_request(request, root=root)
    adapter = DeterministicDryRunExecutionProviderAdapter(provider_id=request.provider_id, provider_type=request.provider_type)
    result = adapter.dry_run(request)
    result_path = write_adapter_result(result, root=root)
    status_paths = write_status_artifacts(result, root=root)
    payload = result.to_dict()
    payload.update({"request_path": str(request_path), "result_path": str(result_path), **status_paths})
    return payload


def load_registered_adapter(request: ExecutionProviderAdapterRequest, *, root: str | Path | None = None, bridge_runner: Any = None):
    """Resolve only adapters registered in the canonical provider catalog seam."""
    from estate.core.codex_bridge_execution_provider_adapter import CodexCliExecutionProviderAdapter
    from estate.core.qwen_local_text_execution_provider_adapter import QwenLocalTextExecutionProviderAdapter
    from estate.core.provider_catalog import load_provider_catalog

    catalog = load_provider_catalog(_root(root) / "config" / "providers" / "catalog.json")
    provider = catalog.get_provider(request.provider_id)
    if provider.status not in {"implemented", "operationally_validated", "institutionalized"}:
        raise ValueError(f"provider '{request.provider_id}' is not registered for execution: {provider.status}")
    if request.provider_id == "codex.execution.cli":
        return CodexCliExecutionProviderAdapter(root=_root(root), bridge_runner=bridge_runner)
    if request.provider_id == "qwen.local.text":
        return QwenLocalTextExecutionProviderAdapter(root=_root(root))
    raise ValueError(f"no concrete adapter registered for provider '{request.provider_id}'")
