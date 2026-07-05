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
