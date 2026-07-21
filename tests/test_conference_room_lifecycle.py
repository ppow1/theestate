import json
from pathlib import Path

import pytest
from estate.core.conference_room_lifecycle import (depart, invite, load_or_create_session, set_backup, transfer, update_default_moderator)
from estate.core.resident_gateway import chat_completion

ROOT=Path(__file__).resolve().parents[1]

def fixture_root(tmp_path):
    (tmp_path/"config").mkdir(); (tmp_path/"data/registry").mkdir(parents=True)
    (tmp_path/"config/conference_room_config.json").write_text((ROOT/"config/conference_room_config.json").read_text())
    (tmp_path/"data/registry/residents.json").write_text((ROOT/"data/registry/residents.json").read_text())
    return tmp_path

def test_new_room_is_steward_and_configured_moderator_only(tmp_path):
    root=fixture_root(tmp_path); state,created=load_or_create_session("chat-a",root)
    assert created and state["active_participants"]==["steward","alfred"]
    assert state["current_moderator"]==state["default_moderator_at_creation"]=="alfred"

def test_lifecycle_transfer_departure_and_backup_succession(tmp_path):
    root=fixture_root(tmp_path); state,_=load_or_create_session("chat-b",root)
    assert invite(state,["Helen","Grace"],root)==["helen","grace"]
    assert [e["initiating_authority"] for e in state["participant_history"] if e["event"]=="acknowledged"]==["helen","grace"]
    transfer(state,"Helen",root); set_backup(state,"Grace",root); result=depart(state,"Helen",root=root)
    assert result["successor"]=="grace" and state["current_moderator"]=="grace"
    assert "helen" not in state["active_participants"]

def test_no_backup_pauses_and_unknown_fails_closed(tmp_path):
    root=fixture_root(tmp_path); state,_=load_or_create_session("chat-c",root)
    depart(state,"Alfred",root=root)
    assert state["current_moderator"] is None and state["status"]=="paused_for_moderator"
    assert invite(state,["Nobody"],root)==[]
    assert state["audit_events"][-1]["reason"]=="unknown_or_inactive_resident"

def test_default_change_affects_new_not_existing_room_and_keeps_backup(tmp_path):
    root=fixture_root(tmp_path); old,_=load_or_create_session("old",root)
    result=update_default_moderator("Marie",root)
    new,_=load_or_create_session("new",root)
    assert result["former"]["name"]=="Alfred" and Path(result["backup_path"]).exists()
    assert old["current_moderator"]=="alfred" and new["current_moderator"]=="marie"

def test_gateway_persists_roster_and_routes_only_active_named_resident(monkeypatch,tmp_path):
    root=fixture_root(tmp_path)
    first={"model":"estate/conference-room","messages":[{"role":"user","content":"Who is here?"}],"metadata":{"session_id":"gw"}}
    code,body=chat_completion(first,root=root); assert code==200
    assert body["estate"]["conference_state"]["active_participants"]==["steward","alfred"]
    invite_payload={"model":"estate/conference-room","messages":[{"role":"user","content":"Invite Grace and Helen."}],"metadata":{"session_id":"gw"}}
    code,body=chat_completion(invite_payload,root=root); assert code==200
    assert {t["resident_id"] for t in body["estate"]["resident_turns"]}=={"grace","helen"}
    assert body["estate"]["conference_state"]["active_participants"]==["steward","alfred","grace","helen"]
