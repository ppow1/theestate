"""Loopback-only, read-only ComfyUI health evidence.

This module never starts a service or submits a workflow.  Its only network
operation is a bounded GET to the manifest-defined ``/system_stats`` endpoint.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse
from urllib.request import urlopen

from estate.core.provider_capacity import ProviderCapacityRecord, latest_capacity_by_provider, write_capacity_record
from estate.core.provider_health import ProviderHealthRecord, latest_health_by_provider, write_health_record

PROVIDER_ID = "comfyui.local.image"
SERVICE_ID = "comfyui"
DEFAULT_ENDPOINT = "http://127.0.0.1:8188/system_stats"
REQUIRED_CAPABILITIES = ("image_generation", "image_iteration")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _iso(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def validate_loopback_endpoint(endpoint: str) -> str:
    parsed = urlparse(endpoint)
    if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError("ComfyUI endpoint must be loopback-only HTTP")
    if parsed.path != "/system_stats" or parsed.params or parsed.query or parsed.fragment:
        raise ValueError("ComfyUI health endpoint must be exactly /system_stats")
    return endpoint


def _default_fetch(endpoint: str, timeout_seconds: float) -> tuple[int, bytes]:
    with urlopen(endpoint, timeout=timeout_seconds) as response:  # nosec B310: endpoint is validated loopback-only
        return int(response.status), response.read()


def probe_comfyui_health(*, root: Path, endpoint: str = DEFAULT_ENDPOINT, timeout_seconds: float = 2.0,
                         freshness_seconds: int = 300, fetch: Callable[[str, float], tuple[int, bytes]] | None = None) -> dict[str, Any]:
    """Perform the one permitted read-only health request and write canonical evidence."""
    validate_loopback_endpoint(endpoint)
    if timeout_seconds <= 0 or timeout_seconds > 10:
        raise ValueError("timeout_seconds must be greater than zero and at most ten")
    if freshness_seconds <= 0:
        raise ValueError("freshness_seconds must be greater than zero")
    checked = _utc_now()
    expires = checked + timedelta(seconds=freshness_seconds)
    status = "offline"
    message = "ComfyUI endpoint unreachable."
    payload: dict[str, Any] | None = None
    malformed = False
    try:
        code, body = (fetch or _default_fetch)(endpoint, timeout_seconds)
        if code != 200:
            status, message = "offline", f"ComfyUI health endpoint returned HTTP {code}."
        else:
            decoded = json.loads(body.decode("utf-8"))
            if not isinstance(decoded, dict):
                malformed = True
                status, message = "degraded", "ComfyUI health endpoint returned malformed JSON evidence."
            else:
                payload = decoded
                status, message = "available", "ComfyUI loopback health endpoint reachable; no execution authority granted."
    except (OSError, TimeoutError, ValueError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        message = f"ComfyUI health endpoint unreachable or malformed: {type(exc).__name__}."
    metadata = {
        "service_id": SERVICE_ID,
        "endpoint": endpoint,
        "probe_method": "GET",
        "probe_path": "/system_stats",
        "endpoint_reachable": status == "available",
        "response_malformed": malformed,
        "provider_admitted": True,
        "live_execution_authorized": False,
        "provider_selected": False,
        "workflow_submitted": False,
        "image_generated": False,
    }
    health = ProviderHealthRecord.create(provider_id=PROVIDER_ID, status=status, reported_by="ComfyUI loopback health probe", message=message,
                                         source="comfyui_system_stats", expires_at=_iso(expires), capabilities_available=list(REQUIRED_CAPABILITIES) if status == "available" else [],
                                         capabilities_unavailable=[] if status == "available" else list(REQUIRED_CAPABILITIES), metadata=metadata)
    health.checked_at = _iso(checked)
    health_paths = write_health_record(health, root=root)
    capacity = ProviderCapacityRecord.create(provider_id=PROVIDER_ID, capacity_state="unknown", reported_by="ComfyUI loopback health probe",
                                             message="Health probing does not inspect queue depth or reserve capacity.", metadata={**metadata, "capacity_observed": False})
    capacity.checked_at = _iso(checked)
    capacity_paths = write_capacity_record(capacity, root=root)
    return {"provider_id": PROVIDER_ID, "endpoint": endpoint, "health_status": status, "endpoint_reachable": status == "available", "response_malformed": malformed,
            "checked_at": health.checked_at, "expires_at": health.expires_at, "system_stats": payload, "health_paths": {k: str(v) if v else None for k, v in health_paths.items()},
            "capacity_paths": {k: str(v) if v else None for k, v in capacity_paths.items()}, "live_provider_called": False,
            "workflow_submitted": False, "image_generated": False, "provider_selected": False}


def has_fresh_comfyui_evidence(*, root: Path, now: datetime | None = None) -> bool:
    record = latest_health_by_provider(root).get(PROVIDER_ID)
    capacity = latest_capacity_by_provider(root).get(PROVIDER_ID)
    if not record or not capacity or record.status != "available" or capacity.capacity_state not in {"idle", "available"}:
        return False
    if not record.expires_at:
        return False
    expiry = datetime.fromisoformat(record.expires_at.replace("Z", "+00:00"))
    return expiry > (now or _utc_now())
