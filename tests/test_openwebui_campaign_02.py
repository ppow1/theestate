import json
from pathlib import Path

from estate.core.openwebui_resident_surface import resident_model_catalog, run_validation
from estate.core.resident_gateway import chat_completion, models_payload
from estate.core.resident_voice_commissioning import synthesize_resident_sample


def _seed_visuals(root: Path):
    (root / "data/visuals").mkdir(parents=True)
    rows = [{"resident_id": rid, "display_name": name, "asset_library_status": "manifest_placeholder", "publication_scope": "Estate Internal"} for rid, name in [("alfred","Alfred"),("helen","Helen"),("ingrid","Ingrid"),("grace","Grace"),("evelyn","Evelyn"),("eleanor","Eleanor"),("marie","Marie"),("judy","Judy")]]
    (root / "data/visuals/canonical_visual_registry.json").write_text(json.dumps({"residents": rows}), encoding="utf-8")


def test_catalog_exposes_all_residents_with_honest_avatar_and_voice_states(tmp_path):
    _seed_visuals(tmp_path)
    catalog = resident_model_catalog(tmp_path)
    ids = {m["id"] for m in catalog["data"]}
    assert {"estate/alfred", "estate/helen", "estate/ingrid", "estate/grace", "estate/evelyn", "estate/eleanor", "estate/marie", "estate/judy"} <= ids
    alfred = next(m for m in catalog["data"] if m["id"] == "estate/alfred")
    assert alfred["estate"]["display_name"] == "Alfred"
    assert alfred["estate"]["provider_model_hidden_in_primary_selector"] is True
    assert alfred["estate"]["avatar"]["state"] == "provisional_placeholder"
    assert alfred["estate"]["avatar"]["avatar_path"] is None
    assert alfred["estate"]["voice"]["voice_id"] == "estate-local-alfred-baritone"


def test_gateway_response_exposes_identity_trace_metadata(tmp_path):
    code, body = chat_completion({"model":"estate/judy", "messages":[{"role":"user","content":"Handle uncertainty without bluffing."}]}, root=tmp_path)
    assert code == 200
    assert body["estate"]["resident_id"] == "judy"
    assert body["estate"]["identity_schema_version"] == "resident_runtime_identity_composition.v1"
    assert body["estate"]["identity_hash"]
    assert body["estate"]["voice"]["state"] in {"ready", "binding_present_tts_unavailable", "unavailable"}


def test_tts_unavailable_does_not_create_placeholder_audio(monkeypatch, tmp_path):
    monkeypatch.setenv("PATH", str(tmp_path / "empty-bin"))
    monkeypatch.delenv("ESTATE_TTS_COMMAND", raising=False)
    result = synthesize_resident_sample("alfred", "hello", root=tmp_path, sample_name="no_fake_audio")
    assert result["ok"] is False
    assert result["placeholder_generated"] is False
    assert not (tmp_path / "runtime/voice/listening_samples/alfred/no_fake_audio.wav").exists()


def test_validation_writes_reports_and_review_package(tmp_path, monkeypatch):
    monkeypatch.setenv("PATH", str(tmp_path / "empty-bin"))
    _seed_visuals(tmp_path)
    report = run_validation(tmp_path)
    assert (tmp_path / "collaboration/reports/openwebui_campaign_02/validation_report.json").exists()
    assert (tmp_path / "collaboration/reports/openwebui_campaign_02/VALIDATION_REPORT.md").exists()
    assert (tmp_path / "STEWARD_LIVE_IDENTITY_VOICE_REVIEW.md").exists()
    assert len(report["prompts"]) == 8
    assert report["voice"]["alfred"]["sample"]["placeholder_generated"] is False


def test_models_payload_uses_resident_first_catalog(tmp_path):
    _seed_visuals(tmp_path)
    payload = models_payload(tmp_path)
    alfred = next(m for m in payload["data"] if m["id"] == "estate/alfred")
    assert alfred["estate"]["display_name"] == "Alfred"
    assert "model" not in alfred["estate"]
