"""Natural-language Grace local image assignment intake."""
from __future__ import annotations

import hashlib
import os
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from estate.core.grace_comfyui_execution import build_sdxl_workflow
from estate.core.grace_momentum_service import LoopbackGraceMomentumClient


def detect_grace_image_assignment(model: str | None, user_message: str) -> bool:
    text = str(user_message or "").lower()
    return model in {"estate/grace", "estate/grace-grounded-test"} and "generate" in text and any(
        word in text for word in ("image", "headshot", "portrait")
    )


def execute_grace_image_assignment(
    payload: dict[str, Any],
    *,
    user_message: str,
    session_id: str | None = None,
) -> dict[str, Any]:
    assignment_key = hashlib.sha256(
        (session_id or "").encode("utf-8") + user_message.encode("utf-8")
    ).hexdigest()[:20]
    seed = int(assignment_key[:12], 16)
    checkpoint = os.environ.get(
        "ESTATE_COMFYUI_CHECKPOINT",
        "CyberRealisticXLPlay_V10.0_FP16.safetensors",
    )
    workflow = build_sdxl_workflow(
        user_message,
        checkpoint=checkpoint,
        seed=seed,
        filename_prefix=f"estate/grace/openwebui/{assignment_key}",
    )
    now = datetime.now(timezone.utc).isoformat()
    command = {
        "schema_version": "estate.grace-momentum-control.v1",
        "command_id": "command-" + uuid4().hex,
        "correlation_id": "openwebui-" + (session_id or assignment_key),
        "causation_id": "openwebui-chat-" + assignment_key,
        "idempotency_key": "grace-image-" + assignment_key,
        "timestamp": now,
        "action": "assignment.execute_local",
        "title": "Grace local image assignment",
        "summary": user_message,
        "task_input": {
            "workflow": workflow,
            "requested_prompt": user_message,
            "checkpoint": checkpoint,
        },
        "adapter_id": "comfyui.local.image",
        "source": "openwebui/grace-grounded-test",
    }
    metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
    claims = {
        "iss": "estate-control",
        "sub": str(metadata.get("user_id") or "openwebui-grace"),
        "office": "Grace",
        "authority_source": "openwebui/grace-assignment",
        "active": True,
    }
    endpoint = os.environ.get("ESTATE_GRACE_MOMENTUM_URL", "http://127.0.0.1:8766")
    client = LoopbackGraceMomentumClient(endpoint, claims, timeout_seconds=960.0)
    return client.send(command)
