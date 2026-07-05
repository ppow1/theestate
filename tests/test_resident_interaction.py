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
