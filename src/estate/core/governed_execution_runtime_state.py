"""Idempotent bootstrap for the governed execution runtime state contract."""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from estate.core.execution_activity import generate_execution_activity_surface
from estate.core.execution_dispatch import generate_current_dispatch_snapshot

RESERVATIONS = Path("runtime/engineering_scheduler/compute_reservations.json")
RECONCILIATION = Path("runtime/execution_adapters/reconciliation")
ADAPTER_DIRS = (
    Path("runtime/execution_adapters/requests"),
    Path("runtime/execution_adapters/results"),
    Path("runtime/execution_adapters/status"),
)


def _atomic_json(path: Path, payload: Any) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return False
    fd, name = tempfile.mkstemp(prefix=f"{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
        return True
    finally:
        if os.path.exists(name):
            os.unlink(name)


def _validate_reservations(path: Path) -> None:
    if not path.exists():
        return
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"malformed reservation state: {path}: {exc}") from exc
    if not isinstance(payload, list) or any(not isinstance(row, dict) for row in payload):
        raise RuntimeError(f"reservation state must be a JSON list of objects: {path}")


def ensure_governed_execution_runtime_state(root: str | Path) -> dict[str, Any]:
    """Create/validate the minimum state required before governed execution.

    Existing state is never overwritten. Missing queue/activity files are
    created through their canonical projection writers; malformed state fails
    closed before any initialization occurs.
    """
    base = Path(root)
    reservation_path = base / RESERVATIONS
    _validate_reservations(reservation_path)
    created: list[str] = []
    reservation_path.parent.mkdir(parents=True, exist_ok=True)
    if _atomic_json(reservation_path, []):
        created.append(RESERVATIONS.as_posix())

    queue = base / "runtime/execution_dispatch/queue.json"
    if queue.exists():
        try:
            payload = json.loads(queue.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"malformed dispatch queue: {queue}: {exc}") from exc
        if not isinstance(payload, (list, dict)):
            raise RuntimeError(f"dispatch queue must be a JSON object or list: {queue}")
    else:
        generate_current_dispatch_snapshot(base, write=True)
        created.append(queue.relative_to(base).as_posix())

    activity = base / "runtime/execution_activity/current.json"
    if activity.exists():
        try:
            payload = json.loads(activity.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"malformed execution activity state: {activity}: {exc}") from exc
        if not isinstance(payload, dict):
            raise RuntimeError(f"execution activity state must be a JSON object: {activity}")
    else:
        generate_execution_activity_surface(base, write=True)
        created.append(activity.relative_to(base).as_posix())

    reconciliation = base / RECONCILIATION
    if reconciliation.exists() and not reconciliation.is_dir():
        raise RuntimeError(f"execution reconciliation path is not a directory: {reconciliation}")
    if not reconciliation.exists():
        reconciliation.mkdir(parents=True, exist_ok=True)
        created.append(RECONCILIATION.as_posix())
    for relative in ADAPTER_DIRS:
        path = base / relative
        if path.exists() and not path.is_dir():
            raise RuntimeError(f"execution adapter path is not a directory: {path}")
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            created.append(relative.as_posix())
    return {
        "status": "READY",
        "root": str(base),
        "created": created,
        "artifacts": [RESERVATIONS.as_posix(), "runtime/execution_dispatch/queue.json", "runtime/execution_activity/current.json", RECONCILIATION.as_posix(), *(path.as_posix() for path in ADAPTER_DIRS)],
    }
