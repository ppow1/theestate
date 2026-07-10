from estate.core.resident_interaction import load_history, process_chat, retry_failed_response
from estate.core.steward_command_center import generate_command_center, render_command_center_html


class FailingAfterDiscoveryAdapter:
    provider = "ollama"
    endpoint = "http://127.0.0.1:11434"

    def __init__(self, *_, **__):
        self.timeout = 1.0

    def discover_models(self):
        return {"available": True, "provider": self.provider, "endpoint": self.endpoint, "models": ["qwen3:8b"], "model": "qwen3:8b", "discovery": "mock model discovered"}

    def select_model(self, resident, models, capability="text", root=None):
        return models[0]

    def generate(self, *, resident, prompt, model=None):
        return {"ok": False, "text": None, "metadata": {"mode": "local_llm_discovered_but_generation_failed", "provider": self.provider, "model": model, "endpoint": self.endpoint, "fallback_used": True, "fallback_reason": "mock transport failure", "generation_attempted": True, "generation_endpoint": f"{self.endpoint}/api/generate", "generation_result_state": "failed", "discovered_models_count": 1}}


class SuccessfulAdapter(FailingAfterDiscoveryAdapter):
    def generate(self, *, resident, prompt, model=None):
        return {"ok": True, "text": "Recovered Alfred response", "metadata": {"mode": "local_llm_generated", "provider": self.provider, "model": model, "endpoint": self.endpoint, "fallback_used": False, "fallback_reason": None, "generation_attempted": True, "generation_endpoint": f"{self.endpoint}/api/generate", "generation_result_state": "succeeded", "discovered_models_count": 1}}


def test_wp0515_alfred_composer_is_primary_and_controls_are_truthful(tmp_path):
    payload = generate_command_center(root=tmp_path, write=False)
    html = render_command_center_html(payload)
    alfred_panel = html.split("id='workspace-alfred'", 1)[1].split("id='workspace-helen'", 1)[0]
    assert alfred_panel.index('id="alfred-chat-form"') < alfred_panel.index('office-actions')
    assert "Enter sends, Shift+Enter inserts a new line" in html
    assert "Stop/cancel is not shown" in html
    assert "data-alfred-action=\"history\"" in html
    assert "data-alfred-action=\"forget\"" in html
    assert "data-office-action=\"alfred.request_briefing\"" in html
    assert "data-alfred-retry-session" in html
    assert "ESTATE_OPEN_WEBUI_URL" in html
    assert "requestSubmit()" in html


def test_wp0515_retry_failed_turn_appends_once_and_refuses_success(monkeypatch, tmp_path):
    from estate.core import resident_interaction as mod

    monkeypatch.setattr(mod, "LocalOllamaAdapter", FailingAfterDiscoveryAdapter)
    failed = process_chat("alfred", "Please fail locally", root=tmp_path)
    assert failed["turn"]["response_contract"]["failed"] is True

    monkeypatch.setattr(mod, "LocalOllamaAdapter", SuccessfulAdapter)
    retried = retry_failed_response("alfred", failed["session_id"], failed["turn"]["turn_id"], root=tmp_path)
    assert retried["ok"] is True
    assert retried["retry"]["retried_turn_id"] == failed["turn"]["turn_id"]
    assert retried["turn"]["resident_response"] == "Recovered Alfred response"

    history = load_history("alfred", session_id=failed["session_id"], root=tmp_path)
    assert [t["turn_id"] for t in history["sessions"][0]["turns"]] == ["turn_0001", "turn_0002"]

    refused = retry_failed_response("alfred", failed["session_id"], retried["turn"]["turn_id"], root=tmp_path)
    assert refused["ok"] is False
    assert refused["error"] == "turn_not_failed"
    assert refused["duplicated_successful_turn"] is False
    assert len(load_history("alfred", session_id=failed["session_id"], root=tmp_path)["sessions"][0]["turns"]) == 2
