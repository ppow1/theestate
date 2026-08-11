"""Generic bounded request envelopes for constrained provider runtimes."""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


class RuntimeLaneBusy(RuntimeError):
    """The lane already has its permitted number of active provider requests."""


def validate_runtime_policy(policy: object) -> dict[str, object]:
    if not isinstance(policy, dict):
        raise ValueError("runtime_policy must be an object")
    maximum = policy.get("max_concurrent_requests")
    if not isinstance(maximum, int) or isinstance(maximum, bool) or maximum < 1:
        raise ValueError("runtime_policy.max_concurrent_requests must be a positive integer")
    queue = policy.get("request_queue")
    if queue not in {"reject_when_busy", "bounded_wait"}:
        raise ValueError("runtime_policy.request_queue is unsupported")
    return dict(policy)


def _lock_path(root: str | Path, runtime_lane_id: str) -> Path:
    safe = "".join(char if char.isalnum() or char in "._-" else "_" for char in runtime_lane_id)
    return Path(root) / "runtime/compute_resources/request_leases" / f"{safe}.lock"


@contextmanager
def request_lease(root: str | Path, runtime_lane_id: str, policy: dict[str, object] | None) -> Iterator[dict[str, object]]:
    """Acquire a per-lane lease; different lanes never serialize each other."""
    if policy is None:
        yield {"enforced": False, "runtime_lane_id": runtime_lane_id}
        return
    checked = validate_runtime_policy(policy)
    if checked["max_concurrent_requests"] != 1:
        raise ValueError("only max_concurrent_requests=1 is currently implemented")
    path = _lock_path(root, runtime_lane_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = path.open("a+b")
    locked = False
    try:
        handle.seek(0)
        if os.name == "nt":
            import msvcrt
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as exc:
                raise RuntimeLaneBusy(f"runtime lane {runtime_lane_id} already has an active request") from exc
        else:
            import fcntl
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                raise RuntimeLaneBusy(f"runtime lane {runtime_lane_id} already has an active request") from exc
        locked = True
        yield {"enforced": True, "runtime_lane_id": runtime_lane_id, "max_concurrent_requests": 1, "lease_path": str(path)}
    finally:
        if locked:
            if os.name == "nt":
                import msvcrt
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()
        if locked:
            try:
                path.unlink()
            except FileNotFoundError:
                pass
