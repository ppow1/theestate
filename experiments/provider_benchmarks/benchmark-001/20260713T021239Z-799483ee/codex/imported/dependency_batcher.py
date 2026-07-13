class DependencyBatchError(ValueError):
    pass

def _is_int_not_bool(value):
    return isinstance(value, int) and not isinstance(value, bool)

def plan_batches(tasks: list[dict], max_parallel: int) -> list[list[str]]:
    if not _is_int_not_bool(max_parallel) or max_parallel <= 0:
        raise DependencyBatchError("max_parallel must be a positive integer")
    if not isinstance(tasks, list):
        raise DependencyBatchError("tasks must be a list")
    records = {}
    for task in tasks:
        if not isinstance(task, dict):
            raise DependencyBatchError("each task must be a dict")
        tid = task.get("id")
        if not isinstance(tid, str) or not tid:
            raise DependencyBatchError("task id must be a non-empty string")
        if tid in records:
            raise DependencyBatchError("duplicate task id")
        duration, priority, deps = task.get("duration"), task.get("priority"), task.get("depends_on")
        if not _is_int_not_bool(duration) or duration <= 0:
            raise DependencyBatchError("duration must be a positive integer")
        if not _is_int_not_bool(priority):
            raise DependencyBatchError("priority must be an integer")
        if not isinstance(deps, list) or any(not isinstance(d, str) or not d for d in deps):
            raise DependencyBatchError("depends_on must be a list of task ids")
        if tid in deps:
            raise DependencyBatchError("self dependency")
        records[tid] = {"duration": duration, "priority": priority, "depends_on": tuple(deps)}
    for rec in records.values():
        for dep in rec["depends_on"]:
            if dep not in records:
                raise DependencyBatchError("unknown dependency")
    remaining, completed, batches = set(records), set(), []
    while remaining:
        eligible = [tid for tid in remaining if all(dep in completed for dep in records[tid]["depends_on"])]
        if not eligible:
            raise DependencyBatchError("dependency cycle detected")
        eligible.sort(key=lambda tid: (-records[tid]["priority"], records[tid]["duration"], tid))
        batch = eligible[:max_parallel]
        batches.append(batch); completed.update(batch); remaining.difference_update(batch)
    return batches
