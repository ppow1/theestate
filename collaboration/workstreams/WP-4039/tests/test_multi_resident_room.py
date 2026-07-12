import importlib.util
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "src" / "multi_resident_room.py"
spec = importlib.util.spec_from_file_location("multi_resident_room", MODULE)
roomcore = importlib.util.module_from_spec(spec)
spec.loader.exec_module(roomcore)


def base_room():
    room = roomcore.create_room(display_name="Planning Room", created_by="steward", created_at="2026-07-12T00:00:00Z", speaking_policy={"max_responses_per_user_turn": 2})
    for rid, name, role in [("grace", "Grace", "planning"), ("helen", "Helen", "privacy"), ("alfred", "Alfred", "operations")]:
        room = roomcore.invite_participant(room, participant_id=rid, kind="resident", display_name=name, role=role, office=f"Office of {name}")
    return room


def test_room_creation_stable_identity_and_staged_uninstalled():
    a = roomcore.create_room(display_name="Planning Room", created_by="steward", created_at="2026-07-12T00:00:00Z")
    b = roomcore.create_room(display_name="Planning Room", created_by="steward", created_at="2026-07-12T00:00:00Z")
    assert a["room_id"] == b["room_id"]
    assert a["audit_metadata"]["staged"] is True
    assert a["audit_metadata"]["installed"] is False
    assert roomcore.room_snapshot(a)["staged_work_is_installed"] is False


def test_explicit_invitation_acceptance_and_no_implicit_participation():
    room = base_room()
    room = roomcore.accept_participant(room, "grace")
    room = roomcore.submit_user_turn(room, text="Everyone weigh in", submitted_by="steward", idempotency_key="1")
    plans = roomcore.plan_resident_turns(room, room["pending_questions"][0]["user_turn_id"])
    assert [p["resident_id"] for p in plans] == ["grace"]
    assert "helen" not in [p["resident_id"] for p in plans]


def test_deterministic_roundtable_order_and_bounded_response_count():
    room = base_room()
    for rid in ["grace", "helen", "alfred"]:
        room = roomcore.accept_participant(room, rid)
    room = roomcore.submit_user_turn(room, text="Everyone", submitted_by="steward", idempotency_key="2")
    plans = roomcore.plan_resident_turns(room, room["pending_questions"][0]["user_turn_id"])
    assert [p["display_name"] for p in plans] == ["Alfred", "Grace"]


def test_targeted_participant_selection_declined_and_unavailable_states():
    room = base_room()
    room = roomcore.accept_participant(room, "grace")
    room = roomcore.accept_participant(room, "helen")
    room = roomcore.decline_participant(room, "helen", "busy")
    room = roomcore.mark_unavailable(room, "alfred", "offline")
    room = roomcore.set_room_mode(room, "targeted", changed_by="steward")
    room = roomcore.submit_user_turn(room, text="Helen and Grace", submitted_by="steward", idempotency_key="3", target_resident_ids=["helen", "grace"])
    plans = roomcore.plan_resident_turns(room, room["pending_questions"][0]["user_turn_id"], target_resident_ids=["helen", "grace", "alfred"])
    assert [p["resident_id"] for p in plans] == ["grace"]


def test_visible_resident_attribution_and_idempotent_retry():
    room = base_room(); room = roomcore.accept_participant(room, "grace")
    room = roomcore.submit_user_turn(room, text="Grace answer", submitted_by="steward", idempotency_key="4", target_resident_ids=["grace"])
    room = roomcore.submit_user_turn(room, text="Grace answer", submitted_by="steward", idempotency_key="4", target_resident_ids=["grace"])
    assert len([t for t in room["turns"] if t["speaker_kind"] == "human"]) == 1
    plan = roomcore.plan_resident_turns(room, room["pending_questions"][0]["user_turn_id"], target_resident_ids=["grace"])[0]
    room = roomcore.record_resident_turn(room, plan, text="A distinct answer", model_metadata={"provider": "test"})
    room = roomcore.record_resident_turn(room, plan, text="duplicate")
    resident_turns = [t for t in room["turns"] if t["speaker_kind"] == "resident"]
    assert len(resident_turns) == 1
    assert resident_turns[0]["resident_id"] == "grace"
    assert resident_turns[0]["display_name"] == "Grace"
    assert resident_turns[0]["authority_disclaimer_metadata"]["no_authority_expansion"] is True


def test_separate_shared_and_resident_context_with_private_omission():
    room = base_room(); room = roomcore.accept_participant(room, "grace")
    room = roomcore.add_context(room, shared_context=[{"text": "public", "classification": "room_shared", "source_reference": "doc:1"}, {"text": "secret", "classification": "hr_private", "source_reference": "hr:1"}], resident_context_packets={"grace": [{"text": "private to Grace", "source_reference": "mem:g"}]})
    ctx = roomcore.filtered_context_for(room, "grace")
    assert [x["text"] for x in ctx["shared_context"]] == ["public"]
    assert ctx["resident_private_context"][0]["text"] == "private to Grace"
    assert any(e["event"] == "context_omitted" for e in room["audit_metadata"]["events"])


def test_pause_resume_archive_and_planning_blocked_when_not_active():
    room = base_room(); room = roomcore.accept_participant(room, "grace")
    token = room["session_reference"]["resume_token"]
    room = roomcore.pause_room(room)
    assert roomcore.plan_resident_turns(room, "x") == []
    room = roomcore.resume_room(room, token)
    assert room["status"] == "active"
    room = roomcore.archive_room(room)
    assert room["status"] == "archived"
    assert roomcore.office_projection(room, "steward")["safe_actions"] == []


def test_resident_to_resident_depth_limits_and_no_privileged_actions():
    room = base_room()
    for rid in ["grace", "helen"]:
        room = roomcore.accept_participant(room, rid)
    blocked = roomcore.plan_resident_to_resident_turns(room, source_user_turn_id="u1", from_resident_id="grace", to_resident_ids=["helen"], enabled=True, max_depth=1, current_depth=1, max_turn_count=1)
    allowed = roomcore.plan_resident_to_resident_turns(room, source_user_turn_id="u1", from_resident_id="grace", to_resident_ids=["helen"], enabled=True, max_depth=2, current_depth=1, max_turn_count=1)
    assert blocked == []
    assert [p["resident_id"] for p in allowed] == ["helen"]
    assert roomcore.execute_privileged_action(room, "hire")["executed"] is False


def test_office_openwebui_safe_projection():
    room = base_room()
    projection = roomcore.office_projection(room, "steward")
    assert projection["room_name"] == "Planning Room"
    assert projection["pending_invited_speakers"] == ["grace", "helen", "alfred"]
    assert "submit_user_turn" in projection["safe_actions"]
    assert projection["session_reference"]["resume_token"].startswith("resume_")
