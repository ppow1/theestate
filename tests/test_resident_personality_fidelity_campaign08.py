from estate.core.resident_gateway import ACTIVE_RESIDENT_MODELS, chat_completion, models_payload
from estate.core.resident_identity_reports import build_conversational_differentiation_report, build_identity_composition_matrix, covered_residents


def test_gateway_exposes_all_live_resident_surfaces_for_open_webui():
    ids = {m["id"] for m in models_payload()["data"]}
    assert {"estate/alfred", "estate/helen", "estate/ingrid", "estate/grace", "estate/evelyn", "estate/eleanor", "estate/marie", "estate/judy"} <= ids
    assert covered_residents() == list(dict.fromkeys(ACTIVE_RESIDENT_MODELS.values()))


def test_every_open_webui_resident_turn_stores_full_identity_stack(tmp_path):
    for resident in covered_residents():
        code, body = chat_completion({"model": f"estate/{resident}", "messages": [{"role": "user", "content": "Who are you, and what boundary should I remember?"}], "metadata": {"session_id": f"fidelity-{resident}"}}, root=tmp_path)
        assert code == 200
        assert body["estate"]["resident_id"] == resident
        stored = (tmp_path / "runtime/resident_interactions/sessions" / f"fidelity-{resident}.json").read_text(encoding="utf-8")
        assert "resident_runtime_identity_composition.v1" in stored
        assert "character_context" in stored
        assert "durable_memory_context" in stored
        assert "relationship_context" in stored


def test_same_question_responses_are_resident_specific_in_fallback(tmp_path):
    responses = {}
    for resident in covered_residents():
        code, body = chat_completion({"model": f"estate/{resident}", "messages": [{"role": "user", "content": "What should I do first when the Estate feels noisy?"}]}, root=tmp_path)
        assert code == 200
        responses[resident] = body["choices"][0]["message"]["content"]
    assert len(set(responses.values())) == len(responses)
    assert "provenance" in responses["eleanor"]
    assert "evidence" in responses["marie"]
    assert "legal risk" in responses["judy"]
    assert "privacy" in responses["ingrid"]


def test_campaign_reports_are_written_and_include_blind_review_artifact(tmp_path):
    matrix = build_identity_composition_matrix(tmp_path, write=True)
    report = build_conversational_differentiation_report(tmp_path, write=True)
    assert len(matrix["rows"]) == len(covered_residents())
    assert all("source_artifacts" in row and row["layers"] for row in matrix["rows"])
    assert report["blind_recognition_review"]
    assert (tmp_path / "runtime/reports/resident_personality_fidelity/identity_composition_matrix.json").exists()
    assert (tmp_path / "runtime/reports/resident_personality_fidelity/conversational_differentiation_report.json").exists()
