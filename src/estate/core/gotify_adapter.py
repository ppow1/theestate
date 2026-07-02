"""Gotify transport adapter for Notification Router recall events.

This module is intentionally bounded to Gotify delivery. It consumes records
emitted by the transport-independent notification router after Alfred has made
its recall assessment, maps eligible recall notifications to a concise Gotify
payload, and records a token-safe delivery report.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib import error, request

from estate.core.paths import ESTATE_ROOT

REPORT_PATH = "runtime/notifications/gotify_delivery_report.json"
TITLE = "Estate Recall"
GOTIFY_URL_ENV = "ESTATE_GOTIFY_URL"
GOTIFY_TOKEN_ENV = "ESTATE_GOTIFY_TOKEN"


class GotifyTransportError(RuntimeError):
    """Raised when Gotify transport delivery fails."""


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def estate_root(root=None):
    if root is not None:
        return Path(root)
    if ESTATE_ROOT.exists():
        return ESTATE_ROOT
    return Path.cwd()


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _config_from_env(env=None):
    env = env or os.environ
    return {
        "url": (env.get(GOTIFY_URL_ENV) or "").rstrip("/"),
        "token": env.get(GOTIFY_TOKEN_ENV) or "",
    }


def gotify_priority(router_priority):
    value = str(router_priority or "normal").lower()
    if value in {"urgent", "high", "critical", "recall"}:
        return 8
    if value in {"low", "info", "informational"}:
        return 2
    return 5


def recall_event_to_gotify_payload(notification):
    reason = notification.get("reason") or notification.get("audit", {}).get("primary_recall_reason") or "unspecified"
    requested_by = notification.get("requested_by") or "unknown"
    action = notification.get("action") or "prepare_recall_delivery"
    return {
        "title": TITLE,
        "priority": gotify_priority(notification.get("priority")),
        "message": f"Recall Steward. reason={reason}; requested_by={requested_by}; action={action}",
    }


def _redact_token(text, config):
    token = config.get("token") or ""
    if token and token in str(text):
        return str(text).replace(token, "[REDACTED]")
    return str(text)


def _safe_status(config, dry_run):
    missing = []
    if not config.get("url"):
        missing.append(GOTIFY_URL_ENV)
    if not config.get("token"):
        missing.append(GOTIFY_TOKEN_ENV)
    if not missing:
        return None
    return {
        "ok": False,
        "status": "warning" if dry_run else "failed",
        "reason": "missing_configuration",
        "message": f"Missing Gotify configuration: {', '.join(missing)}",
        "missing": missing,
    }


def _post_to_gotify(config, payload, timeout=10):
    body = json.dumps(payload).encode("utf-8")
    url = f"{config['url']}/message?token={config['token']}"
    req = request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with request.urlopen(req, timeout=timeout) as response:  # noqa: S310 - configured local Gotify endpoint
            return {"status_code": response.getcode(), "body": response.read().decode("utf-8", errors="replace")[:200]}
    except (error.URLError, error.HTTPError, TimeoutError) as exc:
        raise GotifyTransportError(str(exc)) from exc


def send_gotify_recall(notification, *, dry_run=False, env=None, transport=None, root=None, write_report=True):
    """Send one Notification Router recall record to Gotify.

    Missing config is a dry-run warning and a controlled real-send failure.
    The returned report never includes the Gotify token.
    """
    config = _config_from_env(env)
    payload = recall_event_to_gotify_payload(notification or {})
    warnings = []
    attempts = []
    started_at = _now()

    if (notification or {}).get("class") != "recall" or not (notification or {}).get("eligible_for_immediate_delivery"):
        result = {
            "version": 1,
            "generated_at": started_at,
            "ok": False,
            "status": "skipped",
            "dry_run": dry_run,
            "reason": "not_recall_delivery_eligible",
            "payload": payload,
            "attempts": attempts,
            "warnings": warnings,
        }
        if write_report:
            _write_json(estate_root(root) / REPORT_PATH, result)
        return result

    missing_status = _safe_status(config, dry_run)
    if missing_status:
        warnings.append({"type": "missing_configuration", "message": missing_status["message"], "missing": missing_status["missing"]})
        result = {
            "version": 1,
            "generated_at": started_at,
            "ok": bool(dry_run),
            "status": missing_status["status"],
            "dry_run": dry_run,
            "reason": missing_status["reason"],
            "payload": payload,
            "attempts": attempts,
            "warnings": warnings,
            "configured_url": bool(config.get("url")),
            "configured_token": bool(config.get("token")),
        }
        if write_report:
            _write_json(estate_root(root) / REPORT_PATH, result)
        return result

    if dry_run:
        result = {
            "version": 1,
            "generated_at": started_at,
            "ok": True,
            "status": "dry_run",
            "dry_run": True,
            "reason": "validated_without_delivery",
            "payload": payload,
            "attempts": [],
            "warnings": warnings,
            "configured_url": True,
            "configured_token": True,
        }
        if write_report:
            _write_json(estate_root(root) / REPORT_PATH, result)
        return result

    sender = transport or _post_to_gotify
    last_error = None
    for attempt_number in (1, 2):
        try:
            response = sender(config, payload)
            attempts.append({"attempt": attempt_number, "ok": True})
            result = {
                "version": 1,
                "generated_at": started_at,
                "ok": True,
                "status": "sent",
                "dry_run": False,
                "reason": "delivered",
                "payload": payload,
                "attempts": attempts,
                "warnings": warnings,
                "gotify_response": {"status_code": response.get("status_code")} if isinstance(response, dict) else {},
                "configured_url": True,
                "configured_token": True,
            }
            if write_report:
                _write_json(estate_root(root) / REPORT_PATH, result)
            return result
        except Exception as exc:  # transport boundary: retry once then report controlled failure
            last_error = _redact_token(exc, config)
            attempts.append({"attempt": attempt_number, "ok": False, "error": last_error})

    result = {
        "version": 1,
        "generated_at": started_at,
        "ok": False,
        "status": "failed",
        "dry_run": False,
        "reason": "transport_failure",
        "payload": payload,
        "attempts": attempts,
        "warnings": warnings,
        "error": last_error,
        "configured_url": True,
        "configured_token": True,
    }
    if write_report:
        _write_json(estate_root(root) / REPORT_PATH, result)
    return result


def format_gotify_delivery_report(report):
    return "\n".join([
        "Gotify Adapter v1",
        f"Status: {report.get('status')}",
        f"Dry run: {report.get('dry_run')}",
        f"Reason: {report.get('reason')}",
        f"Attempts: {len(report.get('attempts', []))}",
    ])
