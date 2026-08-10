"""Durable local host wrapper for the Operations Runtime service loop.

The host owns process/autostart concerns only. It delegates all runtime work to
:class:`OperationsRuntimeService` and never invokes providers directly.
"""
from __future__ import annotations

import ctypes
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
TASK_NAME = "Estate Operations Runtime Host"
TASK_NAME_ENV = "ESTATE_OPERATIONS_RUNTIME_TASK_NAME"
DEFAULT_RUNTIME_CODE_ROOT = Path("A:/EstateRuntime/host/estate-main/current")
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



def _run_command(cmd: list[str], *, cwd: Path | None = None, timeout: float | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd) if cwd else None, text=True, capture_output=True, check=False, timeout=timeout)

def _quote_ps(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"

def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _windows_pid_liveness(pid: int) -> str:
    """Return ``alive``, ``dead``, or ``unknown`` for a Windows process id."""
    if pid <= 0:
        return "dead"
    try:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        process_query_limited_information = 0x1000
        handle = kernel32.OpenProcess(process_query_limited_information, False, int(pid))
        if not handle:
            error = ctypes.get_last_error()
            return "dead" if error == 87 else "unknown"
        try:
            exit_code = ctypes.c_ulong()
            if not kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                return "unknown"
            still_active = 259
            return "alive" if exit_code.value == still_active else "dead"
        finally:
            kernel32.CloseHandle(handle)
    except Exception:
        return "unknown"


def _pid_liveness(pid: int) -> str:
    if pid <= 0:
        return "dead"
    if os.name == "nt":
        return _windows_pid_liveness(pid)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return "dead"
    except PermissionError:
        return "alive"
    except OSError:
        return "unknown"
    return "alive"


def _pid_alive(pid: int) -> bool:
    return _pid_liveness(pid) == "alive"


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
    def __init__(self, root: Path | None = None, state_dir: Path | None = None, task_name: str | None = None) -> None:
        self.root = _root(root)
        self.state_dir = _state_dir(state_dir)
        self.task_name_explicit = task_name is not None or os.environ.get(TASK_NAME_ENV) is not None
        self.task_name = task_name or os.environ.get(TASK_NAME_ENV) or TASK_NAME
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

    def _lock_recoverable(self, payload: dict[str, Any]) -> bool:
        pid = int(payload.get("pid") or 0)
        return _pid_liveness(pid) == "dead"

    def acquire_lock(self) -> dict[str, Any]:
        self._ensure_state_dir()
        if self.lock_path.exists():
            payload = _read_json(self.lock_path)
            if int(payload.get("pid") or 0) == os.getpid() and payload.get("state") == "starting":
                payload.update({"heartbeat_at": utc_now_iso(), "state": "running"})
                _write_json(self.lock_path, payload)
                _write_json(self.pid_path, payload)
                return payload
            if not self._lock_recoverable(payload):
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
            if not self._lock_recoverable(payload):
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
        install = _read_json(self.install_path) if self.install_path.exists() else {}
        md_summary = {}
        md_status = self.root / "runtime/merge_discovery/status/latest.json"
        if md_status.exists():
            try:
                md_summary = (_read_json(md_status).get("summary") or {})
            except Exception:
                md_summary = {}
        task_state = self._query_windows_task() if os.name == "nt" else {"scheduled_task_exists": bool(install), "scheduled_task_state": None}
        heartbeat_age = _iso_age_seconds(heartbeat.get("heartbeat_at"))
        heartbeat_current = heartbeat_age is not None and heartbeat_age < STALE_LOCK_SECONDS
        host_pid_alive = bool(pid and _pid_alive(pid))
        lock_present = self.lock_path.exists()
        host_process_state = "running" if host_pid_alive and lock_present else ("stale_lock_dead_pid" if lock_present else "stopped")
        host_state = "running" if host_pid_alive and heartbeat_current and lock_present else "stopped"
        return {"installed": bool(install), **task_state, "host_process_state": host_process_state, "host_pid_alive": host_pid_alive, "heartbeat_state": heartbeat.get("state"), "heartbeat_age_seconds": heartbeat_age, "host_state": host_state, "pid": pid or None, "state_dir": str(self.state_dir), "current_cycle_state": "running" if heartbeat.get("state") == "running" else None, "last_completed_cycle_state": summary.get("operations_runtime_state"), "last_completed_cycle_at": summary.get("last_cycle_at"), "runtime_code_revision": self._runtime_revision(), "watched_remote_ref": md_summary.get("watched_remote_ref", "origin/main"), "last_fetch_at": md_summary.get("last_fetch_at"), "last_scanned_commit": md_summary.get("last_scanned_commit"), "last_processed_work_package": summary.get("latest_admitted_work_package"), "cycle_state": summary.get("operations_runtime_state"), "last_verdict": summary.get("latest_audit_verdict"), "blocking_fault": (summary.get("runtime_warnings") or md_summary.get("errors") or [None])[0], "runtime_status": runtime, "lock_present": lock_present}

    def _launcher_path(self) -> Path:
        return self.state_dir / "run_operations_runtime_host.ps1"

    def _write_windows_launcher(self) -> Path:
        launcher = self._launcher_path()
        launcher.parent.mkdir(parents=True, exist_ok=True)
        launcher.write_text(
            "$ErrorActionPreference = 'Stop'\n"
            f"$env:{ROOT_ENV} = {_quote_ps(str(self.root))}\n"
            f"$env:{HOST_ENV} = {_quote_ps(str(self.state_dir))}\n"
            f"$env:PYTHONPATH = {_quote_ps(str(self.root / 'src'))}\n"
            f"Set-Location {_quote_ps(str(self.root))}\n"
            f"& {_quote_ps(sys.executable)} -m estate.cli.main operations-runtime host run-foreground --discover-merges --auto-admit --process-audits --max-audit-requests 5\n",
            encoding="utf-8",
        )
        return launcher

    def _manifest_scheduled_task_name(self) -> str | None:
        if not self.install_path.exists():
            return None
        try:
            value = _read_json(self.install_path).get("scheduled_task_name")
        except Exception:
            return None
        return value if isinstance(value, str) and value.strip() else None

    def _scheduled_task_name_for_management(self) -> str:
        if self.task_name_explicit:
            return self.task_name
        return self._manifest_scheduled_task_name() or self.task_name

    def _query_windows_task(self, task_name: str | None = None) -> dict[str, Any]:
        managed_task_name = task_name or self._scheduled_task_name_for_management()
        query = ["schtasks", "/Query", "/TN", managed_task_name, "/FO", "LIST", "/V"]
        try:
            result = _run_command(query, timeout=2.0)
        except subprocess.TimeoutExpired as exc:
            return {"scheduled_task_exists": False, "scheduled_task_state": None, "scheduled_task_name": managed_task_name, "query_command": query, "query_returncode": None, "query_stdout": (exc.stdout or ""), "query_stderr": (exc.stderr or ""), "query_timed_out": True}
        exists = result.returncode == 0
        state = None
        for line in result.stdout.splitlines():
            if line.lower().startswith("status:") or line.lower().startswith("scheduled task state:"):
                state = line.split(":", 1)[1].strip()
                break
        return {"scheduled_task_exists": exists, "scheduled_task_state": state, "scheduled_task_name": managed_task_name, "query_command": query, "query_returncode": result.returncode, "query_stdout": result.stdout, "query_stderr": result.stderr}

    def _runtime_revision(self) -> str | None:
        try:
            result = _run_command(["git", "rev-parse", "HEAD"], cwd=self.root, timeout=2.0)
        except subprocess.TimeoutExpired:
            return None
        return result.stdout.strip() if result.returncode == 0 else None

    def install(self) -> dict[str, Any]:
        self._ensure_state_dir()
        command = [sys.executable, "-m", "estate.cli.main", "operations-runtime", "host", "start"]
        payload = {"installed_at": utc_now_iso(), "installed": True, "method": "scheduled-task" if os.name == "nt" else "manual-launch-manifest", "command": command, "root": str(self.root), "state_dir": str(self.state_dir), "scheduled_task_name": self.task_name, "scheduled_task_exists": False, "scheduled_task_verified": False}
        if os.name == "nt":
            launcher = self._write_windows_launcher()
            task_command = f'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "{launcher}"'
            create_cmd = ["schtasks", "/Create", "/SC", "ONLOGON", "/TN", self.task_name, "/TR", task_command, "/F"]
            result = _run_command(create_cmd)
            if result.returncode != 0:
                raise OperationsRuntimeHostError(result.stderr or result.stdout or "failed to create scheduled task")
            task_state = self._query_windows_task(self.task_name)
            if not task_state["scheduled_task_exists"]:
                raise OperationsRuntimeHostError("scheduled task creation could not be verified")
            payload.update(task_state)
            payload.update({"launcher": str(launcher), "windows_command": create_cmd, "scheduled_task_verified": True})
        _write_json(self.install_path, payload)
        return payload

    def uninstall(self) -> dict[str, Any]:
        existed = self.install_path.exists()
        managed_task_name = self._scheduled_task_name_for_management() if os.name == "nt" else None
        if os.name == "nt":
            delete_cmd = ["schtasks", "/Delete", "/TN", managed_task_name, "/F"]
            result = _run_command(delete_cmd)
            if result.returncode not in {0, 1}:
                raise OperationsRuntimeHostError(result.stderr or result.stdout or "failed to delete scheduled task")
            task_state = self._query_windows_task(managed_task_name)
            removed = not task_state["scheduled_task_exists"]
            if not removed:
                raise OperationsRuntimeHostError("scheduled task removal could not be verified")
        else:
            delete_cmd = []
            removed = True
            task_state = {"scheduled_task_exists": False, "scheduled_task_state": None}
        if existed:
            self.install_path.unlink()
        return {"uninstalled_at": utc_now_iso(), "removed_manifest": existed, "scheduled_task": managed_task_name if os.name == "nt" else None, "scheduled_task_removed": removed, "delete_command": delete_cmd, **task_state}

    @classmethod
    def bootstrap(cls, target: str = "estate-main", *, runtime_code_root: Path | None = None, source_root: Path | None = None) -> dict[str, Any]:
        source = _root(source_root)
        code_root = (runtime_code_root or DEFAULT_RUNTIME_CODE_ROOT).resolve()
        fetch = _run_command(["git", "fetch", "--quiet", "origin", "main"], cwd=source)
        if fetch.returncode != 0:
            raise OperationsRuntimeHostError(fetch.stderr or fetch.stdout or "failed to fetch source origin/main")
        remote_url = _run_command(["git", "remote", "get-url", "origin"], cwd=source).stdout.strip() or str(source)
        source_rev = _run_command(["git", "rev-parse", "HEAD"], cwd=source).stdout.strip()
        remote_rev = _run_command(["git", "rev-parse", "origin/main"], cwd=source).stdout.strip()
        if not remote_rev:
            raise OperationsRuntimeHostError("could not resolve source origin/main")
        if code_root.exists() and not (code_root / ".git").exists():
            raise OperationsRuntimeHostError(f"runtime workspace exists but is not a git checkout: {code_root}")
        if not code_root.exists():
            code_root.parent.mkdir(parents=True, exist_ok=True)
            clone = _run_command(["git", "clone", "--quiet", remote_url, str(code_root)])
            if clone.returncode != 0:
                raise OperationsRuntimeHostError(clone.stderr or clone.stdout or "failed to create runtime code workspace")
        set_url = _run_command(["git", "remote", "set-url", "origin", remote_url], cwd=code_root)
        if set_url.returncode != 0:
            raise OperationsRuntimeHostError(set_url.stderr or set_url.stdout or "failed to set runtime origin")
        runtime_fetch = _run_command(["git", "fetch", "--quiet", "origin", "main"], cwd=code_root)
        if runtime_fetch.returncode != 0:
            raise OperationsRuntimeHostError(runtime_fetch.stderr or runtime_fetch.stdout or "failed to fetch runtime origin/main")
        reset = _run_command(["git", "reset", "--hard", "origin/main"], cwd=code_root)
        if reset.returncode != 0:
            raise OperationsRuntimeHostError(reset.stderr or reset.stdout or "failed to reset runtime workspace")
        runtime_rev = _run_command(["git", "rev-parse", "HEAD"], cwd=code_root).stdout.strip()
        runtime_matches_remote = bool(runtime_rev and runtime_rev == remote_rev)
        if not runtime_matches_remote:
            raise OperationsRuntimeHostError("runtime workspace revision does not match origin/main")
        state_dir = code_root.parent / "state"
        host = cls(code_root, state_dir)
        installed = host.install()
        started = host.start()
        deadline = time.time() + 5
        heartbeat_verified = False
        while time.time() < deadline:
            if host.heartbeat_path.exists():
                heartbeat_verified = True
                break
            time.sleep(0.1)
        status = host.status()
        return {"target": target, "remote_ref_used": "origin/main", "source_checkout_revision": source_rev, "remote_main_revision": remote_rev, "runtime_workspace_revision": runtime_rev, "runtime_matches_remote": runtime_matches_remote, "runtime_code_workspace": str(code_root), "scheduled_task_name": host.task_name, "scheduled_task_installed": bool(installed.get("installed")), "scheduled_task_verified": bool(installed.get("scheduled_task_verified") or os.name != "nt"), "host_started": bool(started.get("pid")), "heartbeat_verified": heartbeat_verified or status.get("host_state") == "running", "active_checkout_modifications_performed": False, "pending_only_commits_suppressed": True, "eligible_completed_work_detected": None, "provider_execution_performed": False, "dispatch_execution_performed": False, "install": installed, "start": started, "status": status}
