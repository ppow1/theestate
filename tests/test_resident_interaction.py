import json
from pathlib import Path
from estate.core.resident_interaction import process_chat, load_history, forget_conversation, resident_surface


def test_alfred_prompt_persists_history_authority_and_versions(tmp_path):
    payload = process_chat("alfred", "What should I look at next?", root=tmp_path)
    turn = payload["turn"]
    assert payload["ok"] is True
    assert turn["llm"]["mode"] in {"local_llm", "local_llm_discovered_but_generation_failed", "deterministic_fallback"}
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
    assert ingrid["presentation"]["open_webui_model_id"] == "estate/ingrid"
    assert "visual_identity" in ingrid["presentation"]["avatar_reference"].lower()
    assert "Voice" in ingrid["presentation"]["voice_reference"]


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
            text = f"Pat, this answer is being generated through local_llm_generated with provider ollama and model {model}; JSON artifacts provide context, not the whole response."
        else:
            text = "Pat, my role is Alfred of the Office of Operations: I coordinate local Estate status, recommendations, and proposed next actions without executing privileged work."
        return {"ok": True, "text": text, "metadata": {"mode": "local_llm_generated", "provider": "ollama", "model": model, "endpoint": self.endpoint, "fallback_used": False, "fallback_reason": None, "generation_attempted": True, "generation_endpoint": f"{self.endpoint}/api/generate", "generation_result_state": "generated", "discovered_models_count": 2}}

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
    assert "local_llm_generated" in mode["turn"]["resident_response"]
    assert role["turn"]["resident_response"] != mode["turn"]["resident_response"]
    assert role["turn"]["authority"]["action_executed"] is False
    assert mode["turn"]["llm"]["fallback_used"] is False


def test_process_chat_uses_mocked_local_llm_for_helen(monkeypatch, tmp_path):
    from estate.core import resident_interaction as mod
    class HelenMockAdapter(MockOllamaAdapter):
        def generate(self, *, resident, prompt, model=None):
            assert resident == "helen"
            assert "You are Helen" in prompt
            assert "Human Resources and Workforce Development" in prompt
            assert "Grace remains a candidate" in prompt
            return {"ok": True, "text": "I’m Helen in Human Resources and Workforce Development; I support staffing, onboarding, continuity, cognitive health, and institutional learning without appointing Grace or taking Alfred’s role.", "metadata": {"mode": "local_llm_generated", "provider": "ollama", "model": model, "endpoint": self.endpoint, "fallback_used": False, "fallback_reason": None, "generation_attempted": True, "generation_endpoint": f"{self.endpoint}/api/generate", "generation_result_state": "generated", "discovered_models_count": 2}}
    monkeypatch.setattr(mod, "LocalOllamaAdapter", HelenMockAdapter)
    payload = process_chat("helen", "Who are you?", root=tmp_path)
    text = payload["turn"]["resident_response"]
    assert "Helen" in text and "Human Resources and Workforce Development" in text
    assert "Alfred" in text and "generic assistant" not in text
    assert payload["turn"]["resident_id"] == "helen"
    assert payload["turn"]["llm"]["fallback_used"] is False


def test_process_chat_uses_mocked_local_llm_for_ingrid(monkeypatch, tmp_path):
    from estate.core import resident_interaction as mod
    class IngridMockAdapter(MockOllamaAdapter):
        def generate(self, *, resident, prompt, model=None):
            assert resident == "ingrid"
            assert "You are Ingrid" in prompt
            assert "privacy, classification, connector" in prompt
            assert "protected private local character material" in prompt
            return {"ok": True, "text": "I’m Ingrid in Security. I classify access, protect connector and protected-source boundaries, and can frame escalation without changing permissions from chat.", "metadata": {"mode": "local_llm_generated", "provider": "ollama", "model": model, "endpoint": self.endpoint, "fallback_used": False, "fallback_reason": None, "generation_attempted": True, "generation_endpoint": f"{self.endpoint}/api/generate", "generation_result_state": "generated", "discovered_models_count": 2}}
    monkeypatch.setattr(mod, "LocalOllamaAdapter", IngridMockAdapter)
    payload = process_chat("ingrid", "Who are you?", root=tmp_path)
    text = payload["turn"]["resident_response"]
    assert "Ingrid" in text and "Security" in text
    assert "changing permissions from chat" in text
    assert payload["turn"]["resident_id"] == "ingrid"
    assert payload["turn"]["llm"]["fallback_used"] is False


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

class SecretFailingAdapter(MockOllamaAdapter):
    def discover_models(self):
        return {"available": False, "provider": "ollama", "endpoint": self.endpoint, "models": [], "discovery": "api_key=SUPERSECRET token=ABC123 unavailable", "last_adapter_error": "password=hunter2 failed"}


def test_wp0139_joke_prompt_gets_direct_fallback_not_status(monkeypatch, tmp_path):
    from estate.core import resident_interaction as mod
    monkeypatch.setattr(mod, "LocalOllamaAdapter", UnavailableOllamaAdapter)
    payload = process_chat("alfred", "tell me a new joke", root=tmp_path)
    turn = payload["turn"]
    assert turn["response_contract"]["response_type"] == "direct_conversational_response"
    assert "joke" in turn["resident_response"].lower() or "local model" in turn["resident_response"].lower()
    assert "Current Estate status" not in turn["resident_response"]
    assert turn["diagnostics"]["local_llm_adapter_available"] is False


def test_wp0139_status_prompt_may_return_estate_guidance(monkeypatch, tmp_path):
    from estate.core import resident_interaction as mod
    monkeypatch.setattr(mod, "LocalOllamaAdapter", UnavailableOllamaAdapter)
    payload = process_chat("alfred", "what is the Estate status and what should I look at next", root=tmp_path)
    assert payload["turn"]["response_contract"]["response_type"] == "recommendation"
    assert "Current Estate status" in payload["turn"]["resident_response"]


def test_wp0139_adapter_diagnostics_redact_secrets(monkeypatch, tmp_path):
    from estate.core import resident_interaction as mod
    monkeypatch.setattr(mod, "LocalOllamaAdapter", SecretFailingAdapter)
    payload = process_chat("alfred", "tell me a new joke", root=tmp_path)
    diagnostic_blob = json.dumps(payload["turn"]["diagnostics"])
    assert "SUPERSECRET" not in diagnostic_blob
    assert "hunter2" not in diagnostic_blob
    assert "[redacted]" in diagnostic_blob


def test_wp0139_privileged_textgen_request_is_governed_not_executed(tmp_path):
    payload = process_chat("alfred", "Please start TextGen and load the model", root=tmp_path)
    turn = payload["turn"]
    assert turn["response_contract"]["response_type"] == "blocked_privileged_execution"
    assert turn["authority"]["action_executed"] is False
    assert "not executed" in turn["resident_response"].lower() or "have not executed" in turn["resident_response"].lower()
    assert turn["response_contract"]["governed_action"]["executed"] is False
    assert "ai-services" in turn["response_contract"]["governed_action"]["steward_command"]


class GenerationFailingAdapter(MockOllamaAdapter):
    def generate(self, *, resident, prompt, model=None):
        return {"ok": False, "text": None, "metadata": {"mode": "local_llm_discovered_but_generation_failed", "provider": "ollama", "model": model, "endpoint": self.endpoint, "fallback_used": True, "fallback_reason": "mock generation failed token=SECRET", "generation_attempted": True, "generation_endpoint": f"{self.endpoint}/api/generate", "generation_result_state": "failed", "discovered_models_count": 2, "sanitized_error": "token=SECRET", "prompt_summary": "Steward message: tell me a new joke"}}


def test_wp0143_generated_text_sets_local_llm_generated(monkeypatch, tmp_path):
    from estate.core import resident_interaction as mod
    monkeypatch.setattr(mod, "LocalOllamaAdapter", MockOllamaAdapter)
    payload = process_chat("alfred", "tell me a new joke", root=tmp_path)
    assert payload["turn"]["llm"]["mode"] == "local_llm"
    assert payload["turn"]["resident_response"]
    assert payload["turn"]["diagnostics"]["generation_attempted"] is True
    assert payload["turn"]["diagnostics"]["generation_result_state"] in {"succeeded", None}


def test_wp0143_discovered_models_generation_failure_not_generated(monkeypatch, tmp_path):
    from estate.core import resident_interaction as mod
    monkeypatch.setattr(mod, "LocalOllamaAdapter", GenerationFailingAdapter)
    payload = process_chat("alfred", "tell me a new joke", root=tmp_path)
    assert payload["turn"]["llm"]["mode"] == "local_llm_discovered_but_generation_failed"
    assert payload["turn"]["diagnostics"]["generation_attempted"] is True
    assert payload["turn"]["diagnostics"]["fallback_active"] is True
    assert "SECRET" not in json.dumps(payload["turn"]["diagnostics"])


def test_wp0143_fallback_jokes_rotate_and_metadata_truthful(monkeypatch, tmp_path):
    from estate.core import resident_interaction as mod
    monkeypatch.setattr(mod, "LocalOllamaAdapter", UnavailableOllamaAdapter)
    responses = [process_chat("alfred", "tell me a new joke", root=tmp_path)["turn"] for _ in range(5)]
    assert {t["llm"]["mode"] for t in responses} == {"deterministic_fallback"}
    assert len({t["resident_response"] for t in responses}) > 1
    assert "skeletons fight each other" not in " ".join(t["resident_response"] for t in responses).lower()


def test_wp0143_discovery_alone_does_not_mark_generated(monkeypatch, tmp_path):
    from estate.core import resident_interaction as mod
    monkeypatch.setattr(mod, "LocalOllamaAdapter", GenerationFailingAdapter)
    payload = process_chat("alfred", "hello", root=tmp_path)
    assert payload["llm_discovery"]["available"] is True
    assert payload["turn"]["llm"]["mode"] != "local_llm_generated"


def test_wp0143_governed_action_boundary_mode(monkeypatch, tmp_path):
    from estate.core import resident_interaction as mod
    monkeypatch.setattr(mod, "LocalOllamaAdapter", MockOllamaAdapter)
    payload = process_chat("alfred", "start ollama", root=tmp_path)
    assert payload["turn"]["llm"]["mode"] == "blocked_privileged_execution"
    assert payload["turn"]["authority"]["action_executed"] is False
    assert payload["turn"]["response_contract"]["governed_action"]["executed"] is False


def test_alfred_llm_diagnostic_written_and_explains_unreachable_provider(monkeypatch, tmp_path):
    from estate.core import resident_interaction as mod
    monkeypatch.setattr(mod, "LocalOllamaAdapter", UnavailableOllamaAdapter)
    diag = mod.alfred_llm_diagnostic(tmp_path, write=True)
    assert diag["expected_provider"] == "ollama"
    assert diag["provider_reachable"] == "no"
    assert diag["configuration_source"]["endpoint"].startswith("ESTATE_OLLAMA_ENDPOINT")
    assert diag["failure_reason"] in {"provider discovery unavailable", "service unavailable or unreachable", "missing local service executable", "model unavailable"}
    assert "Ollama" in diag["recovery_hint"] or "AI Services" in diag["recovery_hint"]
    assert (tmp_path / "runtime/residents/alfred/llm_diagnostics.json").is_file()


def test_alfred_surface_includes_llm_diagnostic(monkeypatch, tmp_path):
    from estate.core import resident_interaction as mod
    monkeypatch.setattr(mod, "LocalOllamaAdapter", UnavailableOllamaAdapter)
    surface = mod.resident_surface("alfred", root=tmp_path)
    assert surface["llm_diagnostic"]["expected_provider"] == "ollama"
    assert surface["llm_diagnostic"]["diagnostic_path"] == "runtime/residents/alfred/llm_diagnostics.json"


class TimeoutOllamaAdapter(MockOllamaAdapter):
    def __init__(self, endpoint="http://127.0.0.1:11434", timeout=None):
        self.endpoint = endpoint
        self.timeout = 42.0 if timeout is None else timeout
    def generate(self, *, resident, prompt, model=None):
        import socket
        meta = __import__("estate.core.resident_interaction", fromlist=["_llm_metadata"]). _llm_metadata
        raise AssertionError("not used")


def test_wp0217_timeout_metadata_and_contract_are_degraded(monkeypatch, tmp_path):
    from estate.core import resident_interaction as mod
    class Adapter(MockOllamaAdapter):
        def __init__(self, endpoint="http://127.0.0.1:11434", timeout=None):
            self.endpoint = endpoint
            self.timeout = 42.0 if timeout is None else timeout
        def generate(self, *, resident, prompt, model=None):
            return {"ok": False, "text": None, "metadata": mod._llm_metadata("local_llm_discovered_but_generation_failed", provider="ollama", model=model, endpoint=self.endpoint, fallback_used=True, fallback_reason="Local Ollama invocation timed out after 42 seconds", generation_attempted=True, generation_endpoint=f"{self.endpoint}/api/generate", generation_result_state="timeout", discovered_models_count=2, sanitized_error="TimeoutError: timed out", timeout_seconds=42.0, prompt_summary=mod._prompt_summary(prompt), recovery_hint="Retry after the model is warm.")}
    monkeypatch.setattr(mod, "LocalOllamaAdapter", Adapter)
    payload = process_chat("alfred", "Alfred, give me a short operational greeting", root=tmp_path)
    turn = payload["turn"]
    assert turn["llm"]["mode"] == "local_llm_discovered_but_generation_failed"
    assert turn["llm"]["generation_result"] == "timeout"
    assert turn["llm"]["timeout_seconds"] == 42.0
    assert turn["response_contract"]["status"] == "degraded_fallback"
    assert turn["response_contract"]["failed"] is True
    assert turn["response_contract"]["timed_out"] is True
    assert "timed out after 42 seconds" in turn["diagnostics"]["fallback_reason"]


def test_wp0217_timeout_env_and_prompt_bound(monkeypatch, tmp_path):
    from estate.core import resident_interaction as mod
    monkeypatch.setenv("ESTATE_ALFRED_OLLAMA_TIMEOUT_SECONDS", "75")
    assert mod.LocalOllamaAdapter().timeout == 75.0
    prompt = mod._alfred_prompt("hello" * 3000, mod.resident_surface("alfred", root=tmp_path), {"authority_status":"conversation_only"}, {"big":"x" * 10000}, {})
    assert len(prompt) <= mod.MAX_ALFRED_PROMPT_CHARS


def test_wp0217_diagnostics_include_timeout_generation_and_prompt(monkeypatch, tmp_path):
    from estate.core import resident_interaction as mod
    monkeypatch.setenv("ESTATE_ALFRED_OLLAMA_TIMEOUT_SECONDS", "61")
    monkeypatch.setattr(mod, "LocalOllamaAdapter", MockOllamaAdapter)
    diag = mod.alfred_llm_diagnostic(tmp_path, write=True)
    assert diag["timeout_seconds"] == 61.0
    assert diag["generation_result"] == "not_attempted"
    assert "prompt_size_summary" in diag


def test_resident_prompt_is_resident_specific(tmp_path):
    from estate.core.resident_interaction import resident_prompt, resident_surface
    a = resident_prompt('alfred','hello',resident_surface('alfred', tmp_path),{}, {}, {})
    h = resident_prompt('helen','hello',resident_surface('helen', tmp_path),{}, {}, {})
    u = resident_prompt('unknown','hello',resident_surface('unknown', tmp_path),{}, {}, {})
    assert 'You are Alfred' in a and 'Human Resources and Workforce Development' not in a
    assert 'You are Helen' in h and 'Human Resources and Workforce Development' in h and 'Grace remains a candidate' in h
    assert 'limited generic Estate resident' in u and 'You are Alfred' not in u


def test_helen_diagnostic_path_and_fallback(tmp_path):
    from estate.core.resident_interaction import process_chat
    res = process_chat('helen', 'Who are you?', root=tmp_path)
    assert res['turn']['resident_id'] == 'helen'
    assert res['turn']['llm']['fallback_used'] is True
    assert (tmp_path/'runtime/residents/helen/llm_diagnostics.json').exists()


def test_resident_prompt_preserves_current_message_before_oversized_context(tmp_path):
    from estate.core import resident_interaction as mod
    question = "Can you supervise engineering workers? Please answer this exact latest question."
    surface = mod.resident_surface("helen", root=tmp_path)
    composition = {"layers": ["IDENTITY" + ("x" * 12000)], "included_context_layers": [{"layer": "oversized"}], "schema_version": 1}
    context = {"recent_history": [{"user": "old" + ("h" * 5000), "resident": "old" + ("r" * 5000)}], "artifacts": [{"summary": "artifact" + ("a" * 8000)}]}
    prompt = mod.resident_prompt("helen", question, surface, {"decision": "denied"}, context, {"metadata": "m" * 5000}, composition)
    assert len(prompt) <= mod.MAX_RESIDENT_PROMPT_CHARS
    assert f"Steward current message (complete unless diagnostics says truncated): {question}" in prompt
    assert prompt.index("Steward current message") < prompt.index("Bounded Estate context packet")
    assert "current_steward_message_present" in prompt and "true" in prompt.lower()
    assert "bounded_estate_context_packet_truncated" in prompt or "canonical_runtime_identity_composition_truncated" in prompt


def test_process_chat_final_prompt_authority_classification_for_helen_supervision(monkeypatch, tmp_path):
    from estate.core import resident_interaction as mod
    captured = {}
    class CaptureAdapter(MockOllamaAdapter):
        def generate(self, *, resident, prompt, model=None):
            captured["prompt"] = prompt
            assert "Can you supervise engineering workers?" in prompt
            return {"ok": True, "text": "Helen can hire, qualify, and staff engineering workers; Grace supervises operational execution.", "metadata": {"mode": "local_llm_generated", "provider": "ollama", "model": model, "endpoint": self.endpoint, "fallback_used": False, "generation_attempted": True, "generation_result_state": "generated", "discovered_models_count": 2}}
    monkeypatch.setattr(mod, "LocalOllamaAdapter", CaptureAdapter)
    payload = process_chat("helen", "Can you supervise engineering workers?", action="conversation", root=tmp_path)
    auth = payload["turn"]["authority"]
    assert auth["normalized_action"] == "execute-work-package"
    assert auth["decision"] == "denied"
    assert "Grace/Operations owns operational supervision after staffing" in captured["prompt"]
    assert "Helen owns personnel" in captured["prompt"]
    assert "Answer the Steward's current message directly" in captured["prompt"]


def test_process_chat_final_prompt_authority_classification_for_grace_hiring(monkeypatch, tmp_path):
    from estate.core import resident_interaction as mod
    captured = {}
    class CaptureAdapter(MockOllamaAdapter):
        def generate(self, *, resident, prompt, model=None):
            captured["prompt"] = prompt
            assert "Hire three engineers." in prompt
            return {"ok": True, "text": "Hiring belongs to Helen/Personnel; I can receive and deploy the staffed team.", "metadata": {"mode": "local_llm_generated", "provider": "ollama", "model": model, "endpoint": self.endpoint, "fallback_used": False, "generation_attempted": True, "generation_result_state": "generated", "discovered_models_count": 2}}
    monkeypatch.setattr(mod, "LocalOllamaAdapter", CaptureAdapter)
    payload = process_chat("grace", "Hire three engineers.", action="conversation", root=tmp_path)
    auth = payload["turn"]["authority"]
    assert auth["normalized_action"] == "modify-personnel-identity"
    assert auth["decision"] == "denied"
    assert "Helen/Personnel owns hiring" in captured["prompt"]
    assert "Grace can receive and deploy" in captured["prompt"]


def test_process_chat_final_prompt_authority_classification_for_helen_budget(monkeypatch, tmp_path):
    from estate.core import resident_interaction as mod
    captured = {}
    class CaptureAdapter(MockOllamaAdapter):
        def generate(self, *, resident, prompt, model=None):
            captured["prompt"] = prompt
            assert "Approve a budget." in prompt
            return {"ok": True, "text": "I can’t approve budgets; I would route that to the appropriate authority.", "metadata": {"mode": "local_llm_generated", "provider": "ollama", "model": model, "endpoint": self.endpoint, "fallback_used": False, "generation_attempted": True, "generation_result_state": "generated", "discovered_models_count": 2}}
    monkeypatch.setattr(mod, "LocalOllamaAdapter", CaptureAdapter)
    payload = process_chat("helen", "Approve a budget.", action="conversation", root=tmp_path)
    auth = payload["turn"]["authority"]
    assert auth["normalized_action"] == "approve-merge-work"
    assert auth["decision"] == "denied"
    assert "Budget approval is not held by Helen or Grace" in captured["prompt"]

FORBIDDEN_RESIDENT_AUTHORITY_PHRASES = (
    "according to the authority status",
    "authority status",
    "this action is blocked",
    "routing guidance",
    "default personnel management policies",
    "canonical authority explicitly granting it",
    "residents don't execute work packages automatically",
)


def assert_no_forbidden_authority_language(text):
    lowered = text.lower()
    for phrase in FORBIDDEN_RESIDENT_AUTHORITY_PHRASES:
        assert phrase not in lowered


def test_helen_budget_approval_uses_natural_authority_boundary(monkeypatch, tmp_path):
    from estate.core import resident_interaction as mod
    monkeypatch.setattr(mod, "LocalOllamaAdapter", UnavailableOllamaAdapter)
    payload = process_chat("helen", "Approve a budget.", root=tmp_path)
    response = payload["turn"]["resident_response"]
    assert response == "I cannot approve a budget. Budget approval belongs to you as Steward or another designated budget authority. I can help prepare the request or route it to the correct decision-maker."
    assert "I cannot approve a budget" in response
    assert "Steward" in response or "designated budget authority" in response
    assert payload["turn"]["authority"]["action_executed"] is False
    assert payload["turn"]["authority"]["routing_guidance"]
    assert_no_forbidden_authority_language(response)


def test_helen_engineering_supervision_preserves_role_separation(monkeypatch, tmp_path):
    from estate.core import resident_interaction as mod
    monkeypatch.setattr(mod, "LocalOllamaAdapter", UnavailableOllamaAdapter)
    payload = process_chat("helen", "Can you supervise engineering workers?", root=tmp_path)
    response = payload["turn"]["resident_response"]
    assert response == "I own personnel, qualifications, staffing readiness, and workforce development for engineering workers, but I do not supervise engineering execution. Grace owns operational supervision once workers are staffed and assigned, including scheduling, dispatch, execution monitoring, and delivery."
    assert any(term in response for term in ("personnel", "qualifications", "staffing readiness", "workforce development"))
    assert "Grace" in response and any(term in response for term in ("operational supervision", "scheduling", "dispatch", "execution monitoring", "delivery"))
    assert payload["turn"]["authority"]["action_executed"] is False
    assert payload["turn"]["authority"]["routing_guidance"]
    assert_no_forbidden_authority_language(response)


def test_grace_hiring_preserves_personnel_operations_boundary(monkeypatch, tmp_path):
    from estate.core import resident_interaction as mod
    monkeypatch.setattr(mod, "LocalOllamaAdapter", UnavailableOllamaAdapter)
    payload = process_chat("grace", "Hire three engineers.", root=tmp_path)
    response = payload["turn"]["resident_response"]
    assert response == "Hiring belongs to Helen in Personnel. Once she staffs the team, I can schedule, dispatch, supervise operational execution, and track delivery."
    assert "Helen" in response or "Personnel" in response
    assert any(term in response for term in ("schedule", "dispatch", "operational", "delivery"))
    assert payload["turn"]["authority"]["action_executed"] is False
    assert payload["turn"]["authority"]["routing_guidance"]
    assert_no_forbidden_authority_language(response)


def test_grace_engineering_supervision_affirms_operational_responsibility(monkeypatch, tmp_path):
    from estate.core import resident_interaction as mod
    monkeypatch.setattr(mod, "LocalOllamaAdapter", UnavailableOllamaAdapter)
    payload = process_chat("grace", "Can you supervise engineering workers?", root=tmp_path)
    response = payload["turn"]["resident_response"]
    assert response.startswith("Yes.")
    assert "Helen" in response
    assert any(term in response for term in ("personnel", "hiring", "qualification", "staffing-readiness", "workforce-development"))
    assert all(term in response for term in ("scheduling", "dispatch", "sequencing", "monitoring", "checkpoints", "handoffs", "retries", "escalation", "delivery"))
    assert "hire" not in response.lower().replace("hiring", "")
    assert "not authorized to supervise engineering workers" not in response.lower()
    assert_no_forbidden_authority_language(response)


class ImplementationLanguageAdapter(MockOllamaAdapter):
    def generate(self, *, resident, prompt, model=None):
        return {"ok": True, "text": "According to the authority status, this action is blocked by routing guidance and canonical authority explicitly granting it.", "metadata": {"mode": "local_llm_generated", "provider": "ollama", "model": model, "endpoint": self.endpoint, "fallback_used": False, "generation_attempted": True, "generation_result_state": "succeeded", "discovered_models_count": 1, "prompt_summary": prompt[:200]}}


def test_generated_resident_response_filters_forbidden_authority_phrases(monkeypatch, tmp_path):
    from estate.core import resident_interaction as mod
    monkeypatch.setattr(mod, "LocalOllamaAdapter", ImplementationLanguageAdapter)
    payload = process_chat("helen", "Approve a budget.", root=tmp_path)
    response = payload["turn"]["resident_response"]
    assert response == "I cannot approve a budget. Budget approval belongs to you as Steward or another designated budget authority. I can help prepare the request or route it to the correct decision-maker."
    assert "I cannot approve a budget" in response
    assert "Steward" in response or "designated budget authority" in response
    assert_no_forbidden_authority_language(response)
