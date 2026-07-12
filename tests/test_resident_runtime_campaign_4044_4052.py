import json
from pathlib import Path

from estate.core.character_bible import load_character_context
from estate.core.conference_room_context import assemble_conference_room_context
from estate.core.conversation_isolation import append_turn, load_history, reset_session, session_identity
from estate.core.grounded_fact_provider import get_grounded_facts
from estate.core.relationship_graph import load_relationship_context
from estate.core.resident_identity_composition import compose_resident_identity
from estate.core.resident_mail_bus import send_message, list_mailbox, acknowledge_bus_message
from estate.core.resident_registry_snapshot import build_resident_registry_snapshot


def _seed(root: Path):
    (root/"data/registry").mkdir(parents=True)
    (root/"collaboration/messages").mkdir(parents=True)
    (root/"collaboration/work_packages/pending").mkdir(parents=True)
    (root/"residents").mkdir()
    residents=[]
    for i,name in enumerate(["Alfred","Helen","Grace","Ingrid","Evelyn"],1):
        residents.append({"id": name.lower() if name in {"Grace","Evelyn"} else f"RES-00000{i}", "name": name, "office": "Steward Confidant" if name=="Evelyn" else ("Director of Operations" if name=="Grace" else f"{name} Office"), "department": "Test", "role": f"{name} role", "status": "Active", "classification": "Estate Restricted — Steward Relationship Layer" if name=="Evelyn" else "Estate Internal"})
        (root/"residents"/f"{name.lower()}.md").write_text(f"# {name}\nDistinct {name} profile.\n", encoding="utf-8")
    (root/"data/registry/residents.json").write_text(json.dumps(residents), encoding="utf-8")
    personnel=[]
    for idx,name in enumerate(["Alfred","Helen","Grace","Ingrid","Evelyn"],1):
        personnel.append({"employee_id": f"EMP-{idx}", "display_name": name, "resident_id": name.lower(), "mailbox_id": idx, "current_title": f"{name} title", "current_office": f"{name} office"})
    (root/"data/registry/personnel.json").write_text(json.dumps(personnel), encoding="utf-8")
    (root/"data/registry/functional_mailboxes.json").write_text("[]", encoding="utf-8")


def test_character_registry_facts_and_identity_composition(tmp_path):
    _seed(tmp_path)
    snap = build_resident_registry_snapshot(tmp_path)
    assert snap["record_counts"]["active_residents"] == 5
    assert "Evelyn" in [r["name"] for r in snap["active_residents"]]
    character = load_character_context("Grace", root=tmp_path)
    assert character["stable_traits"]["temperament"].startswith("energetic")
    facts = get_grounded_facts("Helen", root=tmp_path)
    assert any(f["key"] == "registry.active_residents" for f in facts["facts"])
    composed = compose_resident_identity("Evelyn", surface_id="conference-room", root=tmp_path)
    rel = next(l for l in composed["included_context_layers"] if l["layer"] == "relationship_context")
    assert rel["content"]["redactions"]
    assert "protected intimate" not in composed["provider_ready_context"]


def test_conversation_isolation_room_context_and_relationships(tmp_path):
    _seed(tmp_path)
    a = session_identity("Alfred", session_id="same-model", surface_id="resident-chat")
    h = session_identity("Helen", session_id="same-model", surface_id="resident-chat")
    append_turn(a, "user", "Alfred private", root=tmp_path)
    append_turn(h, "user", "Helen private", root=tmp_path)
    assert load_history(a, root=tmp_path)["turns"][0]["content"] == "Alfred private"
    assert load_history(h, root=tmp_path)["turns"][0]["content"] == "Helen private"
    reset_session(a, root=tmp_path)
    assert load_history(a, root=tmp_path)["turns"] == []
    room = assemble_conference_room_context(["Alfred", "Helen", "Evelyn"], root=tmp_path, room_history=[{"speaker":"Alfred","text":"shared"}])
    assert room["private_history_imported"] is False
    assert room["participants"][0]["name"] == "Alfred"
    assert load_relationship_context("Evelyn", surface_id="conference-room", root=tmp_path)["redactions"]


def test_message_runtime_mailbox_routing_and_acknowledgment(tmp_path):
    _seed(tmp_path)
    sent = send_message("Helen", "Grace", "Check", "Operational note", root=tmp_path)
    assert sent["delivered"] is True
    assert Path(tmp_path, sent["path"]).exists()
    duplicate = send_message("Helen", "Grace", "Check", "Operational note", root=tmp_path)
    assert duplicate["duplicate"] is True
    inbox = list_mailbox("Grace", root=tmp_path)
    assert inbox["message_count"] == 1
    assert list_mailbox("Ingrid", root=tmp_path)["message_count"] == 0
    ack = acknowledge_bus_message(inbox["messages"][0]["message_id"], actor="Grace", root=tmp_path)
    assert "acknowledgement_path" in ack
    after = list_mailbox("Grace", root=tmp_path)
    assert after["messages"][0]["ack_status"] in {"pending", "acknowledged"}
