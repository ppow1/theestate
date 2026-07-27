"""Read-only, loopback-only ComfyUI capacity qualification.

Only ``GET /queue`` is allowed.  Queue contents are never persisted; the
canonical capacity record contains only running and pending counts.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from estate.core.comfyui_provider_health import PROVIDER_ID, REQUIRED_CAPABILITIES
from estate.core.provider_capacity import ProviderCapacityRecord, latest_capacity_by_provider, write_capacity_record
from estate.core.provider_catalog import load_provider_catalog
from estate.core.provider_health import latest_health_by_provider

DEFAULT_CAPACITY_ENDPOINT = "http://127.0.0.1:8188/queue"
QUALIFYING_CAPACITY_STATES = {"idle", "available"}


def _utc_now() -> datetime:
    # Capacity probes can legitimately run more than once per second.  Keep
    # microseconds so the canonical latest-record reader has an unambiguous
    # ordering without altering its shared storage contract.
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def validate_capacity_endpoint(endpoint: str) -> str:
    parsed = urlparse(endpoint)
    if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError("ComfyUI capacity endpoint must be loopback-only HTTP")
    if parsed.path != "/queue" or parsed.params or parsed.query or parsed.fragment:
        raise ValueError("ComfyUI capacity endpoint must be exactly /queue")
    return endpoint


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        return None


def _default_fetch(method: str, endpoint: str, timeout_seconds: float) -> tuple[int, bytes, str]:
    request = Request(endpoint, method=method, headers={"Accept": "application/json"})
    opener = build_opener(_NoRedirect())
    try:
        with opener.open(request, timeout=timeout_seconds) as response:
            return int(response.status), response.read(), response.geturl()
    except HTTPError as exc:
        return int(exc.code), b"", endpoint


def _fresh_available_health(root: Path, now: datetime) -> bool:
    health = latest_health_by_provider(root).get(PROVIDER_ID)
    if not health or health.status != "available":
        return False
    expiry = _parse_iso(health.expires_at)
    return bool(expiry and expiry > now and set(REQUIRED_CAPABILITIES).issubset(health.capabilities_available))


def probe_comfyui_capacity(*, root: Path, endpoint: str = DEFAULT_CAPACITY_ENDPOINT, timeout_seconds: float = 2.0,
                           freshness_seconds: int = 300,
                           fetch: Callable[[str, str, float], tuple[int, bytes, str]] | None = None) -> dict[str, Any]:
    """Write one canonical capacity observation without selecting or executing a provider."""
    validate_capacity_endpoint(endpoint)
    if timeout_seconds <= 0 or timeout_seconds > 10:
        raise ValueError("timeout_seconds must be greater than zero and at most ten")
    if freshness_seconds <= 0:
        raise ValueError("freshness_seconds must be greater than zero")
    checked = _utc_now()
    expires = checked + timedelta(seconds=freshness_seconds)
    state, availability, message, active, pending, malformed, endpoint_reachable = "unknown", "unknown", "ComfyUI capacity evidence is unavailable.", 0, 0, False, False
    try:
        status_code, body, final_url = (fetch or _default_fetch)("GET", endpoint, timeout_seconds)
        validate_capacity_endpoint(final_url)
        endpoint_reachable = True
        if status_code != 200:
            availability, message = "unavailable", f"ComfyUI queue endpoint returned HTTP {status_code}."
        else:
            payload = json.loads(body.decode("utf-8"))
            running = payload.get("queue_running") if isinstance(payload, dict) else None
            queued = payload.get("queue_pending") if isinstance(payload, dict) else None
            if not isinstance(running, list) or not isinstance(queued, list):
                malformed, message = True, "ComfyUI queue response lacks list-valued queue_running and queue_pending evidence."
            else:
                active, pending = len(running), len(queued)
                if not _fresh_available_health(root, checked):
                    message = "ComfyUI queue observed, but fresh available health evidence is required before capacity can qualify."
                elif active or pending:
                    state, availability, message = "busy", "reachable", "ComfyUI has active or pending queue work."
                else:
                    state, availability, message = "available", "reachable", "ComfyUI has no active or pending queue work and fresh health evidence is available."
    except (OSError, TimeoutError, ValueError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        availability, message = "unavailable", f"ComfyUI queue endpoint unavailable or invalid: {type(exc).__name__}."
    metadata = {
        "service_id": "comfyui", "endpoint": endpoint, "probe_method": "GET", "probe_path": "/queue",
        "availability": availability, "response_malformed": malformed, "endpoint_reachable": endpoint_reachable,
        "fresh_health_required": True, "provider_admitted": True, "provider_selected": False,
        "live_execution_authorized": False, "workflow_submitted": False, "image_generated": False,
        "expires_at": _iso(expires), "queue_contents_persisted": False,
    }
    record = ProviderCapacityRecord.create(provider_id=PROVIDER_ID, capacity_state=state, reported_by="ComfyUI loopback capacity probe",
                                           active_jobs=active, queue_depth=pending, message=message, metadata=metadata)
    record.checked_at = _iso(checked)
    paths = write_capacity_record(record, root=root)
    return {"provider_id": PROVIDER_ID, "endpoint": endpoint, "capacity_state": state, "availability": availability,
            "active_jobs": active, "queue_depth": pending, "checked_at": record.checked_at, "expires_at": _iso(expires),
            "response_malformed": malformed, "endpoint_reachable": endpoint_reachable,
            "paths": {key: str(value) if value else None for key, value in paths.items()},
            "live_provider_called": False, "workflow_submitted": False, "image_generated": False, "acceptance_granted": False}


def has_fresh_qualifying_capacity(*, root: Path, now: datetime | None = None) -> bool:
    record = latest_capacity_by_provider(root).get(PROVIDER_ID)
    if not record or record.capacity_state not in QUALIFYING_CAPACITY_STATES:
        return False
    expiry = _parse_iso((record.metadata or {}).get("expires_at"))
    return bool(expiry and expiry > (now or _utc_now()))


def evaluate_comfyui_selection_eligibility(*, root: Path, required_capability: str, privacy_cleared: bool = False,
                                            egress_cleared: bool = False, authority_granted: bool = False,
                                            dispatch_authorized: bool = False, now: datetime | None = None) -> dict[str, Any]:
    """Evaluate gates only; this never selects, reserves, dispatches, or executes."""
    reasons: list[str] = []
    try:
        provider = load_provider_catalog(root / "config/providers/catalog.json").get_provider(PROVIDER_ID)
        if required_capability not in provider.capabilities:
            reasons.append("required capability is not admitted for ComfyUI")
        if provider.cost_model != "no_spend_local":
            reasons.append("the no-spend local cost boundary is not evidenced")
        if provider.requires_network:
            reasons.append("the local-only network boundary is not evidenced")
    except (OSError, ValueError, KeyError):
        reasons.append("admitted provider descriptor is unavailable")
    current = now or _utc_now()
    if not _fresh_available_health(root, current):
        reasons.append("fresh available health evidence is required")
    if not has_fresh_qualifying_capacity(root=root, now=current):
        reasons.append("fresh idle or available capacity evidence is required")
    if not privacy_cleared:
        reasons.append("privacy clearance is required")
    if not egress_cleared:
        reasons.append("egress boundary clearance is required")
    if not authority_granted:
        reasons.append("Engineering selection authority is required")
    if not dispatch_authorized:
        reasons.append("Dispatch authorization is required")
    return {"provider_id": PROVIDER_ID, "required_capability": required_capability, "eligible": not reasons,
            "reasons": reasons or ["all selection gates are evidenced; this result still does not select a provider"],
            "provider_selected": False, "dispatch_created": False, "live_provider_called": False,
            "workflow_submitted": False, "image_generated": False, "acceptance_granted": False}
