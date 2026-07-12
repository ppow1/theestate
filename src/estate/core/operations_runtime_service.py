"""Bounded service-loop controller for Operations Runtime."""
from __future__ import annotations

import ctypes
import json
import os
import signal
import time
from pathlib import Path
from typing import Any

from estate.core.operations_runtime import LOCK, OperationsRuntime, STATUS_DIR, _read_json, _write_json, utc_now_iso
from estate.core.paths import ESTATE_ROOT


def _root(root: Path | None = None) -> Path:
    return root or (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())



def _windows_pid_liveness(pid: int) -> str:
    """Return ``alive``, ``dead``, or ``unknown`` for a Windows process id.

    Windows does not provide POSIX ``kill(pid, 0)`` semantics.  Use the
    process handle API instead so a PID left in the lock file before a power
    loss can be identified as dead after reboot without deleting locks for
    live or access-denied owners.
    """
    if pid <= 0:
        return "dead"
    try:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        process_query_limited_information = 0x1000
        handle = kernel32.OpenProcess(process_query_limited_information, False, int(pid))
        if not handle:
            error = ctypes.get_last_error()
            if error == 87:  # ERROR_INVALID_PARAMETER: no process with that PID.
                return "dead"
            if error == 5:  # ERROR_ACCESS_DENIED: process exists but is protected.
                return "alive"
            return "unknown"
        try:
            exit_code = ctypes.c_ulong()
            if not kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                return "unknown"
            return "alive" if exit_code.value == 259 else "dead"  # STILL_ACTIVE
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

class OperationsRuntimeLockError(RuntimeError):
    pass


class OperationsRuntimeService:
    def __init__(self, root: Path | None = None) -> None:
        self.root = _root(root)
        self.runtime = OperationsRuntime(self.root)
        self.lock_path = self.root / LOCK

    def acquire_lock(self) -> dict[str, Any]:
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        if self.lock_path.exists():
            try:
                data = _read_json(self.lock_path)
            except Exception as exc:
                raise OperationsRuntimeLockError(f"operations runtime lock malformed: {exc}")
            if not isinstance(data, dict):
                raise OperationsRuntimeLockError("operations runtime lock malformed: metadata is not an object")
            try:
                pid = int(data.get("pid") or 0)
            except (TypeError, ValueError) as exc:
                raise OperationsRuntimeLockError(f"operations runtime lock malformed: invalid pid {data.get('pid')!r}") from exc
            live = _pid_liveness(pid)
            if live == "dead":
                recovery = {"pid": pid, "recovered_at": utc_now_iso(), "reason": "dead_owner_lock", "liveness": live, "lock": data}
                _write_json(self.root / STATUS_DIR / "stale_lock_recovery_latest.json", recovery)
                self.lock_path.unlink()
            elif live == "alive":
                raise OperationsRuntimeLockError(f"operations runtime already locked by live pid {data.get('pid', 'unknown')}")
            else:
                raise OperationsRuntimeLockError(f"operations runtime lock owner liveness uncertain for pid {data.get('pid', 'unknown')}")
        payload = {"pid": os.getpid(), "acquired_at": utc_now_iso(), "state": "running"}
        _write_json(self.lock_path, payload)
        return payload

    def release_lock(self) -> None:
        if self.lock_path.exists():
            self.lock_path.unlink()

    def run_once(self, *, dry_run: bool = False, mode: str = "observe-only", max_audit_requests: int = 1) -> dict[str, Any]:
        self.acquire_lock()
        try:
            return self.runtime.run_cycle(dry_run=dry_run, mode=mode, max_audit_requests=max_audit_requests)
        finally:
            self.release_lock()

    def start(self, *, max_cycles: int = 1, interval_seconds: float = 30.0, dry_run: bool = False, mode: str = "observe-only", max_audit_requests: int = 1) -> dict[str, Any]:
        if max_cycles < 1:
            raise ValueError("max_cycles must be at least 1")
        if interval_seconds < 0:
            raise ValueError("interval_seconds must be non-negative")
        self.runtime.ensure_dirs()
        self.runtime.clear_stop_request()
        self.acquire_lock()
        cycles: list[dict[str, Any]] = []
        state = "running"
        try:
            for index in range(max_cycles):
                if self.runtime.stop_requested():
                    state = "stop_requested"
                    break
                cycle = self.runtime.run_cycle(dry_run=dry_run, mode=mode, max_audit_requests=max_audit_requests)
                cycles.append(cycle)
                if self.runtime.stop_requested():
                    state = "stop_requested"
                    break
                if index < max_cycles - 1:
                    latest = self.runtime.load_status()
                    latest["summary"]["operations_runtime_state"] = "sleeping"
                    _write_json(self.root / STATUS_DIR / "latest.json", latest)
                    _write_json(self.root / STATUS_DIR / "summary.json", latest["summary"])
                    if interval_seconds:
                        time.sleep(interval_seconds)
            else:
                state = "stopped"
        except Exception:
            state = "failed"
            raise
        finally:
            self.release_lock()
        status = self.runtime.load_status()
        status["summary"]["operations_runtime_state"] = state
        _write_json(self.root / STATUS_DIR / "latest.json", status)
        _write_json(self.root / STATUS_DIR / "summary.json", status["summary"])
        return {"state": state, "cycles_run": len(cycles), "cycles": cycles, "status": status, "provider_execution_performed": False, "dispatch_execution_performed": False}

    def status(self) -> dict[str, Any]:
        payload = self.runtime.load_status()
        payload["lock_present"] = self.lock_path.exists()
        return payload

    def request_stop(self) -> dict[str, Any]:
        return self.runtime.request_stop()

    def report(self) -> str:
        p = self.root / "runtime/operations_runtime/reports/latest.md"
        if p.exists():
            return p.read_text(encoding="utf-8")
        from estate.core.operations_runtime import format_operations_runtime_report
        return format_operations_runtime_report(self.runtime.load_status())
