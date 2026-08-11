from __future__ import annotations

import threading
from pathlib import Path

import pytest

from estate.core.qwen_local_text_execution_provider_adapter import QwenLocalTextExecutionProviderAdapter
from estate.core.runtime_envelope import RuntimeLaneBusy, request_lease


POLICY = {"max_concurrent_requests": 1, "request_queue": "reject_when_busy", "max_output_tokens": 64, "context_limit": 2048}


def test_bounded_ollama_options_reach_provider_request(tmp_path: Path):
    from test_qwen_local_text_execution_provider_adapter import _technical_request

    request, adapter = _technical_request(tmp_path, response_text="The bounded task completed.", output_name="bounded-options")
    calls = []

    def transport(method, url, payload, timeout):
        calls.append((method, url, payload, timeout))
        return (200, {"models": [{"name": "qwen3:8b"}]}) if method == "GET" else (200, {"model": "qwen3:8b", "response": "The bounded task completed."})

    adapter.http_call = transport
    result = adapter.submit(request)
    assert result.status == "completed"
    post = next(item for item in calls if item[0] == "POST")
    assert post[2]["options"] == {"num_ctx": 4096, "num_predict": 128}
    assert post[2]["think"] is False


def test_incomplete_qwen_response_remains_fail_closed(tmp_path: Path):
    from test_qwen_local_text_execution_provider_adapter import _technical_request

    request, adapter = _technical_request(tmp_path, response_text="", output_name="incomplete-qwen")

    def transport(method, url, payload, timeout):
        return (200, {"models": [{"name": "qwen3:8b"}]}) if method == "GET" else (200, {"model": "qwen3:8b", "response": "", "thinking": "hidden reasoning", "done": True, "done_reason": "length", "eval_count": 128})

    adapter.http_call = transport
    result = adapter.submit(request)
    assert result.status == "failed"
    assert result.errors == ["Qwen returned a malformed or incomplete response"]


def test_completed_qwen_response_with_thinking_metadata_is_accepted(tmp_path: Path):
    from test_qwen_local_text_execution_provider_adapter import _technical_request

    request, adapter = _technical_request(tmp_path, response_text="", output_name="completed-qwen")

    def transport(method, url, payload, timeout):
        return (200, {"models": [{"name": "qwen3:8b"}]}) if method == "GET" else (200, {"model": "qwen3:8b", "response": "The bounded task completed.", "thinking": "", "done": True, "done_reason": "stop", "eval_count": 7})

    adapter.http_call = transport
    result = adapter.submit(request)
    assert result.status == "completed"


def test_same_lane_second_request_is_blocked(tmp_path: Path):
    lane = "qwen.local.text.p100-1"
    acquired = threading.Event()
    release = threading.Event()

    def hold():
        with request_lease(tmp_path, lane, POLICY):
            acquired.set()
            release.wait(timeout=5)

    worker = threading.Thread(target=hold)
    worker.start()
    assert acquired.wait(timeout=5)
    with pytest.raises(RuntimeLaneBusy):
        with request_lease(tmp_path, lane, POLICY):
            pass
    release.set()
    worker.join(timeout=5)
    assert not worker.is_alive()


def test_different_gpu_lanes_can_hold_leases_concurrently(tmp_path: Path):
    entered = []
    barrier = threading.Barrier(2)

    def hold(lane: str):
        with request_lease(tmp_path, lane, POLICY):
            entered.append(lane)
            barrier.wait(timeout=5)

    workers = [threading.Thread(target=hold, args=(lane,)) for lane in ("qwen.local.text.4090", "qwen.local.text.p100-1")]
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join(timeout=5)
    assert sorted(entered) == ["qwen.local.text.4090", "qwen.local.text.p100-1"]
