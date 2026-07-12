import importlib.util
import sys
from pathlib import Path


def load_module():
    path = Path(__file__).resolve().parents[1] / "src" / "open_webui_multi_resident_gateway.py"
    spec = importlib.util.spec_from_file_location("wp4040_open_webui_multi_resident_gateway", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


mod = load_module()


def test_default_plan_exposes_residents_and_room_model():
    catalog = mod.default_plan().model_catalog()
    ids = {item["id"] for item in catalog["data"]}
    assert {"estate/alfred", "estate/helen", "estate/ingrid", "estate/grace", "estate/conference-room"} <= ids
    assert catalog["estate"]["installed"] is False


def test_normalize_open_webui_request_preserves_session_room_targets_and_stream():
    payload = {"model":"estate/conference-room", "stream": True, "messages":[{"role":"user", "content":"Helen and Grace, weigh in."}], "metadata":{"room_id":"room-1", "session_id":"sess-1", "resident_targets":["Helen", " grace "]}}
    normalized = mod.normalize_open_webui_request(payload)
    assert normalized["stream"] is True
    assert normalized["room_id"] == "room-1"
    assert normalized["session_id"] == "sess-1"
    assert normalized["resident_targets"] == ["helen", "grace"]
    assert normalized["staged_execution"] == "not_executed"


def test_attributed_response_envelope_keeps_resident_identity():
    body = mod.attributed_response_envelope(model="estate/conference-room", room_id="room-1", resident_turns=[{"resident_id":"helen", "display_name":"Helen", "content":"Operational view."}, {"resident_id":"grace", "display_name":"Grace", "content":"Director view."}])
    content = body["choices"][0]["message"]["content"]
    assert "Helen: Operational view." in content
    assert "Grace: Director view." in content
    assert body["estate"]["attribution_preserved"] is True
    assert body["estate"]["privileged_action_executed"] is False


def test_streaming_sse_lines_end_with_done():
    body = mod.attributed_response_envelope(model="estate/conference-room", room_id="room-1", resident_turns=[{"resident_id":"ingrid", "display_name":"Ingrid", "content":"Privacy note."}], stream=True)
    lines = mod.sse_lines(body)
    assert body["object"] == "chat.completion.chunk"
    assert lines[-1] == "data: [DONE]"
    assert '"finish_reason": "stop"' in lines[1]
