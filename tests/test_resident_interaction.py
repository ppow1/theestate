from pathlib import Path
from estate.core.resident_interaction import process_chat, load_history, forget_conversation, resident_surface


def test_alfred_prompt_persists_history_authority_and_versions(tmp_path):
    payload = process_chat("alfred", "What should I look at next?", root=tmp_path)
    turn = payload["turn"]
    assert payload["ok"] is True
    assert turn["llm"]["mode"] in {"local_llm", "deterministic_fallback"}
    assert turn["authority"]["action_executed"] is False
    assert turn["authority"]["authority_status"] in {"within_responsibility", "conversation_only"}
    assert turn["resident_surface"]["resident_api_standard_version"] == "resident-api-standard-v1"
    assert turn["resident_surface"]["resident_implementation_version"] == "alfred-operations-implementation-v1"
    assert (tmp_path / payload["session_path"]).exists()
    history = load_history("alfred", session_id=payload["session_id"], root=tmp_path)
    assert history["sessions"][0]["turns"][0]["turn_id"] == "turn_0001"


def test_forget_redacts_and_suppresses_normal_history(tmp_path):
    payload = process_chat("alfred", "secret local note", root=tmp_path)
    result = forget_conversation(payload["session_id"], root=tmp_path)
    assert result["ok"] is True
    normal = load_history("alfred", session_id=payload["session_id"], root=tmp_path)
    assert normal["sessions"][0]["turns"] == []
    full = load_history("alfred", session_id=payload["session_id"], root=tmp_path, include_forgotten=True)
    assert full["sessions"][0]["turns"][0]["memory_status"] == "forgotten"
    assert "redacted" in full["sessions"][0]["turns"][0]["user_message"]


def test_surface_inspection_supports_future_residents_and_extensions():
    alfred = resident_surface("alfred")
    assert alfred["resident_api_standard_version"] == "resident-api-standard-v1"
    assert alfred["resident_implementation_version"] == "alfred-operations-implementation-v1"
    assert alfred["extension_mechanism"]["proposal_template"].endswith("resident_api_extension_proposal_template.md")
    assert any(c["id"] == "character.mood_arc.evaluate" for c in alfred["capabilities"])
    ingrid = resident_surface("ingrid")
    assert ingrid["resident_id"] == "ingrid"
    assert ingrid["office"] == "Security"


def test_templates_exist():
    for path in [
        "docs/operations/residents/resident_interaction_template.md",
        "docs/operations/residents/resident_api_surface_standard.md",
        "docs/operations/residents/resident_implementation_profile_template.md",
        "docs/operations/residents/resident_api_extension_proposal_template.md",
    ]:
        assert Path(path).is_file()

class MockOllamaAdapter:
    provider = "ollama"
    def __init__(self, endpoint="http://127.0.0.1:11434", timeout=12.0):
        self.endpoint = endpoint
    def discover_models(self):
        return {"available": True, "provider": "ollama", "endpoint": self.endpoint, "models": ["llama3:8b", "qwen3:8b"], "discovery": "mock local Ollama models discovered"}
    def select_model(self, resident, models):
        return "qwen3:8b" if "qwen3:8b" in models else models[0]
    def generate(self, *, resident, prompt, model=None):
        if "running from JSON files or an LLM" in prompt:
            text = f"Pat, this answer is being generated through local_llm with provider ollama and model {model}; JSON artifacts provide context, not the whole response."
        else:
            text = "Pat, my role is Alfred of the Office of Operations: I coordinate local Estate status, recommendations, and proposed next actions without executing privileged work."
        return {"ok": True, "text": text, "metadata": {"mode": "local_llm", "provider": "ollama", "model": model, "endpoint": self.endpoint, "fallback_used": False, "fallback_reason": None}}

class UnavailableOllamaAdapter(MockOllamaAdapter):
    def discover_models(self):
        return {"available": False, "provider": "ollama", "endpoint": self.endpoint, "models": [], "discovery": "mock Ollama unavailable"}
    def generate(self, *, resident, prompt, model=None):
        raise AssertionError("generate should not be called when discovery is unavailable")


def test_local_ollama_adapter_selects_qwen3_for_alfred(monkeypatch):
    from estate.core import resident_interaction as mod
    adapter = MockOllamaAdapter()
    assert adapter.select_model("alfred", ["llama3:8b", "qwen3:8b"]) == "qwen3:8b"
    assert mod.local_llm_status(adapter)["model"] == "qwen3:8b"


def test_process_chat_uses_mocked_local_llm_and_distinguishes_intents(monkeypatch, tmp_path):
    from estate.core import resident_interaction as mod
    monkeypatch.setattr(mod, "LocalOllamaAdapter", MockOllamaAdapter)
    role = process_chat("alfred", "Good afternoon Alfred, define your role for me.", root=tmp_path)
    mode = process_chat("alfred", "Alfred, are you running from JSON files or an LLM right now?", root=tmp_path)
    assert role["turn"]["llm"]["mode"] == "local_llm"
    assert role["turn"]["llm"]["model"] == "qwen3:8b"
    assert mode["turn"]["llm"]["provider"] == "ollama"
    assert "role is Alfred" in role["turn"]["resident_response"]
    assert "local_llm" in mode["turn"]["resident_response"]
    assert role["turn"]["resident_response"] != mode["turn"]["resident_response"]
    assert role["turn"]["authority"]["action_executed"] is False
    assert mode["turn"]["llm"]["fallback_used"] is False


def test_process_chat_falls_back_with_metadata_when_ollama_unavailable(monkeypatch, tmp_path):
    from estate.core import resident_interaction as mod
    monkeypatch.setattr(mod, "LocalOllamaAdapter", UnavailableOllamaAdapter)
    payload = process_chat("alfred", "What should I look at next?", root=tmp_path)
    assert payload["turn"]["llm"]["mode"] == "deterministic_fallback"
    assert payload["turn"]["llm"]["fallback_used"] is True
    assert "mock Ollama unavailable" in payload["turn"]["llm"]["fallback_reason"]
    assert "Recommended next action" in payload["turn"]["resident_response"]

class MockVisionAdapter:
    def discover_models(self):
        return {"available": True, "models": ["llava:latest"], "model": "llava:latest", "vision_capable": True}
    def summarize_image(self, *, image_path, prompt="", model=None):
        return {"ok": True, "status": "processed", "summary": "A mocked screenshot summary.", "provider": "ollama", "model": "llava:latest"}

class NoVisionAdapter(MockVisionAdapter):
    def discover_models(self):
        return {"available": False, "models": [], "model": None, "vision_capable": False}
    def summarize_image(self, *, image_path, prompt="", model=None):
        return {"ok": False, "status": "unavailable", "summary": None, "provider": "none", "model": None, "reason": "no local vision-capable model discovered"}


def test_attachment_metadata_image_persistence_and_turn_link(tmp_path):
    import base64
    png = base64.b64encode(b"\x89PNG\r\n\x1a\nmock").decode("ascii")
    payload = process_chat("alfred", "inspect this", root=tmp_path, attachments=[{"kind":"image","source":"clipboard_paste","mime_type":"image/png","original_filename":"screen.png","data_base64":png}], vision_adapter=MockVisionAdapter())
    att = payload["turn"]["attachments"][0]
    assert att["attachment_id"] == "attach_0001"
    assert att["vision_status"] == "processed"
    assert att["summary"] == "A mocked screenshot summary."
    assert att["storage_path"].startswith("runtime/resident_interactions/attachments/alfred/")
    assert (tmp_path / att["storage_path"]).is_file()
    history = load_history("alfred", session_id=payload["session_id"], root=tmp_path)
    assert history["sessions"][0]["turns"][0]["attachments"][0]["attachment_id"] == "attach_0001"


def test_unsafe_or_unsupported_attachment_payload_rejected(tmp_path):
    import pytest
    with pytest.raises(ValueError):
        process_chat("alfred", "bad", root=tmp_path, attachments=[{"kind":"image","mime_type":"application/pdf","data_base64":"AA=="}])


def test_forget_redacts_attachment_summary(tmp_path):
    import base64
    png = base64.b64encode(b"\x89PNG\r\n\x1a\nmock").decode("ascii")
    payload = process_chat("alfred", "secret image", root=tmp_path, attachments=[{"kind":"image","mime_type":"image/png","data_base64":png}], vision_adapter=MockVisionAdapter())
    forget_conversation(payload["session_id"], root=tmp_path)
    full = load_history("alfred", session_id=payload["session_id"], root=tmp_path, include_forgotten=True)
    att = full["sessions"][0]["turns"][0]["attachments"][0]
    assert att["redaction_status"] == "forgotten"
    assert att["summary"] is None


def test_vision_unavailable_fallback_is_truthful(tmp_path):
    import base64
    png = base64.b64encode(b"\x89PNG\r\n\x1a\nmock").decode("ascii")
    payload = process_chat("alfred", "what is in it?", root=tmp_path, attachments=[{"kind":"image","mime_type":"image/png","data_base64":png}], vision_adapter=NoVisionAdapter())
    att = payload["turn"]["attachments"][0]
    assert att["vision_status"] == "unavailable"
    assert "cannot" in payload["turn"]["resident_response"] or "no local vision" in payload["turn"]["resident_response"] or "no local vision-capable" in payload["turn"]["resident_response"]


def test_wp0130_vision_capable_model_detection_from_name_and_metadata():
    from estate.core.resident_interaction import is_vision_capable_model
    assert is_vision_capable_model("llava:latest") is True
    assert is_vision_capable_model("custom-local", {"details": {"families": ["llama", "clip"]}, "modelfile": "mmproj"}) is True
    assert is_vision_capable_model("qwen3:8b", {"details": {"families": ["llama"]}}) is False


class MultiVisionOllamaAdapter:
    provider = "ollama"
    endpoint = "http://127.0.0.1:11434"
    timeout = 1.0
    def discover_models(self):
        return {"available": True, "provider": "ollama", "endpoint": self.endpoint, "models": ["llava:latest", "llama3.2-vision:11b", "qwen3:8b"]}


def test_wp0130_configured_vision_model_preference_and_no_cloud(tmp_path):
    from estate.core.resident_interaction import LocalVisionAdapter
    cfg = {"provider":"ollama","endpoint":"http://127.0.0.1:11434","preferred_model":"llama3.2-vision:11b","fallback_behavior":"vision_unavailable","cloud_allowed":True,"config_path":"runtime/residents/alfred/vision_model_config.json"}
    status = LocalVisionAdapter(ollama=MultiVisionOllamaAdapter(), config=cfg).discover_models()
    assert status["model"] == "llama3.2-vision:11b"
    assert status["cloud_allowed"] is False
    assert status["vision_capable_models"] == ["llava:latest", "llama3.2-vision:11b"]


def test_wp0130_alfred_uses_vision_summary_in_image_question_response(tmp_path):
    import base64
    png = base64.b64encode(b"\x89PNG\r\n\x1a\nmock").decode("ascii")
    payload = process_chat("alfred", "what do you see?", root=tmp_path, attachments=[{"kind":"image","mime_type":"image/png","data_base64":png}], vision_adapter=MockVisionAdapter())
    assert "A mocked screenshot summary." in payload["turn"]["resident_response"]
    assert payload["turn"]["attachments"][0]["vision_provider"] == "ollama"


def test_wp0130_attachment_metadata_records_unavailable_when_no_model(tmp_path):
    import base64
    png = base64.b64encode(b"\x89PNG\r\n\x1a\nmock").decode("ascii")
    payload = process_chat("alfred", "inspect unavailable", root=tmp_path, attachments=[{"kind":"image","mime_type":"image/png","data_base64":png}], vision_adapter=NoVisionAdapter())
    att = payload["turn"]["attachments"][0]
    assert att["vision_status"] == "unavailable"
    assert att["vision_provider"] == "none"
    assert att["summary"] is None
