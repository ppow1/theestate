from estate.core.execution_adapter_handoff_runtime import prepare_handoff
from estate.core.openwebui_engineering_workflow import detect_engineering_assignment_command, detect_bounded_local_text_intent, detect_bounded_compute_resource_intent, _qwen_minimum_safe_vram_mib, _target_symbolic_lane, _parallel_bounded_text_task_specs, execute_parallel_bounded_local_text_from_chat
from estate.core.resident_gateway import _bounded_local_text_content, _grace_runtime_operation_response
from estate.core import resident_gateway
from estate.core.resident_gateway import chat_completion, chat_completion_stream
from estate.core.compute_resources import ComputeResourceObservation
from estate.core.gpu_runtime_lanes import RuntimeLane

LIVE_BOUNDED_PROMPT = "Grace, run a small bounded local text task: write one short sentence confirming that this governed task used the UUID-bound RTX 4090 lane; include no secrets and perform no hardware actions."
P100_LIVE_PROMPT = "Grace, run a small bounded local text task using the governed P100 compute lane, produce one short sentence, and tell me which physical GPU executed it."


def test_detects_explicit_metadata_command():
    command = detect_engineering_assignment_command(
        {"metadata": {"estate_command": "initiate_engineering_assignment", "engineering_objective": "Repair the dashboard."}},
        "Please do it.",
    )
    assert command["objective"] == "Repair the dashboard."
    assert command["source"] == "metadata"


def test_bounded_text_intent_is_explicit_and_ordinary_chat_is_not_executable():
    assert detect_bounded_local_text_intent({"model": "estate/grace"}, "Grace, run a small bounded local text task.")["state"] == "execution_requested"
    assert detect_bounded_local_text_intent({"model": "estate/grace"}, LIVE_BOUNDED_PROMPT) == {"state": "execution_requested", "intent": "bounded_local_text", "source": "explicit_chat_prefix"}
    assert detect_bounded_local_text_intent({"model": "estate/grace"}, "Grace, what is the Estate status?")["state"] == "conversation_only"
    assert detect_bounded_local_text_intent({"model": "estate/grace"}, "Grace, run something locally.")["state"] == "execution_blocked"


def test_natural_bounded_local_text_variants_are_executable():
    prompts = [
        "Run one small governed local text task and return one short sentence confirming successful local execution. Use the normal governed execution path and do not perform hardware actions.",
        "Grace, execute a bounded local text-generation task and give me one short sentence.",
        "Use the governed local text execution path for a tiny response.",
        "Run a small local governed text task; no hardware actions.",
    ]
    for prompt in prompts:
        result = detect_bounded_local_text_intent({"model": "estate/grace"}, prompt)
        assert result == {"state": "execution_requested", "intent": "bounded_local_text", "source": "semantic_chat_intent"}


def test_ambiguous_or_unsafe_local_requests_remain_fail_closed():
    prompts = [
        "Run this locally.",
        "Use my GPU.",
        "Execute something on this computer.",
        "Run a benchmark.",
        "Delete this file locally.",
        "Launch PowerShell locally.",
    ]
    for prompt in prompts:
        assert detect_bounded_local_text_intent({"model": "estate/grace"}, prompt)["state"] == "execution_blocked"


def test_natural_parallel_bounded_text_variants_produce_two_qualified_specs():
    prompts = [
        "Grace, run two small independent governed local text tasks at the same time: one on the governed RTX 4090 lane and one on the conservative P100 lane. Keep both tasks tiny and return one short result from each.",
        "Run two bounded local text-generation tasks concurrently, one on each qualified GPU lane.",
        "Execute a pair of small governed text tasks in parallel: one on 4090 and one on P100.",
        "Run two independent governed local text tasks concurrently and return a short result from each.",
    ]
    for prompt in prompts:
        result = detect_bounded_local_text_intent({"model": "estate/grace"}, prompt)
        assert result["state"] == "execution_requested"
        assert result["intent"] == "parallel_bounded_local_text"
        assert len(result["task_specs"]) == 2
        assert [item["runtime_lane_id"] for item in result["task_specs"]] == ["qwen.local.text.4090", "qwen.local.text.p100-1"]


def test_parallel_intent_preserves_qualified_profiles_and_fails_closed_for_unsafe_requests():
    specs = _parallel_bounded_text_task_specs()
    assert specs[0]["model"] == "qwen3:8b" and specs[0]["concurrency"] == 1
    assert specs[1]["model"] == "llama3.2:3b" and specs[1]["context_limit"] == 1024 and specs[1]["output_cap"] == 32
    for prompt in ("Use both GPUs.", "Run two things in parallel.", "Benchmark both GPUs.", "Run PowerShell on both GPUs.", "Delete two files concurrently.", "Stress the P100 and 4090.", "Run two tasks on an A100 and a P100."):
        assert detect_bounded_local_text_intent({"model": "estate/grace"}, prompt)["state"] == "execution_blocked"


def test_parallel_executor_uses_two_existing_single_task_paths(monkeypatch, tmp_path):
    calls = []
    def fake_single(payload, *, user_message, session_id, root):
        calls.append((payload["metadata"]["parallel_task_id"], user_message))
        return {"state": "execution_completed", "provider_execution_performed": True, "objective": {"objective_id": calls[-1][0]}}
    monkeypatch.setattr("estate.core.openwebui_engineering_workflow.execute_bounded_local_text_from_chat", fake_single)
    prompt = "Run two independent governed local text tasks concurrently and return a short result from each."
    result = execute_parallel_bounded_local_text_from_chat({"model": "estate/grace"}, user_message=prompt, session_id="parallel-test", root=tmp_path)
    assert result["state"] == "execution_completed"
    assert {item[0] for item in calls} == {"rtx4090", "p100"}


def test_bounded_prompt_with_runtime_keywords_bypasses_read_only_runtime_layer():
    prompt = "Grace, run a small bounded local text task on the governed P100 compute lane: write one short sentence about a safe operational checkpoint; include no secrets and perform no hardware actions."
    payload = {"model": "estate/grace", "messages": [{"role": "user", "content": prompt}]}
    assert detect_bounded_local_text_intent(payload, prompt)["state"] == "execution_requested"
    assert _grace_runtime_operation_response(payload, root=".") is None


def test_exact_p100_prompt_precedes_runtime_inference_in_both_modes(monkeypatch, tmp_path):
    payload = {"model": "estate/grace", "messages": [{"role": "user", "content": P100_LIVE_PROMPT}]}
    assert detect_bounded_local_text_intent(payload, P100_LIVE_PROMPT) == {
        "state": "execution_requested", "intent": "bounded_local_text", "source": "explicit_chat_prefix"
    }
    assert _grace_runtime_operation_response(payload, root=tmp_path) is None

    calls = []
    def fake_handler(payload, *, user_message, session_id, root, stream=False):
        calls.append(stream)
        return {"id": "bounded-precedence", "object": "chat.completion.chunk" if stream else "chat.completion", "created": 0, "model": "estate/grace", "choices": [{"index": 0, "delta": {"content": "governed"}}] if stream else [{"index": 0, "message": {"content": "governed"}}], "estate": {"bounded_local_text": {"state": "execution_requested"}}}

    monkeypatch.setattr(resident_gateway, "_bounded_local_text_chat_completion", fake_handler)
    code, _ = chat_completion({**payload, "stream": False}, root=tmp_path)
    assert code == 200
    code, _ = chat_completion_stream({**payload, "stream": True}, root=tmp_path)
    assert code == 200
    assert calls == [False, True]


def test_symbolic_p100_resource_intent_resolves_registered_physical_resource(tmp_path):
    uuid = "GPU-6785b322-899d-8eec-e817-31d83279a414"
    resource_id = f"DESKTOP-JA3RPNQ:nvidia:{uuid}"
    observation = ComputeResourceObservation(resource_id=resource_id, host_id="DESKTOP-JA3RPNQ", nvidia_uuid=uuid, name="Tesla P100-PCIE-16GB", health_state="healthy", capacity_state="available")
    lane = RuntimeLane(runtime_lane_id="qwen.local.text.p100-1", provider_id="qwen.local.text", endpoint_type="ollama-http", endpoint_address="http://127.0.0.1:12100", host_id="DESKTOP-JA3RPNQ", compute_resource_id=resource_id, gpu_uuid=uuid, model_identity="llama3.2:3b", environment_binding={"CUDA_VISIBLE_DEVICES": uuid, "OLLAMA_HOST": "127.0.0.1:12100"}, provider_config_path="config/providers/qwen_local_text_p100.json", minimum_vram_mib=4096)
    (tmp_path / "config/providers").mkdir(parents=True)
    (tmp_path / "config/providers/qwen_local_text_p100.json").write_text('{"minimum_safe_vram_mib": 4096}', encoding="utf-8")
    import estate.core.openwebui_engineering_workflow as workflow
    original = workflow.load_registered_lanes
    workflow.load_registered_lanes = lambda root: [lane]
    try:
        assert detect_bounded_compute_resource_intent("use the governed P100 compute lane") == {"state": "required", "symbol": "p100", "source": "registered_compute_resource_symbol"}
        selected = _target_symbolic_lane(tmp_path, [observation], "p100")
        assert selected[0].runtime_lane_id == "qwen.local.text.p100-1"
        assert selected[2].nvidia_uuid == uuid
    finally:
        workflow.load_registered_lanes = original


def test_unknown_or_raw_placement_text_fails_closed_without_injection():
    assert detect_bounded_compute_resource_intent("run on the Tesla V100") ["state"] == "blocked"
    assert detect_bounded_compute_resource_intent("use GPU-46f3fd00-5454-4536-4196-5d8b727e14f2") ["state"] == "blocked"
    assert detect_bounded_compute_resource_intent("use qwen.local.text.4090") ["state"] == "blocked"
    assert detect_bounded_compute_resource_intent("run a small bounded local text task") == {"state": "none"}


def test_qwen_model_specific_vram_floor_fails_closed_when_missing(tmp_path):
    config = tmp_path / "config/providers/qwen_local_text.json"
    config.parent.mkdir(parents=True)
    config.write_text('{"minimum_safe_vram_mib": 8192}\n', encoding="utf-8")
    assert _qwen_minimum_safe_vram_mib(tmp_path) == 8192
    config.write_text('{}\n', encoding="utf-8")
    assert _qwen_minimum_safe_vram_mib(tmp_path) is None


def test_missing_lane_registry_fails_closed_before_bounded_execution(tmp_path, monkeypatch):
    import estate.core.openwebui_engineering_workflow as workflow
    monkeypatch.setattr(workflow, "collect_nvidia_smi", lambda: [ComputeResourceObservation(
        resource_id="host:nvidia:GPU-test", host_id="host", nvidia_uuid="GPU-test",
        name="NVIDIA GeForce RTX 4090", health_state="healthy", capacity_state="available",
    )])
    result = workflow.execute_bounded_local_text_from_chat(
        {"model": "estate/grace"},
        user_message="Grace, run a small bounded local text task.",
        session_id="missing-lane-registry",
        root=tmp_path,
    )
    assert result["state"] == "execution_blocked"
    assert result["provider_execution_performed"] is False
    assert "target lane" in result["reason"]


def test_bounded_visible_placement_uses_authoritative_receipt_metadata():
    content = _bounded_local_text_content({
        "state": "execution_completed",
        "lane": {"runtime_lane_id": "qwen.local.text.p100-1"},
        "placement": {"selected": "host:nvidia:GPU-P100"},
        "execution": {"result": {"summary": "completed", "metadata": {"runtime_bound_gpu_uuid": "GPU-P100"}}},
    })
    assert '"gpu_uuid": "GPU-P100"' in content


def test_bounded_text_request_fails_closed_without_fresh_physical_evidence(tmp_path):
    code, body = chat_completion({"model": "estate/grace", "messages": [{"role": "user", "content": "Grace, run a small bounded local text task."}], "metadata": {"session_id": "bounded-blocked"}}, root=tmp_path)
    assert code == 200
    assert body["estate"]["bounded_local_text"]["state"] == "execution_blocked"
    assert body["estate"]["provider_execution_performed"] is False


def test_streaming_bounded_text_enters_governed_handler(monkeypatch, tmp_path):
    observed = {}

    def fake_handler(payload, *, user_message, session_id, root, stream):
        observed.update({"payload": payload, "user_message": user_message, "session_id": session_id, "root": root, "stream": stream})
        return {"id": "bounded-test", "object": "chat.completion.chunk", "created": 0, "model": "estate/grace", "choices": [{"delta": {"content": "governed"}}], "estate": {"bounded_local_text": {"state": "execution_blocked"}}}

    monkeypatch.setattr(resident_gateway, "_bounded_local_text_chat_completion", fake_handler)
    code, body = chat_completion_stream({"model": "estate/grace", "stream": True, "messages": [{"role": "user", "content": LIVE_BOUNDED_PROMPT}], "metadata": {"session_id": "stream-bounded"}}, root=tmp_path)
    assert code == 200
    chunks = list(body)
    assert chunks[0]["estate"]["bounded_local_text"]["state"] == "execution_blocked"
    assert observed["stream"] is True
    assert observed["session_id"] == "stream-bounded"


def test_openwebui_chat_initiates_existing_helen_grace_dispatch_workflow(tmp_path):
    code, body = chat_completion(
        {
            "model": "estate/grace",
            "messages": [{"role": "user", "content": "Initiate Engineering Department assignment: add a validation smoke test."}],
            "metadata": {"session_id": "owui-eng-1"},
        },
        root=tmp_path,
    )

    assert code == 200
    workflow = body["estate"]["engineering_assignment"]
    assert workflow["second_execution_system_created"] is False
    assert workflow["provider_execution_performed"] is False
    assert workflow["helen_request"]["request_type"] == "staffing_request"
    assert workflow["helen_assessment"]["assessor"] == "Helen"
    assert workflow["grace_action"]["state"] == "dispatch_requested"
    assert workflow["grace_action"]["dispatch_handoff_request"]["provider_execution_must_remain_behind_dispatch"] is True
    assert (tmp_path / "runtime/workforce_development/status/latest.json").exists()
    assert (tmp_path / "runtime/operations/grace/status/latest.json").exists()
    assert (tmp_path / "runtime/execution_dispatch/queue.json").exists()
    assert "No second execution system" in body["choices"][0]["message"]["content"]


def test_openwebui_dispatch_is_immediately_handoff_eligible(tmp_path):
    code, body = chat_completion(
        {
            "model": "estate/grace",
            "messages": [{"role": "user", "content": EXACT_COMMAND}],
            "metadata": {"session_id": "owui-eng-handoff-ready"},
        },
        root=tmp_path,
    )

    assert code == 200
    dispatch_id = body["estate"]["engineering_assignment"]["grace_action"]["dispatch_handoff_request"]["dispatch_id"]
    prepared = prepare_handoff(dispatch_id, tmp_path)

    assert prepared["status"] == "handoff_validated"
    assert prepared["errors"] == []
    adapter_request = prepared["adapter_request"]
    assert prepared["adapter_request"] is None
    assert prepared["dispatch"]["provider"] is None
    assert prepared["dispatch"]["provider_metadata"]["commission"]["requested_outcome"]
    assert prepared["dispatch"]["provider_metadata"]["commission"]["acceptance_criteria"]
    assert prepared["dispatch"]["provider_metadata"]["provider_execution_must_remain_behind_dispatch"] is True

EXACT_COMMAND = (
    "Initiate Engineering Department assignment: verify the Open WebUI engineering assignment workflow "
    "by creating one bounded validation smoke-test assignment."
)

FORBIDDEN_VISIBLE_PHRASES = (
    "unknown action category",
    "authority status",
    "this action is blocked",
    "blocked by default",
    "routing guidance",
)


def _workflow_artifact_counts(root):
    import json
    queue_path = root / "runtime/execution_dispatch/queue.json"
    dispatch_queue = json.loads(queue_path.read_text()) if queue_path.exists() else []
    return {
        "helen_requests": len(list((root / "runtime/workforce_development/requests").glob("*.json"))),
        "helen_assessments": len(list((root / "runtime/workforce_development/assessments").glob("*.json"))),
        "grace_objectives": len(list((root / "runtime/operations/grace/objectives").glob("*.json"))),
        "grace_actions": len(list((root / "runtime/operations/grace/actions").glob("*.json"))),
        "dispatch_requests": len(dispatch_queue.get("items", [])),
    }


def test_exact_command_non_streaming_still_initiates_workflow(tmp_path):
    code, body = chat_completion(
        {
            "model": "estate/grace",
            "stream": False,
            "messages": [{"role": "user", "content": EXACT_COMMAND}],
            "metadata": {"session_id": "owui-eng-exact-nonstream"},
        },
        root=tmp_path,
    )

    assert code == 200
    assert body["object"] == "chat.completion"
    assert body["choices"][0]["finish_reason"] == "stop"
    assert body["estate"]["session_id"] == "owui-eng-exact-nonstream"
    assert body["estate"]["engineering_assignment"]["provider_execution_performed"] is False
    assert body["estate"]["engineering_assignment"]["second_execution_system_created"] is False
    assert body["estate"]["privileged_action_executed"] is False


def test_exact_command_streaming_initiates_workflow_once_without_conversation(monkeypatch, tmp_path):
    calls = []
    def fake_process_chat(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("streaming engineering command must not enter ordinary conversation handling")
    monkeypatch.setattr("estate.core.resident_gateway.process_chat", fake_process_chat)

    code, chunks = chat_completion_stream(
        {
            "model": "estate/grace",
            "stream": True,
            "messages": [{"role": "user", "content": EXACT_COMMAND}],
            "metadata": {"session_id": "owui-eng-exact-stream"},
        },
        root=tmp_path,
    )
    chunks = list(chunks)
    visible = "".join(chunk["choices"][0]["delta"].get("content", "") for chunk in chunks)
    first_estate = chunks[0]["estate"]
    workflow = first_estate["engineering_assignment"]

    assert code == 200
    assert calls == []
    assert chunks[0]["object"] == "chat.completion.chunk"
    assert chunks[0]["choices"][0]["delta"] == {"role": "assistant"}
    assert any(chunk["choices"][0]["delta"].get("content") for chunk in chunks)
    assert chunks[-1]["choices"][0]["delta"] == {}
    assert chunks[-1]["choices"][0]["finish_reason"] == "stop"
    assert first_estate["resident_id"] == "grace"
    assert first_estate["session_id"] == "owui-eng-exact-stream"
    assert first_estate["provider_execution_performed"] is False
    assert first_estate["second_execution_system_created"] is False
    assert first_estate["privileged_action_executed"] is False
    assert workflow["provider_execution_performed"] is False
    assert workflow["second_execution_system_created"] is False
    assert workflow["helen_request"]["request_type"] == "staffing_request"
    assert workflow["helen_assessment"]["assessor"] == "Helen"
    assert workflow["grace_action"]["state"] == "dispatch_requested"
    assert workflow["grace_action"]["dispatch_handoff_request"]["provider_execution_must_remain_behind_dispatch"] is True
    assert _workflow_artifact_counts(tmp_path) == {
        "helen_requests": 1,
        "helen_assessments": 1,
        "grace_objectives": 1,
        "grace_actions": 1,
        "dispatch_requests": 1,
    }
    assert "Engineering Department assignment initiated through the existing Helen workforce" in visible
    assert "Grace operations" in visible
    assert "Dispatch runtimes" in visible
    lower_visible = visible.lower()
    assert all(phrase not in lower_visible for phrase in FORBIDDEN_VISIBLE_PHRASES)
