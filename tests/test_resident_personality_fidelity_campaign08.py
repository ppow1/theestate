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


def test_character_behavior_is_source_linked_and_provider_ready():
    from estate.core.resident_identity_composition import compose_resident_identity

    for resident in covered_residents():
        composition = compose_resident_identity(resident, surface_id="open-webui-single-resident")
        character = next(layer for layer in composition["included_context_layers"] if layer["layer"] == "character_context")
        assert character["content"]["behavior_profile"]["office"]
        assert any(source["source"] == "data/character-architecture/resident_behavior_profiles_v0_1.json" for source in character["sources"])
        assert "Canonical character and behavior" in composition["provider_ready_context"]
        assert "vocabulary_and_cadence" in composition["provider_ready_context"]


def test_direct_and_conference_room_use_identical_resident_behavior(tmp_path):
    question = "What should I do first when the Estate feels noisy?"
    for resident in ("alfred", "helen", "ingrid", "grace"):
        direct = chat_completion({"model": f"estate/{resident}", "messages": [{"role": "user", "content": question}]}, root=tmp_path)[1]
        room = chat_completion({"model": "estate/conference-room", "messages": [{"role": "user", "content": question}], "metadata": {"resident_targets": [resident], "session_id": f"parity-{resident}"}}, root=tmp_path)[1]
        direct_text = direct["choices"][0]["message"]["content"]
        room_text = room["estate"]["resident_turns"][0]["content"]
        assert direct_text == room_text
        assert len(room["estate"]["resident_turns"]) == 1


def test_personality_survives_continued_and_rehydrated_session(tmp_path):
    payload = {"model": "estate/ingrid", "messages": [{"role": "user", "content": "Give me a safe first step."}], "metadata": {"session_id": "continuity-ingrid"}}
    first = chat_completion(payload, root=tmp_path)[1]
    second = chat_completion(payload, root=tmp_path)[1]
    assert "minimum-necessary" in first["choices"][0]["message"]["content"]
    assert first["choices"][0]["message"]["content"] == second["choices"][0]["message"]["content"]
    import json
    stored = json.loads((tmp_path / "runtime/resident_interactions/sessions/continuity-ingrid.json").read_text())
    assert len(stored["turns"]) == 2
    assert all("behavior_profile" in str(turn["identity_composition"]) for turn in stored["turns"])
