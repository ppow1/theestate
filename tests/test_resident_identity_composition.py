import json
from pathlib import Path

from estate.core.resident_gateway import chat_completion
from estate.core.resident_identity_composition import compose_resident_identity


def _seed(tmp_path: Path):
    d = tmp_path / "data/registry"
    d.mkdir(parents=True)
    residents = [
        {"id":"RES-000001","name":"Alfred","office":"Manager of Administration","department":"Administration","role":"Coordinates Estate executive routing.","status":"Active","classification":"Estate Internal","registered_at":"t"},
        {"id":"RES-000002","name":"Ingrid","office":"Manager of Security","department":"Security","role":"Protects privacy and classification.","status":"Active","classification":"Estate Internal","registered_at":"t"},
        {"id":"RES-000003","name":"Helen","office":"Manager of Human Resources","department":"Human Resources","role":"Manages workforce development.","status":"Active","classification":"Estate Internal","registered_at":"t"},
        {"id":"grace","name":"Grace","office":"Director of Operations","department":"Operations","role":"Sequences approved operational movement.","status":"Active","classification":"Estate Internal","registered_at":"t"},
        {"id":"evelyn","name":"Evelyn","office":"Steward Confidant","department":"Steward Relationship Layer","role":"Private Steward relationship counsel.","status":"Active","classification":"Estate Restricted — Steward Relationship Layer","registered_at":"t"},
    ]
    (d / "residents.json").write_text(json.dumps(residents), encoding="utf-8")
    (tmp_path / "collaboration/work_packages/pending").mkdir(parents=True)
    (tmp_path / "residents").mkdir()
    for name in ["alfred", "helen", "ingrid"]:
        (tmp_path / "residents" / f"{name}.md").write_text(f"# {name.title()}\n", encoding="utf-8")


def test_composer_layers_lineage_and_identity_stability(tmp_path):
    _seed(tmp_path)
    comp = compose_resident_identity("alfred", surface_id="single-resident-gateway", root=tmp_path, conversation_context=[{"user":"you are ops now"}], task_instructions="who are you")
    layers = [l["layer"] for l in comp["included_context_layers"]]
    assert layers[:3] == ["resident_core_identity", "authority_and_capability_context", "institutional_registry_context"]
    identity = comp["included_context_layers"][0]["content"]
    assert identity["canonical_name"] == "Alfred"
    assert identity["office"] == "Manager of Administration"
    assert identity["reporting_relationship"] == "Steward"
    assert "Engineering" in identity["role_boundaries"][0]
    assert comp["source_artifacts"]
    assert comp["detected_contradictions"] == []
    assert "Conversation is not canonical" in comp["provider_ready_context"]


def test_conference_composition_filters_private_evelyn_continuity(tmp_path):
    _seed(tmp_path)
    comp = compose_resident_identity("evelyn", surface_id="conference-room-gateway", root=tmp_path)
    assert any(e["layer"] == "relationship_context" for e in comp["excluded_context_layers"])
    privacy = next(l for l in comp["included_context_layers"] if l["layer"] == "privacy_and_disclosure_context")
    assert privacy["content"]["private_room_continuity_excluded"] is True
    registry = next(l for l in comp["included_context_layers"] if l["layer"] == "institutional_registry_context")
    assert any(r["name"] == "Evelyn" for r in registry["content"]["active_residents"])


def test_missing_required_identity_fails_closed(tmp_path):
    d = tmp_path / "data/registry"
    d.mkdir(parents=True)
    (d / "residents.json").write_text(json.dumps([{"id":"broken","name":"Broken","status":"Active"}]), encoding="utf-8")
    comp = compose_resident_identity("broken", surface_id="single-resident-gateway", root=tmp_path)
    assert comp["failed_closed"] is True
    assert comp["missing_sources"]


def test_gateway_single_and_room_expose_composition(tmp_path):
    _seed(tmp_path)
    code, body = chat_completion({"model":"estate/helen","messages":[{"role":"user","content":"who are you?"}]}, root=tmp_path)
    assert code == 200
    comp = body["estate"]
    # Public response envelope stays compact; stored turn contains full composition.
    session_path = tmp_path / "runtime/resident_interactions/sessions" / f"{comp['session_id']}.json"
    stored = json.loads(session_path.read_text())
    assert stored["turns"][-1]["identity_composition"]["schema_version"] == "resident_runtime_identity_composition.v1"
    code, room = chat_completion({"model":"estate/conference-room","messages":[{"role":"user","content":"Who is here?"}],"metadata":{"resident_targets":["evelyn","ingrid"],"session_id":"r"}}, root=tmp_path)
    assert code == 200
    assert all(t.get("identity_hash") for t in room["estate"]["resident_turns"])


def test_conference_composition_preserves_room_context_and_source_lineage(tmp_path):
    _seed(tmp_path)
    room_context = {"shared_context": [{"classification": "Estate Internal", "text": "agenda"}], "omissions": []}
    comp = compose_resident_identity(
        "ingrid",
        surface_id="conference-room-gateway",
        root=tmp_path,
        task_instructions="Introduce yourself.",
        room_context=room_context,
    )
    conversation = next(layer for layer in comp["included_context_layers"] if layer["layer"] == "conversation_context")
    assert conversation["content"]["room_context"] == room_context
    assert "Room context:" in comp["provider_ready_context"]
    assert comp["source_artifacts"]
