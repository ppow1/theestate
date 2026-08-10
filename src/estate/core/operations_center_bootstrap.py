"""Local server bootstrap for the Estate Operations Center.

This module starts, inspects, and stops the existing Steward command center HTTP
server. It is local-first only: it binds to loopback by default, stores no
secrets, and never executes work packages or changes command authority.
"""

from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

from estate.core.paths import ESTATE_ROOT
from estate.core.engineering_capacity_runtime import generate_engineering_capacity_dashboard
from estate.core.operations_center_settings import load_operations_center_settings
from estate.core.service_health_registry import generate_service_health_registry
from estate.core.steward_command_center import generate_command_center

PID_PATH = Path("runtime/steward/operations_center_server.pid")
LOG_PATH = Path("runtime/steward/operations_center_server.log")
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765


def _root(root: str | Path | None = None) -> Path:
    return Path(root) if root is not None else ESTATE_ROOT


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _pid_file(root: Path) -> Path:
    return root / PID_PATH


def _log_file(root: Path) -> Path:
    return root / LOG_PATH


def _read_pid(root: Path) -> dict[str, Any] | None:
    path = _pid_file(root)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"pid_file": str(PID_PATH), "pid_file_readable": False}


def _process_alive(pid: int | None) -> bool:
    if not pid:
        return False
    if os.name == "nt":
        return _windows_process_alive(pid)
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    proc_stat = Path(f"/proc/{pid}/stat")
    if proc_stat.exists():
        try:
            parts = proc_stat.read_text(encoding="utf-8").split()
            if len(parts) > 2 and parts[2] == "Z":
                return False
        except OSError:
            pass
    return True


def _windows_process_alive(pid: int) -> bool:
    import ctypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    handle = kernel32.OpenProcess(0x1000, False, int(pid))  # PROCESS_QUERY_LIMITED_INFORMATION
    if not handle:
        return ctypes.get_last_error() == 5  # access denied: retain ownership conservatively
    try:
        exit_code = ctypes.c_ulong()
        if not kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
            return True
        return exit_code.value == 259  # STILL_ACTIVE
    finally:
        kernel32.CloseHandle(handle)


def _windows_process_creation_token(pid: int) -> int | None:
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    handle = kernel32.OpenProcess(0x1000, False, int(pid))  # PROCESS_QUERY_LIMITED_INFORMATION
    if not handle:
        return None
    try:
        created = wintypes.FILETIME()
        exited = wintypes.FILETIME()
        kernel = wintypes.FILETIME()
        user = wintypes.FILETIME()
        if not kernel32.GetProcessTimes(handle, ctypes.byref(created), ctypes.byref(exited), ctypes.byref(kernel), ctypes.byref(user)):
            return None
        return (int(created.dwHighDateTime) << 32) | int(created.dwLowDateTime)
    finally:
        kernel32.CloseHandle(handle)


def _windows_process_matches_server(pid: int, pid_info: dict[str, Any]) -> bool:
    """Limit force termination to this server's executable and process instance."""
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    handle = kernel32.OpenProcess(0x1000, False, int(pid))  # PROCESS_QUERY_LIMITED_INFORMATION
    if not handle:
        return False
    try:
        size = wintypes.DWORD(32768)
        buffer = ctypes.create_unicode_buffer(size.value)
        if not kernel32.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)):
            return False
        expected_token = pid_info.get("windows_creation_token")
        actual_token = _windows_process_creation_token(pid)
        return bool(expected_token and actual_token == expected_token and os.path.normcase(os.path.abspath(buffer.value)) == os.path.normcase(os.path.abspath(sys.executable)))
    finally:
        kernel32.CloseHandle(handle)


def _windows_force_terminate(pid: int) -> bool:
    import ctypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    handle = kernel32.OpenProcess(0x0001, False, int(pid))  # PROCESS_TERMINATE
    if not handle:
        return False
    try:
        return bool(kernel32.TerminateProcess(handle, 1))
    finally:
        kernel32.CloseHandle(handle)


def _wait_for_process_exit(pid: int, timeout: float = 2.0) -> bool:
    deadline = time.monotonic() + timeout
    while _process_alive(pid) and time.monotonic() < deadline:
        time.sleep(0.1)
    return not _process_alive(pid)


def _fetch_status(host: str, port: int, timeout: float = 1.5) -> dict[str, Any]:
    try:
        with urlopen(f"http://{host}:{port}/status.json", timeout=timeout) as response:
            return {"reachable": True, "http_status": response.status, "payload": json.loads(response.read().decode("utf-8"))}
    except (OSError, URLError, json.JSONDecodeError) as exc:
        return {"reachable": False, "error": str(exc)}


def _server_ready(host: str, port: int, *, process: subprocess.Popen[bytes], timeout: float = 0.25) -> bool:
    """Return whether the newly spawned server is alive and accepting connections."""
    if process.poll() is not None:
        return False
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return process.poll() is None
    except OSError:
        return False


def operations_center_status(*, root: str | Path | None = None) -> dict[str, Any]:
    base = _root(root)
    pid_info = _read_pid(base) or {}
    pid = pid_info.get("pid") if isinstance(pid_info, dict) else None
    host = pid_info.get("host") or DEFAULT_HOST
    port = int(pid_info.get("port") or DEFAULT_PORT)
    running = _process_alive(pid)
    http = _fetch_status(host, port) if running else {"reachable": False, "error": "server process is not running"}
    settings = load_operations_center_settings(base)
    return {
        "generated_at": _now(),
        "local_only": True,
        "command_surface": "operations-center status",
        "host": host,
        "port": port,
        "url": f"http://{host}:{port}/",
        "pid": pid,
        "running": running,
        "http_status": http,
        "entry_point": "runtime/steward/command_center.html",
        "settings_loaded": bool(settings.get("settings")),
        "settings_path": settings.get("path"),
        "pid_file": str(PID_PATH),
        "log_file": str(LOG_PATH),
        "authority": {"executes_work_packages": False, "bypasses_steward_authorization": False, "stores_secrets": False},
    }


def operations_center_start(*, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, root: str | Path | None = None) -> dict[str, Any]:
    base = _root(root)
    existing = operations_center_status(root=base)
    if existing.get("running"):
        existing.update({"started": False, "message": "Operations Center server is already running."})
        return existing

    preflight: list[dict[str, Any]] = []
    settings = load_operations_center_settings(base)
    preflight.append({"name": "settings", "status": "available" if settings.get("settings") else "degraded", "path": settings.get("path")})
    health = generate_service_health_registry(root=base, write=True)
    summary = health.get("summary") or {}
    preflight.append({"name": "service_health_preflight", "status": summary.get("overall_status") or "available", "path": "runtime/services/service_health_registry.json"})
    # Fast-start consumes the durable dashboard artifact. Refresh this projection
    # first so the Office cannot materialize a provider-only snapshot after new
    # seat telemetry has already been collected.
    engineering_capacity = generate_engineering_capacity_dashboard(root=base, write=True)
    preflight.append({"name": "engineering_capacity_projection", "status": "available", "path": "runtime/engineering_capacity/dashboard.json", "codex_seat_observations": len(engineering_capacity.get("codex_seat_observations") or [])})
    command_center = generate_command_center(root=base, write=True, fast_start=True)
    preflight.append({"name": "static_entry_point", "status": "available", "path": "runtime/steward/command_center.html", "panel_count": len(command_center.get("panels") or {})})
    runtime_dir = base / "runtime" / "steward"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    log_handle = _log_file(base).open("a", encoding="utf-8")
    env = os.environ.copy()
    src_path = str(Path(__file__).resolve().parents[2])
    env["PYTHONPATH"] = src_path + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    proc = subprocess.Popen(
        [sys.executable, "-m", "estate.cli.main", "steward-command-center", "--serve", "--host", host, "--port", str(port)],
        cwd=base,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        start_new_session=True,
        env=env,
    )
    pid_payload = {"pid": proc.pid, "host": host, "port": port, "started_at": _now(), "command": "steward-command-center --serve", "local_only": True}
    if os.name == "nt":
        creation_token = _windows_process_creation_token(proc.pid)
        if creation_token is not None:
            pid_payload["windows_creation_token"] = creation_token
    _pid_file(base).write_text(json.dumps(pid_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    deadline = time.monotonic() + 8.0
    ready = False
    while time.monotonic() < deadline:
        if _server_ready(host, port, process=proc):
            ready = True
            break
        time.sleep(0.1)

    settings = load_operations_center_settings(base)
    status = {
        "generated_at": _now(),
        "local_only": True,
        "command_surface": "operations-center status",
        "host": host,
        "port": port,
        "url": f"http://{host}:{port}/",
        "pid": proc.pid,
        "running": proc.poll() is None,
        "http_status": {"reachable": ready, "probe": "tcp"},
        "entry_point": "runtime/steward/command_center.html",
        "settings_loaded": bool(settings.get("settings")),
        "settings_path": settings.get("path"),
        "pid_file": str(PID_PATH),
        "log_file": str(LOG_PATH),
        "authority": {"executes_work_packages": False, "bypasses_steward_authorization": False, "stores_secrets": False},
    }
    reachable = bool(status["running"] and ready)
    status.update({"started": reachable, "preflight": preflight, "message": "Operations Center server started." if reachable else "Server process did not become reachable; inspect log file."})
    return status


def operations_center_stop(*, root: str | Path | None = None) -> dict[str, Any]:
    base = _root(root)
    pid_info = _read_pid(base) or {}
    pid = pid_info.get("pid") if isinstance(pid_info, dict) else None
    if not _process_alive(pid):
        _pid_file(base).unlink(missing_ok=True)
        return {"generated_at": _now(), "local_only": True, "stopped": False, "running": False, "message": "No running Operations Center server was found."}
    if os.name != "nt":
        os.kill(pid, signal.SIGTERM)
        still_running = not _wait_for_process_exit(pid)
    else:
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass
        still_running = not _wait_for_process_exit(pid)
        if still_running and _windows_process_matches_server(pid, pid_info):
            _windows_force_terminate(pid)
            still_running = not _wait_for_process_exit(pid)
    if not still_running:
        _pid_file(base).unlink(missing_ok=True)
    return {"generated_at": _now(), "local_only": True, "stopped": not still_running, "running": still_running, "pid": pid, "message": "Operations Center server stopped." if not still_running else "Server did not stop after SIGTERM."}


def format_operations_center_bootstrap(payload: dict[str, Any]) -> str:
    lines = ["Estate Operations Center Local Server", f"Local only: {payload.get('local_only')}", f"URL: {payload.get('url', f'http://{payload.get('host', DEFAULT_HOST)}:{payload.get('port', DEFAULT_PORT)}/')}", f"Running: {payload.get('running')}"]
    if payload.get("message"):
        lines.append(f"Status: {payload.get('message')}")
    if payload.get("entry_point"):
        lines.append(f"Static entry point: {payload.get('entry_point')}")
    lines.append("Authority: read-only bootstrap; does not execute work packages, store secrets, or bypass Steward authorization.")
    return "\n".join(lines)
