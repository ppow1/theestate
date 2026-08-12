from __future__ import annotations

import json
import sys
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from estate.core.execution_dispatch import (
    QUEUE_LOCK,
    _queue_mutation_lock,
    enqueue_dispatch_request,
    load_dispatch_queue,
    update_dispatch_state,
)


def _request(root: Path, dispatch_id: str) -> dict:
    return {
        "dispatch_id": dispatch_id,
        "work_package_id": dispatch_id,
        "title": dispatch_id,
        "requested_by": "Engineering",
        "assigned_worker": "test-worker",
        "provider": "codex-cli-openai",
        "profile_label": "test",
        "classification": "Estate Internal",
        "state": "Queued",
        "prompt_source": "prompt.md",
        "sandbox": "read-only",
        "allowed_read_paths": ["prompt.md"],
        "allowed_providers": ["codex-cli-openai"],
        "created_at": f"2026-08-11T00:00:{int(dispatch_id.rsplit('-', 1)[-1]):02d}Z",
        "updated_at": f"2026-08-11T00:00:{int(dispatch_id.rsplit('-', 1)[-1]):02d}Z",
    }


def _enqueue_process(args: tuple[str, str]) -> str:
    root, dispatch_id = args
    return enqueue_dispatch_request(_request(Path(root), dispatch_id), root).dispatch_id


def test_cross_process_writers_preserve_distinct_dispatch_entries(tmp_path):
    (tmp_path / "prompt.md").write_text("bounded test prompt\n", encoding="utf-8")
    args = [(str(tmp_path), f"dispatch-{index:02d}") for index in range(12)]
    with ProcessPoolExecutor(max_workers=4) as pool:
        assert sorted(pool.map(_enqueue_process, args)) == sorted(item[1] for item in args)
    items = load_dispatch_queue(tmp_path)
    assert {item.dispatch_id for item in items} == {item[1] for item in args}
    assert json.loads((tmp_path / "runtime/execution_dispatch/queue.json").read_text(encoding="utf-8"))["item_count"] == 12


def test_concurrent_readers_never_observe_partial_json(tmp_path):
    (tmp_path / "prompt.md").write_text("bounded test prompt\n", encoding="utf-8")
    enqueue_dispatch_request(_request(tmp_path, "dispatch-00"), tmp_path)

    def update(index: int):
        update_dispatch_state("dispatch-00", "Running" if index % 2 else "Ready", tmp_path)

    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(update, index) for index in range(20)]
        for _ in range(100):
            load_dispatch_queue(tmp_path)
        [future.result() for future in futures]
    assert load_dispatch_queue(tmp_path)[0].dispatch_id == "dispatch-00"


def test_concurrent_distinct_state_updates_do_not_lose_records(tmp_path):
    (tmp_path / "prompt.md").write_text("bounded test prompt\n", encoding="utf-8")
    enqueue_dispatch_request(_request(tmp_path, "dispatch-00"), tmp_path)
    enqueue_dispatch_request(_request(tmp_path, "dispatch-01"), tmp_path)

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(update_dispatch_state, dispatch_id, "Running", tmp_path) for dispatch_id in ("dispatch-00", "dispatch-01")]
        [future.result() for future in futures]
    assert {item.dispatch_id for item in load_dispatch_queue(tmp_path)} == {"dispatch-00", "dispatch-01"}
    assert {item.state for item in load_dispatch_queue(tmp_path)} == {"Running"}


def test_stale_temp_file_is_not_authoritative(tmp_path):
    (tmp_path / "prompt.md").write_text("bounded test prompt\n", encoding="utf-8")
    enqueue_dispatch_request(_request(tmp_path, "dispatch-00"), tmp_path)
    queue = tmp_path / "runtime/execution_dispatch/queue.json"
    (queue.parent / "queue.json.stale.tmp").write_text("not authoritative", encoding="utf-8")
    assert [item.dispatch_id for item in load_dispatch_queue(tmp_path)] == ["dispatch-00"]


def test_persistent_malformed_queue_fails_closed_after_bounded_retry(tmp_path):
    queue = tmp_path / "runtime/execution_dispatch/queue.json"
    queue.parent.mkdir(parents=True)
    queue.write_text("{", encoding="utf-8")
    with pytest.raises(ValueError, match="malformed JSON"):
        load_dispatch_queue(tmp_path)


def test_lock_releases_after_exception(tmp_path):
    with pytest.raises(RuntimeError):
        with _queue_mutation_lock(tmp_path):
            raise RuntimeError("synthetic mutation failure")
    with _queue_mutation_lock(tmp_path):
        pass
    assert (tmp_path / QUEUE_LOCK).is_file()


def test_lock_timeout_is_truthful(tmp_path):
    with _queue_mutation_lock(tmp_path):
        with pytest.raises(TimeoutError, match="Dispatch queue lock"):
            with _queue_mutation_lock(tmp_path, timeout_seconds=0.03):
                pass


def test_queue_lock_scope_does_not_wrap_provider_execution():
    source = Path("src/estate/core/execution_dispatch.py").read_text(encoding="utf-8")
    assert "provider" not in source[source.index("def _queue_mutation_lock"):source.index("def _read_queue_payload")]
