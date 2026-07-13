"""Local server bootstrap for the Estate Operations Center.

This module starts, inspects, and stops the existing Steward command center HTTP
server. It is local-first only: it binds to loopback by default, stores no
secrets, and never executes work packages or changes command authority.
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

from estate.core.paths import ESTATE_ROOT
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


def _fetch_status(host: str, port: int, timeout: float = 1.5) -> dict[str, Any]:
    try:
        with urlopen(f"http://{host}:{port}/status.json", timeout=timeout) as response:
            return {"reachable": True, "http_status": response.status, "payload": json.loads(response.read().decode("utf-8"))}
    except (OSError, URLError, json.JSONDecodeError) as exc:
        return {"reachable": False, "error": str(exc)}


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
    command_center = generate_command_center(root=base, write=True)
    preflight.append({"name": "static_entry_point", "status": "available", "path": "runtime/steward/command_center.html", "panel_count": len(command_center.get("panels") or {})})

    runtime_dir = base / "runtime" / "steward"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    log_handle = _log_file(base).open("a", encoding="utf-8")
    env = os.environ.copy()
    src_path = str(Path(__file__).resolve().parents[2])
    env["PYTHONPATH"] = src_path + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    env["ESTATE_BOOTSTRAP_STATUS_FAST"] = "1"
    proc = subprocess.Popen(
        [sys.executable, "-m", "estate.cli.main", "steward-command-center", "--serve", "--host", host, "--port", str(port)],
        cwd=base,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        start_new_session=True,
        env=env,
    )
    pid_payload = {"pid": proc.pid, "host": host, "port": port, "started_at": _now(), "command": "steward-command-center --serve", "local_only": True}
    _pid_file(base).write_text(json.dumps(pid_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    status = operations_center_status(root=base)
    for _ in range(80):
        status = operations_center_status(root=base)
        if status.get("running") and (status.get("http_status") or {}).get("reachable"):
            break
        time.sleep(0.1)
    reachable = bool(status.get("running") and (status.get("http_status") or {}).get("reachable"))
    status.update({"started": reachable, "preflight": preflight, "message": "Operations Center server started." if reachable else "Server process did not become reachable; inspect log file."})
    return status


def operations_center_stop(*, root: str | Path | None = None) -> dict[str, Any]:
    base = _root(root)
    pid_info = _read_pid(base) or {}
    pid = pid_info.get("pid") if isinstance(pid_info, dict) else None
    if not _process_alive(pid):
        _pid_file(base).unlink(missing_ok=True)
        return {"generated_at": _now(), "local_only": True, "stopped": False, "running": False, "message": "No running Operations Center server was found."}
    os.kill(pid, signal.SIGTERM)
    for _ in range(20):
        if not _process_alive(pid):
            break
        time.sleep(0.1)
    still_running = _process_alive(pid)
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
