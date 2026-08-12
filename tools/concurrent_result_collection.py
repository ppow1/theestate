"""Deadlock-free collection of bounded child-process results."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Any


def _read_stream(stream: Any) -> str:
    try:
        return stream.read()
    finally:
        stream.close()


def collect_process(process: Any, *, timeout: float | None = None) -> dict[str, Any]:
    """Drain both pipes while the child runs, then return its complete result."""
    with ThreadPoolExecutor(max_workers=2) as pool:
        stdout_future = pool.submit(_read_stream, process.stdout)
        stderr_future = pool.submit(_read_stream, process.stderr)
        returncode = process.wait(timeout=timeout)
        return {
            "returncode": returncode,
            "stdout": stdout_future.result(),
            "stderr": stderr_future.result(),
        }


def collect_processes(processes: dict[str, Any], *, timeout: float | None = None) -> dict[str, dict[str, Any]]:
    """Collect independent child results concurrently; no result waits on another."""
    with ThreadPoolExecutor(max_workers=max(1, len(processes))) as pool:
        futures = {name: pool.submit(collect_process, process, timeout=timeout) for name, process in processes.items()}
        return {name: future.result() for name, future in futures.items()}
