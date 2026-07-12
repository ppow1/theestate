from estate.core.multi_resident_room import (
    STAGED_WORK_IS_INSTALLED,
    accept_participant,
    create_room,
    execute_privileged_action,
    invite_participant,
    plan_resident_turns,
    submit_user_turn,
)
from estate.core.resident_gateway import chat_completion, models_payload
from estate.core.evelyn_relationship_runtime import ContinuityRecord, EvelynRelationshipRuntime


def test_room_core_is_installed_and_blocks_privileged_actions():
    room = create_room(display_name="Daily room", created_by="pat", created_at="2026-07-12T00:00:00Z")
    room = invite_participant(room, participant_id="alfred", kind="resident", display_name="Alfred")
    room = accept_participant(room, "alfred")
    room = submit_user_turn(room, text="status?", submitted_by="pat", idempotency_key="one")
    plans = plan_resident_turns(room, room["pending_questions"][0]["user_turn_id"])
    assert STAGED_WORK_IS_INSTALLED is True
    assert plans[0]["resident_id"] == "alfred"
    assert execute_privileged_action(room, "appoint")["executed"] is False


def test_gateway_exposes_evelyn_and_room_model_and_room_routes_canonically(tmp_path):
    ids = {m["id"] for m in models_payload()["data"]}
    assert {"estate/evelyn", "estate/conference-room"} <= ids
    code, body = chat_completion({"model": "estate/conference-room", "messages": [{"role": "user", "content": "Who is here?"}], "metadata": {"resident_targets": ["evelyn", "ingrid"], "session_id": "room-test"}}, root=tmp_path)
    assert code == 200
    assert body["estate"]["attribution_preserved"] is True
    assert body["estate"]["privileged_action_executed"] is False
    assert "Evelyn" in body["choices"][0]["message"]["content"]
    assert "Ingrid" in body["choices"][0]["message"]["content"]


def test_evelyn_relationship_runtime_restricts_private_context(tmp_path):
    runtime = EvelynRelationshipRuntime(tmp_path)
    runtime.propose_record(ContinuityRecord(record_id="r1", category="private_conversation", summary="private detail"))
    assert runtime.build_context(audience="alfred")["private_content_exposed"] is False
    report = runtime.evaluate_turn.__self__.diagnostics()
    assert report["raw_private_content_in_diagnostics"] is False
