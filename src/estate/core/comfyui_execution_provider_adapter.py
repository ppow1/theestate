"""Non-submitting ComfyUI provider adapter for governed request preparation."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from estate.core.comfyui_provider_health import DEFAULT_ENDPOINT, PROVIDER_ID, validate_loopback_endpoint
from estate.core.execution_provider_adapter import ExecutionProviderAdapter, ExecutionProviderAdapterRequest, ExecutionProviderAdapterResult, utc_now


class ComfyUIExecutionProviderAdapter(ExecutionProviderAdapter):
    adapter_id = "comfyui-local-request-preparation-v1"
    provider_id = PROVIDER_ID
    provider_type = "media"

    def prepare_workflow_request(self, request: ExecutionProviderAdapterRequest) -> dict[str, Any]:
        validation = self.validate_request(request)
        if not validation.ok:
            raise ValueError("adapter request is invalid: " + "; ".join(validation.errors))
        if not self.supports(request):
            raise ValueError("request is not for the admitted local ComfyUI provider")
        metadata = request.metadata or {}
        validate_loopback_endpoint(str(metadata.get("endpoint") or DEFAULT_ENDPOINT))
        required = metadata.get("required_capabilities") or []
        if "image_generation" not in required and "image_iteration" not in required:
            raise ValueError("ComfyUI request requires image_generation or image_iteration capability")
        workflow = metadata.get("workflow")
        if not isinstance(workflow, dict) or not workflow:
            raise ValueError("ComfyUI workflow must be a non-empty object")
        canonical = json.dumps(workflow, sort_keys=True, separators=(",", ":"))
        return {"schema_version": "estate.comfyui-prepared-request.v1", "adapter_id": self.adapter_id,
                "adapter_request_id": request.adapter_request_id, "dispatch_id": request.dispatch_id, "provider_id": self.provider_id,
                "endpoint": str(metadata.get("endpoint") or DEFAULT_ENDPOINT), "workflow": json.loads(canonical),
                "workflow_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(), "live_provider_called": False,
                "workflow_submitted": False, "image_generated": False, "validation_required": request.validation_required,
                "chief_architect_acceptance_required": True, "acceptance_granted": False}

    def dry_run(self, request: ExecutionProviderAdapterRequest) -> ExecutionProviderAdapterResult:
        started = utc_now()
        try:
            prepared = self.prepare_workflow_request(request)
            return ExecutionProviderAdapterResult(adapter_request_id=request.adapter_request_id, dispatch_id=request.dispatch_id, provider_id=self.provider_id,
                status="dry_run_completed", started_at=started, finished_at=utc_now(), summary="ComfyUI workflow request prepared and validated without submission.",
                artifacts=["prepared://" + prepared["workflow_sha256"]], validation_status="passed",
                metadata={"prepared_request": prepared, "live_provider_called": False, "workflow_submitted": False, "image_generated": False, "acceptance_granted": False})
        except ValueError as exc:
            return ExecutionProviderAdapterResult(adapter_request_id=request.adapter_request_id, dispatch_id=request.dispatch_id, provider_id=self.provider_id,
                status="blocked", started_at=started, finished_at=utc_now(), summary=str(exc), artifacts=["blocked://comfyui-request-validation"], validation_status="failed",
                errors=[str(exc)], metadata={"live_provider_called": False, "workflow_submitted": False, "image_generated": False, "acceptance_granted": False})

    def submit(self, request: ExecutionProviderAdapterRequest) -> ExecutionProviderAdapterResult:
        return ExecutionProviderAdapterResult(adapter_request_id=request.adapter_request_id, dispatch_id=request.dispatch_id, provider_id=self.provider_id,
            status="blocked", started_at=utc_now(), finished_at=utc_now(), summary="ComfyUI workflow submission is not authorized by provider admission.",
            artifacts=["blocked://comfyui-live-submission-not-authorized"], validation_status="not_run",
            errors=["live workflow submission requires separate explicit authorization"],
            metadata={"live_provider_called": False, "workflow_submitted": False, "image_generated": False, "acceptance_granted": False})
