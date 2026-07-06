import json
from pathlib import Path

from estate.ai_services.discovery import rediscover
from estate.ai_services.control import request
from estate.ai_services.steward_model_selector import (
    build_steward_ai_services_panel,
    set_assignment,
    set_preference,
    decide_approval,
)


def _manifest(service_id, display, endpoint, port, paths=None, operations=None, approval=None):
    return {
        "service_id": service_id,
        "display_name": display,
        "service_type": "model_runtime",
        "local_only": True,
        "host_policy": {"bind": "127.0.0.1", "allow_public_bind": False},
        "default_endpoint": endpoint,
        "ports": [port],
        "paths": paths or {},
        "operations": operations or {"status": {"api_template": "GET /health"}},
        "approval": approval or {},
    }


def _write(root, name, data):
    p = root / "runtime/ai_services/implementations" / name
    p.mkdir(parents=True)
    (p / "service.manifest.json").write_text(json.dumps(data), encoding="utf-8")


def _seed(root):
    models = root / "models"; models.mkdir(); (models / "Qwen3.gguf").write_text("x")
    _write(root, "textgen", _manifest("textgen", "TextGen", "http://127.0.0.1:5000/v1", 5000, {"models": str(models)}, {"status": {"api_template": "GET /v1/models"}, "load_model": {"command_template": "load {model}"}, "start": {"command_template": "textgen"}, "stop": {"command_template": "stop"}}, {"load_model": {"required": True}, "start": {"required": True}, "stop": {"required": True}}))
    _write(root, "ollama", _manifest("ollama", "Ollama", "http://127.0.0.1:11434", 11434, {"models": str(root / "missing-ollama-models")}, {"status": {"api_template": "GET /api/tags"}, "list_models": {"api_template": "GET /api/tags"}}, {}))
    _write(root, "comfyui", _manifest("comfyui", "ComfyUI", "http://127.0.0.1:8188", 8188))
    _write(root, "open_webui", _manifest("open_webui", "Open WebUI", "http://127.0.0.1:8080", 8080))
    _write(root, "sillytavern", _manifest("sillytavern", "SillyTavern", "http://127.0.0.1:8000", 8000))
    rediscover(root)


def test_steward_ui_data_model_builds_services_models_hooks_and_audit(tmp_path):
    _seed(tmp_path)
    panel = build_steward_ai_services_panel(tmp_path)["data"]
    assert {s["service_id"] for s in panel["services"]} >= {"ollama", "textgen", "comfyui", "open_webui", "sillytavern"}
    assert any(m["backing_service"] == "textgen" and m["source_status"] == "available" for m in panel["models"])
    assert any(m["backing_service"] == "ollama" and m["source_status"] in {"unavailable", "available_hook_unqueried"} for m in panel["models"])
    assert panel["actions"]["rediscover"] == "ai-services rediscover"
    assert panel["actions"]["refresh_status"] == "ai-services status"
    assert panel["audit_tail"]


def test_preferences_validate_or_mark_unresolved_and_assignments_persist(tmp_path):
    _seed(tmp_path)
    prefs = set_preference("estate_preferred_text_model", "textgen:Qwen3.gguf", root=tmp_path)
    assert prefs["preferences"]["estate_preferred_text_model"]["resolution"] == "resolved"
    prefs = set_preference("estate_preferred_vision_model", "textgen:missing.gguf", root=tmp_path)
    assert prefs["preferences"]["estate_preferred_vision_model"]["resolution"] == "unresolved"
    assignments = set_assignment("alfred", "textgen:Qwen3.gguf", root=tmp_path, reason="Alfred text default")
    assert assignments["assignments"]["alfred"]["model_id"] == "textgen:Qwen3.gguf"
    reread = build_steward_ai_services_panel(tmp_path)["data"]["model_assignments"]
    assert reread["assignments"]["alfred"]["resolution"] == "resolved"


def test_alfred_cannot_approve_own_request_but_steward_can_deny(tmp_path):
    _seed(tmp_path)
    request("load_model", "textgen", actor="alfred", root=tmp_path, model="Qwen3.gguf")
    blocked = decide_approval("approved", "load_model", "textgen", actor="alfred", approved_by="alfred", model="Qwen3.gguf", root=tmp_path)
    assert blocked["error"] == "actor_cannot_approve_own_authority_expansion"
    denied = decide_approval("denied", "load_model", "textgen", actor="alfred", approved_by="steward", model="Qwen3.gguf", root=tmp_path)
    assert denied["state"] == "denied"
    panel = build_steward_ai_services_panel(tmp_path)["data"]
    assert any(r["state"] == "denied" for r in panel["approvals"]["requests"])


def test_wp0138_discovers_multiple_gguf_files_directories_and_loaded_separately(tmp_path):
    models = tmp_path / "models"
    models.mkdir()
    for name in ["Qwen3-8B-Q6_K.gguf", "Meta-Llama-3.1-8B-Instruct-Q5_K_M.gguf"]:
        (models / name).write_text("x")
    repo = models / "Weiwei22_WaifuChat-8b"
    repo.mkdir()
    (repo / "config.json").write_text("{}")
    _write(tmp_path, "textgen", _manifest("textgen", "TextGen", "http://127.0.0.1:5000/v1", 5000, {"models": str(models)}, {"status": {"api_template": "GET /v1/models"}, "load_model": {"command_template": "load {model}"}}, {"load_model": {"required": True}}))
    rediscover(tmp_path)
    state = {"version": "ai-services-state-v1", "services": {"textgen": {"status": "running", "loaded_model": "Qwen3-8B-Q6_K.gguf"}}}
    (tmp_path / "runtime/ai_services/state.json").write_text(json.dumps(state), encoding="utf-8")

    panel = build_steward_ai_services_panel(tmp_path)["data"]
    inventory = {m["name"]: m for m in panel["models"] if m["backing_service"] == "textgen"}

    assert inventory["Qwen3-8B-Q6_K.gguf"]["installed"] is True
    assert inventory["Meta-Llama-3.1-8B-Instruct-Q5_K_M.gguf"]["installed"] is True
    assert inventory["Weiwei22_WaifuChat-8b"]["classification_status"] == "huggingface_or_model_directory"
    assert inventory["Qwen3-8B-Q6_K.gguf"]["currently_loaded"] is True
    assert inventory["Meta-Llama-3.1-8B-Instruct-Q5_K_M.gguf"]["currently_loaded"] is False
    assert panel["dashboard"]["known_installed_models"] == 3


def test_wp0138_audit_tail_redacts_secrets_and_is_newest_first(tmp_path):
    _seed(tmp_path)
    audit = tmp_path / "runtime/ai_services/audit_log.jsonl"
    audit.write_text('\n'.join([
        json.dumps({"result": "old", "details": {"api_key": "secret-value"}}),
        json.dumps({"result": "new", "details": {"message": "ok"}}),
    ]), encoding="utf-8")
    tail = build_steward_ai_services_panel(tmp_path)["data"]["audit_tail"]
    assert tail[0]["result"] == "new"
    assert tail[1]["details"]["api_key"] == "[redacted]"
