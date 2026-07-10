"""Durable local host wrapper for the Operations Runtime service loop.

The host owns process/autostart concerns only. It delegates all runtime work to
:class:`OperationsRuntimeService` and never invokes providers directly.
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

from estate.core.operations_runtime import utc_now_iso
from estate.core.operations_runtime_service import OperationsRuntimeLockError, OperationsRuntimeService
from estate.core.paths import ESTATE_ROOT

HOST_ENV = "ESTATE_OPERATIONS_RUNTIME_HOST_DIR"
ROOT_ENV = "ESTATE_OPERATIONS_RUNTIME_ROOT"
DEFAULT_INTERVAL_SECONDS = 30.0
DEFAULT_MAX_CYCLES = 1_000_000
STALE_LOCK_SECONDS = 6 * 60 * 60


def _root(root: Path | None = None) -> Path:
    if root is not None:
        return root
    if os.environ.get(ROOT_ENV):
        return Path(os.environ[ROOT_ENV]).resolve()
    return ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd()


def _state_dir(state_dir: Path | None = None) -> Path:
    if state_dir is not None:
        return state_dir
    if os.environ.get(HOST_ENV):
        return Path(os.environ[HOST_ENV]).expanduser().resolve()
    return (Path.home() / ".estate" / "operations_runtime_host").resolve()


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def _iso_age_seconds(value: str | None) -> float | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return max(0.0, (datetime.now(timezone.utc) - parsed).total_seconds())


class OperationsRuntimeHostError(RuntimeError):
    """Raised when host lifecycle actions cannot be completed safely."""


class OperationsRuntimeHost:
    def __init__(self, root: Path | None = None, state_dir: Path | None = None) -> None:
        self.root = _root(root)
        self.state_dir = _state_dir(state_dir)
        self.lock_path = self.state_dir / "host.lock.json"
        self.pid_path = self.state_dir / "host.pid.json"
        self.heartbeat_path = self.state_dir / "heartbeat.json"
        self.last_cycle_path = self.state_dir / "last_cycle.json"
        self.startup_path = self.state_dir / "startup.json"
        self.shutdown_path = self.state_dir / "shutdown.json"
        self.crash_path = self.state_dir / "crash.json"
        self.install_path = self.state_dir / "autostart.json"
        self.stop_path = self.state_dir / "stop_requested.json"

    def _ensure_state_dir(self) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def _lock_stale(self, payload: dict[str, Any]) -> bool:
        pid = int(payload.get("pid") or 0)
        if pid and not _pid_alive(pid):
            return True
        age = _iso_age_seconds(payload.get("heartbeat_at") or payload.get("acquired_at"))
        return age is not None and age > STALE_LOCK_SECONDS

    def acquire_lock(self) -> dict[str, Any]:
        self._ensure_state_dir()
        if self.lock_path.exists():
            payload = _read_json(self.lock_path)
            if int(payload.get("pid") or 0) == os.getpid() and payload.get("state") == "starting":
                payload.update({"heartbeat_at": utc_now_iso(), "state": "running"})
                _write_json(self.lock_path, payload)
                _write_json(self.pid_path, payload)
                return payload
            if not self._lock_stale(payload):
                raise OperationsRuntimeHostError(f"operations runtime host already running as pid {payload.get('pid', 'unknown')}")
            self.lock_path.unlink()
        payload = {"pid": os.getpid(), "root": str(self.root), "acquired_at": utc_now_iso(), "heartbeat_at": utc_now_iso(), "state": "running"}
        _write_json(self.lock_path, payload)
        _write_json(self.pid_path, payload)
        return payload

    def release_lock(self) -> None:
        if self.lock_path.exists():
            self.lock_path.unlink()

    def heartbeat(self, state: str, cycle: dict[str, Any] | None = None) -> None:
        payload = {"pid": os.getpid(), "state": state, "root": str(self.root), "heartbeat_at": utc_now_iso(), "provider_execution_performed": False}
        _write_json(self.heartbeat_path, payload)
        if self.lock_path.exists():
            lock = _read_json(self.lock_path)
            lock.update({"heartbeat_at": payload["heartbeat_at"], "state": state})
            _write_json(self.lock_path, lock)
        if cycle is not None:
            _write_json(self.last_cycle_path, cycle)

    def run_foreground(self, *, interval_seconds: float = DEFAULT_INTERVAL_SECONDS, max_cycles: int = DEFAULT_MAX_CYCLES, dry_run: bool = False, mode: str = "observe-only", max_audit_requests: int = 1) -> dict[str, Any]:
        self.acquire_lock()
        _write_json(self.startup_path, {"pid": os.getpid(), "started_at": utc_now_iso(), "root": str(self.root)})
        state = "running"
        cycles_run = 0
        service = OperationsRuntimeService(self.root)
        try:
            service.runtime.clear_stop_request()
            for _ in range(max_cycles):
                if self.stop_path.exists() or service.runtime.stop_requested():
                    state = "stop_requested"
                    break
                self.heartbeat("running")
                cycle = service.run_once(dry_run=dry_run, mode=mode, max_audit_requests=max_audit_requests)
                cycles_run += 1
                self.heartbeat("sleeping", cycle)
                if interval_seconds:
                    time.sleep(interval_seconds)
            else:
                state = "stopped"
            return {"state": state, "cycles_run": cycles_run, "provider_execution_performed": False}
        except Exception as exc:
            state = "failed"
            _write_json(self.crash_path, {"pid": os.getpid(), "crashed_at": utc_now_iso(), "error": str(exc), "type": type(exc).__name__})
            raise
        finally:
            _write_json(self.shutdown_path, {"pid": os.getpid(), "shutdown_at": utc_now_iso(), "state": state})
            if self.stop_path.exists():
                self.stop_path.unlink()
            self.release_lock()

    def start(self) -> dict[str, Any]:
        self._ensure_state_dir()
        if self.lock_path.exists():
            payload = _read_json(self.lock_path)
            if not self._lock_stale(payload):
                raise OperationsRuntimeHostError(f"operations runtime host already running as pid {payload.get('pid', 'unknown')}")
            self.lock_path.unlink()
        env = os.environ.copy()
        env[ROOT_ENV] = str(self.root)
        env[HOST_ENV] = str(self.state_dir)
        cmd = [sys.executable, "-m", "estate.cli.main", "operations-runtime", "host", "run-foreground"]
        with (self.state_dir / "host.stdout.log").open("ab") as out, (self.state_dir / "host.stderr.log").open("ab") as err:
            proc = subprocess.Popen(cmd, cwd=str(self.root), env=env, stdin=subprocess.DEVNULL, stdout=out, stderr=err, start_new_session=(os.name != "nt"))
        payload = {"state": "starting", "pid": proc.pid, "command": cmd, "started_at": utc_now_iso(), "heartbeat_at": utc_now_iso(), "state_dir": str(self.state_dir), "root": str(self.root)}
        _write_json(self.pid_path, payload)
        _write_json(self.lock_path, payload)
        return payload

    def stop(self) -> dict[str, Any]:
        self._ensure_state_dir()
        _write_json(self.stop_path, {"requested_at": utc_now_iso()})
        OperationsRuntimeService(self.root).request_stop()
        pid = int((_read_json(self.pid_path).get("pid") if self.pid_path.exists() else 0) or 0)
        if pid and _pid_alive(pid):
            try:
                os.kill(pid, signal.SIGTERM)
            except OSError:
                pass
        return {"state": "stop_requested", "pid": pid or None}

    def restart(self) -> dict[str, Any]:
        stopped = self.stop()
        started = self.start()
        return {"state": "restarted", "stop": stopped, "start": started}

    def status(self) -> dict[str, Any]:
        runtime = OperationsRuntimeService(self.root).status()
        heartbeat = _read_json(self.heartbeat_path) if self.heartbeat_path.exists() else {}
        lock = _read_json(self.lock_path) if self.lock_path.exists() else {}
        pid = int((lock.get("pid") or heartbeat.get("pid") or 0) or 0)
        running = bool(pid and _pid_alive(pid) and self.lock_path.exists())
        summary = runtime.get("summary", {})
        return {"host_state": "running" if running else "stopped", "pid": pid or None, "state_dir": str(self.state_dir), "heartbeat_age_seconds": _iso_age_seconds(heartbeat.get("heartbeat_at")), "cycle_state": summary.get("operations_runtime_state"), "last_verdict": summary.get("latest_audit_verdict"), "blocking_fault": (summary.get("runtime_warnings") or [None])[0], "runtime_status": runtime, "lock_present": self.lock_path.exists()}

    def install(self) -> dict[str, Any]:
        self._ensure_state_dir()
        command = [sys.executable, "-m", "estate.cli.main", "operations-runtime", "host", "start"]
        payload = {"installed_at": utc_now_iso(), "method": "scheduled-task" if os.name == "nt" else "manual-launch-manifest", "command": command, "root": str(self.root), "state_dir": str(self.state_dir)}
        if os.name == "nt":
            payload["scheduled_task"] = "Estate Operations Runtime Host"
            # Document the native command instead of requiring elevated privileges during tests.
            payload["windows_command"] = ["schtasks", "/Create", "/SC", "ONLOGON", "/TN", payload["scheduled_task"], "/TR", " ".join(command), "/F"]
        _write_json(self.install_path, payload)
        return payload

    def uninstall(self) -> dict[str, Any]:
        existed = self.install_path.exists()
        if existed:
            self.install_path.unlink()
        return {"uninstalled_at": utc_now_iso(), "removed_manifest": existed, "scheduled_task": "Estate Operations Runtime Host" if os.name == "nt" else None}
