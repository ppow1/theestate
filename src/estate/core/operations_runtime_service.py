"""Bounded service-loop controller for Operations Runtime."""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from estate.core.operations_runtime import LOCK, OperationsRuntime, STATUS_DIR, _read_json, _write_json, utc_now_iso
from estate.core.paths import ESTATE_ROOT


def _root(root: Path | None = None) -> Path:
    return root or (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


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
            data = _read_json(self.lock_path)
            raise OperationsRuntimeLockError(f"operations runtime already locked by {data.get('pid', 'unknown')}")
        payload = {"pid": os.getpid(), "acquired_at": utc_now_iso(), "state": "running"}
        _write_json(self.lock_path, payload)
        return payload

    def release_lock(self) -> None:
        if self.lock_path.exists():
            self.lock_path.unlink()

    def run_once(self, *, dry_run: bool = False) -> dict[str, Any]:
        self.acquire_lock()
        try:
            return self.runtime.run_cycle(dry_run=dry_run)
        finally:
            self.release_lock()

    def start(self, *, max_cycles: int = 1, interval_seconds: float = 30.0, dry_run: bool = False) -> dict[str, Any]:
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
                cycle = self.runtime.run_cycle(dry_run=dry_run)
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
