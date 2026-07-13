"""Deterministic dependency batching for Benchmark 001.

This module exposes :class:`DependencyBatchError` and :func:`plan_batches`.
It has no third-party dependencies and does not mutate caller-provided task
records.
"""

from __future__ import annotations



class DependencyBatchError(ValueError):
    """Raised when dependency batch planning input is invalid or unschedulable."""


def _is_int_not_bool(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _validate_task_collection(tasks: list[dict], max_parallel: int) -> dict[str, dict]:
    if not _is_int_not_bool(max_parallel) or max_parallel <= 0:
        raise DependencyBatchError("max_parallel must be a positive integer")

    if not isinstance(tasks, list):
        raise DependencyBatchError("tasks must be a list of task dictionaries")

    by_id: dict[str, dict] = {}
    for index, task in enumerate(tasks):
        if not isinstance(task, dict):
            raise DependencyBatchError(f"task at index {index} must be a dictionary")

        task_id = task.get("id")
        if not isinstance(task_id, str) or not task_id:
            raise DependencyBatchError(f"task at index {index} has an invalid id")
        if task_id in by_id:
            raise DependencyBatchError(f"duplicate task id: {task_id}")

        duration = task.get("duration")
        if not _is_int_not_bool(duration) or duration <= 0:
            raise DependencyBatchError(f"task {task_id!r} has an invalid duration")

        priority = task.get("priority")
        if not _is_int_not_bool(priority):
            raise DependencyBatchError(f"task {task_id!r} has an invalid priority")

        depends_on = task.get("depends_on")
        if not isinstance(depends_on, list):
            raise DependencyBatchError(f"task {task_id!r} has invalid dependencies")
        for dep_id in depends_on:
            if not isinstance(dep_id, str) or not dep_id:
                raise DependencyBatchError(f"task {task_id!r} has invalid dependency id")
            if dep_id == task_id:
                raise DependencyBatchError(f"task {task_id!r} depends on itself")

        by_id[task_id] = {
            "id": task_id,
            "duration": duration,
            "priority": priority,
            "depends_on": tuple(depends_on),
        }

    for task_id, task in by_id.items():
        for dep_id in task["depends_on"]:
            if dep_id not in by_id:
                raise DependencyBatchError(
                    f"task {task_id!r} depends on unknown task {dep_id!r}"
                )

    return by_id


def plan_batches(tasks: list[dict], max_parallel: int) -> list[list[str]]:
    """Return deterministic dependency batches for *tasks*.

    A task becomes eligible only after every dependency has been completed in a
    previous batch. Eligible tasks are ordered by descending priority, ascending
    duration, then ascending task id, and each batch contains at most
    ``max_parallel`` task ids.

    Raises:
        DependencyBatchError: if validation fails or the dependency graph has a
            cycle.
    """

    by_id = _validate_task_collection(tasks, max_parallel)
    completed: set[str] = set()
    batches: list[list[str]] = []

    while len(completed) < len(by_id):
        eligible = [
            task
            for task in by_id.values()
            if task["id"] not in completed
            and all(dep_id in completed for dep_id in task["depends_on"])
        ]
        if not eligible:
            raise DependencyBatchError("dependency cycle detected")

        eligible.sort(key=lambda task: (-task["priority"], task["duration"], task["id"]))
        batch = [task["id"] for task in eligible[:max_parallel]]
        completed.update(batch)
        batches.append(batch)

    return batches


__all__ = ["DependencyBatchError", "plan_batches"]
