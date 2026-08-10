from estate.core.execution_adapter_handoff_runtime import prepare_handoff
from estate.core.openwebui_engineering_workflow import detect_engineering_assignment_command, detect_bounded_local_text_intent, _qwen_minimum_safe_vram_mib
from estate.core.resident_gateway import _bounded_local_text_content
from estate.core import resident_gateway
from estate.core.resident_gateway import chat_completion, chat_completion_stream

LIVE_BOUNDED_PROMPT = "Grace, run a small bounded local text task: write one short sentence confirming that this governed task used the UUID-bound RTX 4090 lane; include no secrets and perform no hardware actions."


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


def test_qwen_model_specific_vram_floor_fails_closed_when_missing(tmp_path):
    config = tmp_path / "config/providers/qwen_local_text.json"
    config.parent.mkdir(parents=True)
    config.write_text('{"minimum_safe_vram_mib": 8192}\n', encoding="utf-8")
    assert _qwen_minimum_safe_vram_mib(tmp_path) == 8192
    config.write_text('{}\n', encoding="utf-8")
    assert _qwen_minimum_safe_vram_mib(tmp_path) is None


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
