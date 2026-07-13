"""Deterministic dependency batch planner and CLI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


class DependencyBatchError(ValueError):
    """Raised when dependency batch input is invalid."""


def _is_int_not_bool(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _validate_tasks(tasks: list[dict]) -> dict[str, dict[str, Any]]:
    if not isinstance(tasks, list):
        raise DependencyBatchError("tasks must be a list")

    normalized: dict[str, dict[str, Any]] = {}
    for index, task in enumerate(tasks):
        if not isinstance(task, dict):
            raise DependencyBatchError(f"task at index {index} must be an object")

        task_id = task.get("id")
        if not isinstance(task_id, str) or task_id == "":
            raise DependencyBatchError(f"task at index {index} has missing, empty, or non-string id")
        if task_id in normalized:
            raise DependencyBatchError(f"duplicate task id: {task_id}")

        duration = task.get("duration")
        if not _is_int_not_bool(duration) or duration <= 0:
            raise DependencyBatchError(f"task {task_id} duration must be a positive integer")

        priority = task.get("priority")
        if not _is_int_not_bool(priority):
            raise DependencyBatchError(f"task {task_id} priority must be an integer")

        depends_on = task.get("depends_on")
        if not isinstance(depends_on, list) or any(not isinstance(dep, str) for dep in depends_on):
            raise DependencyBatchError(f"task {task_id} depends_on must be a list of strings")

        normalized[task_id] = {
            "id": task_id,
            "duration": duration,
            "priority": priority,
            "depends_on": list(depends_on),
        }

    for task_id, task in normalized.items():
        for dep in task["depends_on"]:
            if dep not in normalized:
                raise DependencyBatchError(f"task {task_id} depends on unknown task: {dep}")
            if dep == task_id:
                raise DependencyBatchError(f"task {task_id} depends on itself")

    return normalized


def _sort_key(task: dict[str, Any]) -> tuple[int, int, str]:
    return (-task["priority"], task["duration"], task["id"])


def plan_batches(tasks: list[dict], max_parallel: int) -> list[list[str]]:
    """Plan deterministic concurrent batches for dependency-constrained tasks."""
    if not _is_int_not_bool(max_parallel) or max_parallel <= 0:
        raise DependencyBatchError("max_parallel must be a positive integer")

    task_by_id = _validate_tasks(tasks)
    completed: set[str] = set()
    scheduled: set[str] = set()
    batches: list[list[str]] = []

    while len(scheduled) < len(task_by_id):
        eligible = [
            task
            for task_id, task in task_by_id.items()
            if task_id not in scheduled and all(dep in completed for dep in task["depends_on"])
        ]
        if not eligible:
            remaining = sorted(set(task_by_id) - scheduled)
            raise DependencyBatchError("dependency graph contains a cycle involving: " + ", ".join(remaining))

        selected = sorted(eligible, key=_sort_key)[:max_parallel]
        batch = [task["id"] for task in selected]
        batches.append(batch)
        scheduled.update(batch)
        completed.update(batch)

    return batches


def _positive_int_argument(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a positive integer") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def _load_cli_input(path: Path, max_parallel_arg: int | None) -> tuple[list[dict], int]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except OSError as exc:
        raise DependencyBatchError(f"could not read input file: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise DependencyBatchError(f"invalid JSON: {exc.msg}") from exc

    if isinstance(payload, dict):
        if "tasks" not in payload:
            raise DependencyBatchError("input object must contain tasks")
        tasks = payload["tasks"]
        max_parallel = max_parallel_arg if max_parallel_arg is not None else payload.get("max_parallel")
    elif isinstance(payload, list):
        tasks = payload
        if max_parallel_arg is None:
            raise DependencyBatchError("--max-parallel is required when input is a task array")
        max_parallel = max_parallel_arg
    else:
        raise DependencyBatchError("input JSON must be an object or task array")

    return tasks, max_parallel


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plan deterministic dependency batches.")
    parser.add_argument("input_json", help="Path to input JSON")
    parser.add_argument("--max-parallel", type=_positive_int_argument, dest="max_parallel")
    args = parser.parse_args(argv)

    try:
        tasks, max_parallel = _load_cli_input(Path(args.input_json), args.max_parallel)
        batches = plan_batches(tasks, max_parallel)
    except DependencyBatchError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    json.dump({"batches": batches}, sys.stdout, separators=(",", ":"))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
