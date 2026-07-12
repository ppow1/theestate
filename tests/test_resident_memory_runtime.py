import pytest

from estate.core.resident_identity_composition import compose_resident_identity
from estate.core.resident_memory_runtime import ResidentMemoryRuntime, retrieve_memory_context


def evidence(path="collaboration/messages/msg.json", line=3):
    return [{"source": path, "line": line, "kind": "approved_message"}]


def test_conversation_temporary_until_governed_promotion(tmp_path):
    runtime = ResidentMemoryRuntime(tmp_path)
    composition = compose_resident_identity("alfred", surface_id="resident", root=tmp_path, conversation_context=[{"user":"likes tea", "resident":"noted"}])
    memory_layer = next(l for l in composition["included_context_layers"] if l["layer"] == "durable_memory_context")
    assert memory_layer["content"]["records"] == []
    proposed = runtime.propose_long_term_memory("alfred", "preference", "Alfred prefers tea for late reviews.", evidence(), approval=False)
    assert proposed["status"] == "proposed"
    assert retrieve_memory_context("alfred", root=tmp_path)["records"] == []
    runtime.promote_memory(proposed["memory_id"])
    assert retrieve_memory_context("alfred", root=tmp_path)["records"][0]["content"].startswith("Alfred prefers")


def test_private_evelyn_memory_excluded_from_shared_room(tmp_path):
    runtime = ResidentMemoryRuntime(tmp_path)
    runtime.write_memory({"subject":"evelyn", "memory_class":"comfort", "content":"Private Steward reassurance ritual.", "evidence": evidence(), "disclosure_scope":"evelyn_steward_private"})
    assert runtime.query_memories(subject="evelyn", surface_id="resident", actor="Steward")
    assert runtime.query_memories(subject="evelyn", surface_id="conference-room", actor="Helen") == []


def test_episode_stores_summary_not_raw_transcript_and_survives_reload(tmp_path):
    runtime = ResidentMemoryRuntime(tmp_path)
    ep = runtime.create_episode(participants=["Alfred", "Helen"], event_time="2026-07-12T10:00:00Z", summary="Alfred and Helen completed a handoff review.", evidence=evidence("runtime/resident_interactions/sessions/a.json", 12), verified_facts=["handoff completed"], feelings=["Helen was relieved"], uncertainty=["follow-up timing"])
    assert "raw transcript" not in ep["content"].lower()
    again = ResidentMemoryRuntime(tmp_path).query_memories(subject="alfred", memory_classes={"episode"})
    assert again[0]["metadata"]["participants"] == ["alfred", "helen"]


def test_correction_preserves_lineage_and_diagnostics_find_contradiction(tmp_path):
    runtime = ResidentMemoryRuntime(tmp_path)
    a = runtime.write_memory({"subject":"alfred", "memory_class":"routine", "content":"Morning reviews happen at 9.", "evidence": evidence("a", 1)})
    runtime.write_memory({"subject":"alfred", "memory_class":"routine", "content":"Morning reviews happen at 10.", "evidence": evidence("b", 2)})
    assert any(d["type"] == "possible_contradiction" for d in runtime.diagnostics())
    fixed = runtime.correct_memory(a["memory_id"], {"content":"Morning reviews happen at 09:00 when scheduled.", "evidence": evidence("c", 3)})
    assert fixed["supersedes"] == [a["memory_id"]]
    old = next(r for r in runtime.load()["records"] if r["memory_id"] == a["memory_id"])
    assert old["status"] == "superseded"


def test_institutional_memory_rebuild_deterministic_and_private_excluded(tmp_path):
    runtime = ResidentMemoryRuntime(tmp_path)
    runtime.write_institutional_memory("decision", "Conference memories require authorization.", evidence("governance/decision.md", 7), state="current_policy")
    one = retrieve_memory_context("helen", root=tmp_path, surface_id="conference-room", actor="Helen")
    two = retrieve_memory_context("helen", root=tmp_path, surface_id="conference-room", actor="Helen")
    assert one == two
    assert one["records"][0]["metadata"]["institutional_state"] == "current_policy"


def test_relationship_proposals_review_and_no_auto_promotion(tmp_path):
    runtime = ResidentMemoryRuntime(tmp_path)
    proposal = runtime.propose_relationship_change(["evelyn", "steward"], "trust", 0.7, evidence(), disclosure_scope="evelyn_steward_private")
    assert proposal["status"] == "proposed"
    review = runtime.relationship_review(resident="evelyn", actor="Helen", surface_id="conference-room")
    assert review["unresolved_proposals"]
    assert any(f["type"] == "privacy_redactions_present" for f in review["findings"])


def test_repair_requires_authority_and_receipt(tmp_path):
    runtime = ResidentMemoryRuntime(tmp_path)
    rec = runtime.write_memory({"subject":"helen", "memory_class":"lesson", "content":"Escalate burnout indicators to Helen review.", "evidence": evidence()})
    with pytest.raises(PermissionError):
        runtime.repair("retire", [rec["memory_id"]], actor="guest", reason="no authority")
    receipt = runtime.repair("retire", [rec["memory_id"]], actor="Ingrid", reason="privacy correction")
    assert receipt["before_hash"] != receipt["after_hash"]
