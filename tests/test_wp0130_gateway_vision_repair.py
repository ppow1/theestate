import base64
import json

import pytest

from estate.core.resident_gateway import ACTIVE_RESIDENT_MODELS, chat_completion
from estate.core.resident_interaction import ATTACHMENT_STORE, load_history, load_vision_config, process_chat


PNG = b"\x89PNG\r\n\x1a\nshared mocked pixels"
DATA_URL = "data:image/png;base64," + base64.b64encode(PNG).decode("ascii")
SUMMARY = "A red umbrella is open beside a blue front door."
VOICE_MARKERS = {
    "alfred": "quiet the room", "ingrid": "Ingrid here", "helen": "lowering the temperature",
    "grace": "Grace here", "evelyn": "Come here a moment", "eleanor": "record from weather",
    "marie": "evidence triage", "judy": "risk surface",
}


class CountingVisionAdapter:
    def __init__(self):
        self.calls = []

    def summarize_image(self, *, image_path, prompt="", model=None):
        self.calls.append(image_path.read_bytes())
        return {"ok": True, "status": "processed", "summary": SUMMARY,
                "provider": "ollama", "model": "llama3.2-vision:11b"}


class UnavailableVisionAdapter:
    def summarize_image(self, **kwargs):
        return {"ok": False, "status": "unavailable", "summary": None,
                "provider": "none", "model": None, "reason": "no compatible local model"}


@pytest.mark.parametrize("resident", list(ACTIVE_RESIDENT_MODELS.values()))
def test_all_gateway_residents_use_one_bounded_observation_in_their_own_voice(monkeypatch, tmp_path, resident):
    from estate.core import resident_interaction as interaction

    adapter = CountingVisionAdapter()
    monkeypatch.setattr(interaction, "local_llm_status", lambda *args, **kwargs: {"available": False, "models": []})
    result = process_chat(
        resident,
        "Can you tell me what this is?",
        root=tmp_path,
        attachments=[{"kind": "image", "mime_type": "image/png", "data_base64": DATA_URL.split(",", 1)[1]}],
        vision_adapter=adapter,
    )

    attachment = result["turn"]["attachments"][0]
    assert adapter.calls == [PNG]
    assert attachment["vision_status"] == "processed"
    assert attachment["vision_provider"] == "ollama"
    assert attachment["vision_model"] == "llama3.2-vision:11b"
    assert attachment["summary"] == SUMMARY
    assert SUMMARY in result["turn"]["resident_response"]
    assert VOICE_MARKERS[resident].lower() in result["turn"]["resident_response"].lower()


def test_ingrid_openwebui_image_reaches_vision_and_persists_metadata(monkeypatch, tmp_path):
    from estate.core import resident_interaction as interaction

    adapter = CountingVisionAdapter()
    monkeypatch.setattr(interaction, "LocalVisionAdapter", lambda root=None: adapter)
    monkeypatch.setattr(interaction, "local_llm_status", lambda *args, **kwargs: {"available": False, "models": []})
    code, body = chat_completion({
        "model": "estate/ingrid",
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": "Can you tell me what this is?"},
            {"type": "image_url", "image_url": {"url": DATA_URL}},
        ]}],
        "metadata": {"chat_id": "ingrid-image-regression"},
    }, root=tmp_path)

    assert code == 200
    answer = body["choices"][0]["message"]["content"]
    assert SUMMARY in answer
    assert "image.png" not in answer
    history = load_history("ingrid", session_id="ingrid-image-regression", root=tmp_path)
    attachment = history["sessions"][0]["turns"][0]["attachments"][0]
    assert attachment["vision_status"] == "processed"
    assert attachment["vision_provider"] == "ollama"
    assert attachment["vision_model"] == "llama3.2-vision:11b"
    assert attachment["summary"] == SUMMARY
    stored = tmp_path / attachment["storage_path"]
    assert stored.read_bytes() == PNG
    serialized = json.dumps(history)
    assert DATA_URL not in serialized
    assert base64.b64encode(PNG).decode("ascii") not in serialized


def test_openwebui_uploaded_file_metadata_and_bounded_stored_path_are_normalized(monkeypatch, tmp_path):
    from estate.core import resident_interaction as interaction

    source = tmp_path / ATTACHMENT_STORE / "ingrid" / "upload" / "image.png"
    source.parent.mkdir(parents=True)
    source.write_bytes(PNG)
    adapter = CountingVisionAdapter()
    monkeypatch.setattr(interaction, "LocalVisionAdapter", lambda root=None: adapter)
    monkeypatch.setattr(interaction, "local_llm_status", lambda *args, **kwargs: {"available": False, "models": []})
    code, _ = chat_completion({
        "model": "estate/ingrid",
        "messages": [{"role": "user", "content": "Inspect it", "files": [{"file": {
            "name": "image.png", "content_type": "image/png",
            "storage_path": str(source.relative_to(tmp_path)),
        }}]}],
    }, root=tmp_path)
    assert code == 200
    assert adapter.calls == [PNG]


def test_ingrid_unavailable_is_truthful_and_does_not_invent(monkeypatch, tmp_path):
    from estate.core import resident_interaction as interaction

    monkeypatch.setattr(interaction, "LocalVisionAdapter", lambda root=None: UnavailableVisionAdapter())
    monkeypatch.setattr(interaction, "local_llm_status", lambda *args, **kwargs: {"available": False, "models": []})
    code, body = chat_completion({"model": "estate/ingrid", "messages": [{"role": "user", "content": [
        {"type": "text", "text": "Can you tell me what this is?"},
        {"type": "image_url", "image_url": DATA_URL},
    ]}]}, root=tmp_path)
    answer = body["choices"][0]["message"]["content"].lower()
    assert code == 200
    assert "no local vision-capable model" in answer
    assert SUMMARY.lower() not in answer


def test_conference_room_passes_same_attachment_boundary_to_each_resident(monkeypatch, tmp_path):
    seen = []

    def fake_process_chat(resident, user_message, **kwargs):
        seen.append((resident, kwargs.get("attachments")))
        return {"session_id": "room", "turn": {"turn_id": "t", "resident_id": resident,
                "resident_display_name": resident.title(), "resident_response": "observed",
                "identity_composition": kwargs["identity_composition"], "llm": {}}}

    monkeypatch.setattr("estate.core.resident_gateway.process_chat", fake_process_chat)
    code, _ = chat_completion({"model": "estate/conference-room", "metadata": {"resident_targets": ["ingrid", "helen"]},
                               "messages": [{"role": "user", "content": [{"type": "text", "text": "Discuss"},
                                                                            {"type": "image_url", "image_url": {"url": DATA_URL}}]}]}, root=tmp_path)
    assert code == 200
    assert [resident for resident, _ in seen] == ["ingrid", "helen"]
    assert all(items and items[0]["data_base64"] == DATA_URL.split(",", 1)[1] for _, items in seen)


def test_vision_configuration_is_one_canonical_local_only_artifact():
    config = load_vision_config()
    assert config["config_path"] == "runtime/residents/alfred/vision_model_config.json"
    assert config["preferred_model"] == "llama3.2-vision:11b"
    assert config["cloud_allowed"] is False
