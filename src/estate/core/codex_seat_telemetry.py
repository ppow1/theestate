"""Read-only per-seat Codex rate-limit telemetry.

The installed Codex CLI's TUI obtains ``/status`` rate limits through the
app-server ``account/rateLimits/read`` JSON-RPC method.  This module uses that
same structured request under an explicitly selected CODEX_HOME.  It never
starts a thread or turn and never performs login, logout, or reset operations.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import threading
import time
from queue import Empty, Queue
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Sequence

from estate.core.codex_bridge import CODEX_SEAT_HOMES
from estate.core.paths import ESTATE_ROOT

TELEMETRY_JSON = Path("runtime/engineering_capacity/codex_seat_telemetry.json")
CODEX_SEATS = tuple(CODEX_SEAT_HOMES)
WEEKLY_WINDOW_MINUTES = 7 * 24 * 60
RpcRunner = Callable[..., subprocess.CompletedProcess[str]]


def _root(root: str | Path | None = None) -> Path:
    return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _iso_from_epoch(value: Any) -> str | None:
    if not isinstance(value, (int, float)):
        return None
    try:
        return datetime.fromtimestamp(value, timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    except (OverflowError, OSError, ValueError):
        return None


def _rpc_lines() -> str:
    return "\n".join(
        [
            json.dumps({"method": "initialize", "id": 1, "params": {"clientInfo": {"name": "estate-seat-telemetry", "title": "Estate seat telemetry", "version": "1"}}}),
            json.dumps({"method": "initialized", "params": {}}),
            json.dumps({"method": "account/read", "id": 2, "params": {"refreshToken": False}}),
            json.dumps({"method": "account/rateLimits/read", "id": 3}),
            "",
        ]
    )


def _child_environment(seat_id: str) -> dict[str, str]:
    if seat_id not in CODEX_SEAT_HOMES:
        raise ValueError(f"unknown Codex seat: {seat_id}")
    environment = os.environ.copy()
    environment["CODEX_HOME"] = str(CODEX_SEAT_HOMES[seat_id])
    return environment


def _response_lines(stdout: str) -> dict[int, dict[str, Any]]:
    responses: dict[int, dict[str, Any]] = {}
    for line in stdout.splitlines():
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and isinstance(value.get("id"), int):
            responses[value["id"]] = value
    return responses


def _run_app_server_stream(command: list[str], *, environment: dict[str, str], timeout_seconds: int) -> subprocess.CompletedProcess[str]:
    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=environment,
    )
    output: Queue[str | None] = Queue()

    def read_output() -> None:
        assert process.stdout is not None
        for line in process.stdout:
            output.put(line)
        output.put(None)

    reader = threading.Thread(target=read_output, daemon=True)
    reader.start()
    assert process.stdin is not None
    for line in _rpc_lines().splitlines():
        process.stdin.write(line + "\n")
        process.stdin.flush()

    lines: list[str] = []
    deadline = time.monotonic() + timeout_seconds
    try:
        while time.monotonic() < deadline:
            try:
                line = output.get(timeout=0.25)
            except Empty:
                continue
            if line is None:
                break
            lines.append(line)
            try:
                if json.loads(line).get("id") == 3:
                    break
            except json.JSONDecodeError:
                continue
    finally:
        try:
            process.stdin.close()
        except OSError:
            pass
        if process.poll() is None:
            process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=2)
        if process.stdout:
            process.stdout.close()
        if process.stderr:
            process.stderr.close()
    return subprocess.CompletedProcess(command, process.returncode, "".join(lines), "")


def _native_snapshots(rate_limits: dict[str, Any]) -> list[dict[str, Any]]:
    snapshots: list[dict[str, Any]] = []
    by_limit_id = rate_limits.get("rateLimitsByLimitId") or {}
    if isinstance(by_limit_id, dict):
        for limit_id, snapshot in by_limit_id.items():
            if isinstance(snapshot, dict):
                snapshots.append({"limit_id": limit_id, **snapshot})
    if not snapshots and isinstance(rate_limits.get("rateLimits"), dict):
        snapshots.append({"limit_id": rate_limits["rateLimits"].get("limitId", "codex"), **rate_limits["rateLimits"]})
    return snapshots


def _display_windows(snapshots: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    windows: list[dict[str, Any]] = []
    for snapshot in snapshots:
        for window_name in ("primary", "secondary"):
            native = snapshot.get(window_name)
            if not isinstance(native, dict):
                continue
            used = native.get("usedPercent")
            remaining = 100 - used if isinstance(used, (int, float)) else None
            windows.append(
                {
                    "limit_id": snapshot.get("limit_id"),
                    "window": window_name,
                    "window_minutes": native.get("windowDurationMins"),
                    "used_percent": used,
                    "remaining_percent": remaining,
                    "resets_at_epoch": native.get("resetsAt"),
                    "resets_at": _iso_from_epoch(native.get("resetsAt")),
                }
            )
    return windows


def _unavailable(seat_id: str, observed_at: str, reason: str, account: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "seat_id": seat_id,
        "capacity_identity": f"codex.seat.{seat_id}",
        "execution_modes": ["cli"],
        "execution_surface": "codex-cli",
        "codex_home": str(CODEX_SEAT_HOMES[seat_id]),
        "source": "codex app-server account/rateLimits/read",
        "observed_at": None,
        "collection_attempted_at": observed_at,
        "collection_status": "unavailable",
        "failure_reason": reason,
        "account": account or {},
        "native_rate_limits": {},
        "windows": [],
        "weekly_limit_percent_left": None,
        "weekly_limit_reset_at": None,
    }


def collect_codex_seat(
    seat_id: str,
    *,
    codex_binary: str | None = None,
    timeout_seconds: int = 20,
    run_process: RpcRunner | None = None,
    observed_at: str | None = None,
) -> dict[str, Any]:
    """Collect one seat's native rate-limit snapshot without model execution."""
    if seat_id not in CODEX_SEAT_HOMES:
        raise ValueError(f"unknown Codex seat: {seat_id}")
    attempted_at = observed_at or _utc_now()
    binary = codex_binary or shutil.which("codex") or "codex"
    runner = run_process
    try:
        command = [binary, "app-server", "--stdio"]
        environment = _child_environment(seat_id)
        completed = runner(
            command,
            input=_rpc_lines(),
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
            env=environment,
        ) if runner else _run_app_server_stream(command, environment=environment, timeout_seconds=timeout_seconds)
    except (OSError, subprocess.TimeoutExpired):
        return _unavailable(seat_id, attempted_at, "app-server process failed or timed out")

    responses = _response_lines(completed.stdout or "")
    account_response = responses.get(2, {})
    account_value = account_response.get("result", {}).get("account") if isinstance(account_response.get("result"), dict) else None
    account = {
        "type": account_value.get("type"),
        "plan_type": account_value.get("planType"),
    } if isinstance(account_value, dict) else {}
    rate_response = responses.get(3, {})
    if not isinstance(rate_response.get("result"), dict):
        return _unavailable(seat_id, attempted_at, "account/rateLimits/read returned no rate-limit result", account)

    rate_result = rate_response["result"]
    snapshots = _native_snapshots(rate_result)
    windows = _display_windows(snapshots)
    weekly = next((window for window in windows if window.get("window_minutes") == WEEKLY_WINDOW_MINUTES), None)
    if weekly is None:
        return {
            **_unavailable(seat_id, attempted_at, "no weekly rate-limit window was returned", account),
            "native_rate_limits": rate_result,
            "windows": windows,
        }
    return {
        "seat_id": seat_id,
        "capacity_identity": f"codex.seat.{seat_id}",
        "execution_modes": ["cli"],
        "execution_surface": "codex-cli",
        "codex_home": str(CODEX_SEAT_HOMES[seat_id]),
        "source": "codex app-server account/rateLimits/read",
        "observed_at": attempted_at,
        "collection_attempted_at": attempted_at,
        "collection_status": "available",
        "failure_reason": None,
        "account": account,
        "native_rate_limits": rate_result,
        "windows": windows,
        "weekly_limit_percent_left": weekly.get("remaining_percent"),
        "weekly_limit_reset_at": weekly.get("resets_at"),
    }


def collect_codex_seat_telemetry(
    *,
    root: str | Path | None = None,
    seats: Sequence[str] = CODEX_SEATS,
    codex_binary: str | None = None,
    timeout_seconds: int = 20,
    run_process: RpcRunner | None = None,
    write: bool = True,
) -> dict[str, Any]:
    root_path = _root(root)
    observations = [
        collect_codex_seat(seat, codex_binary=codex_binary, timeout_seconds=timeout_seconds, run_process=run_process)
        for seat in seats
    ]
    if write:
        previous_by_seat: dict[str, dict[str, Any]] = {}
        previous_path = root_path / TELEMETRY_JSON
        try:
            previous = json.loads(previous_path.read_text(encoding="utf-8"))
            previous_by_seat = {
                item.get("seat_id"): item
                for item in previous.get("seats", [])
                if isinstance(item, dict) and item.get("seat_id") in CODEX_SEAT_HOMES
            }
        except (OSError, json.JSONDecodeError):
            previous_by_seat = {}
        for index, observation in enumerate(observations):
            if observation.get("collection_status") == "available":
                continue
            previous_observation = previous_by_seat.get(observation.get("seat_id")) or {}
            if previous_observation.get("weekly_limit_percent_left") is None or not previous_observation.get("observed_at"):
                continue
            observations[index] = {
                **previous_observation,
                "collection_attempted_at": observation.get("collection_attempted_at"),
                "collection_status": "stale",
                "failure_reason": observation.get("failure_reason") or "refresh failed; retaining last valid observation",
                "last_collection_status": "unavailable",
                "last_failure_reason": observation.get("failure_reason"),
            }
    payload = {
        "version": 1,
        "generated_at": _utc_now(),
        "source": "codex app-server account/rateLimits/read",
        "read_only": True,
        "does_not_start_turns": True,
        "does_not_modify_authentication": True,
        "seats": observations,
    }
    if write:
        path = root_path / TELEMETRY_JSON
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def format_codex_seat_telemetry(payload: dict[str, Any]) -> str:
    lines = ["# Codex Seat Fuel Telemetry", "", f"Generated: {payload.get('generated_at')}", ""]
    for seat in payload.get("seats") or []:
        lines.append(
            f"- {seat.get('seat_id')}: status={seat.get('collection_status')}; weekly_left={seat.get('weekly_limit_percent_left') if seat.get('weekly_limit_percent_left') is not None else 'unknown'}; reset={seat.get('weekly_limit_reset_at') or 'unknown'}; observed={seat.get('observed_at') or 'unknown'}; reason={seat.get('failure_reason') or 'none'}"
        )
    return "\n".join(lines) + "\n"
