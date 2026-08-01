import json
from pathlib import Path
import jsonschema
from estate.core.steward_help import answer, build_snapshot, render_cheat_sheet

ROOT = Path(__file__).parents[1]

def test_snapshot_schema_sources_and_required_entities():
    snapshot = build_snapshot(ROOT, include_live_probes=False)
    schema = json.loads((ROOT / "schemas/help/current_capabilities_v1.schema.json").read_text())
    jsonschema.Draft202012Validator(schema).validate(snapshot)
    names = {e["name"] for e in snapshot["entities"]}
    assert {"Grace", "Helen", "Engineering", "Qwen Coder", "Whisper", "ComfyUI", "Estate Skills framework", "Repository Health", "Open WebUI / Grace / Resident Gateway"} <= names
    assert snapshot["institutional_acceptance"] == "not_granted"
    assert snapshot["source_references"] and all("sha256" in x for x in snapshot["source_references"])
    assert snapshot["conflicts"]

def test_plain_language_help_never_executes():
    snapshot = build_snapshot(ROOT, include_live_probes=False)
    for request in ["Grace, help.", "Grace, what can we do?", "Grace, show my commands.", "What Skills are available?", "How do I ask for a transcript?"]:
        response = answer(snapshot, request)
        assert response["executed"] is False
        assert response["institutional_acceptance"] == "not_granted"
    skills = answer(snapshot, "Grace, what Skills are available?")
    assert skills["intent"] == "skill_discovery" and skills["executed"] is False

def test_status_distinctions_and_bounded_outcome():
    snapshot = build_snapshot(ROOT, include_live_probes=False)
    by_name = {e["name"]: e for e in snapshot["entities"]}
    assert by_name["Whisper"]["availability"] == "capability_gap"
    assert by_name["Qwen Coder"]["availability"] == "registered_unavailable"
    result = answer(snapshot, "Can we transcribe audio?")
    assert result["matches"][0]["name"] == "Whisper"
    assert "capability gap" in result["plain_language"]
    helen = answer(snapshot, "Helen, do we have a governed transcription capability?", resident="Helen")
    assert helen["matches"][0]["name"] == "Whisper" and helen["executed"] is False

def test_live_response_binds_freshness_and_sources():
    snapshot = build_snapshot(ROOT, include_live_probes=False)
    response = answer(snapshot, "Grace, what can Engineering do right now?")
    assert response["generated_at"] == snapshot["generated_at"]
    assert response["freshness_state"] == snapshot["freshness_state"]
    assert response["source_references"] == snapshot["source_references"]
    assert response["executed"] is False

def test_ambiguous_request_fails_closed_and_cheat_sheet_is_readable():
    snapshot = build_snapshot(ROOT, include_live_probes=False)
    result = answer(snapshot, "Can we generate?")
    assert result["executed"] is False
    assert result.get("ambiguous") is True or len(result["matches"]) != 1
    sheet = render_cheat_sheet(snapshot)
    assert "What is operational now" in sheet
    assert "Known limits" in sheet
    assert "not_granted" in sheet

def test_resident_conversation_routes_help_without_generation(tmp_path, monkeypatch):
    from estate.core import resident_interaction
    snapshot = build_snapshot(ROOT, include_live_probes=False)
    monkeypatch.setattr(resident_interaction, "build_steward_help_snapshot", lambda _root: snapshot)
    result = resident_interaction.process_chat("grace", "Grace, what Skills are available?", root=tmp_path, session_id="help-acceptance")
    assert result["turn"]["help_surface"]["executed"] is False
    assert result["turn"]["help_surface"]["freshness_state"] == snapshot["freshness_state"]
    assert result["turn"]["llm"]["mode"] == "steward_help_snapshot"
