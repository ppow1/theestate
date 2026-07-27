from estate.core.grace_momentum_service import FakeGraceMomentumService, GraceMomentumClient, TEST_IDENTITIES
from estate.core.office_grace_momentum import GraceMomentumEstateUI, canonical_links


def ui(root, identity="grace"):
    return GraceMomentumEstateUI(GraceMomentumClient(FakeGraceMomentumService(root), TEST_IDENTITIES[identity]))


def test_component_contract_rendering_and_deep_links(tmp_path):
    surface = ui(tmp_path)
    surface.command("momentum.authorize", objective_id="objective / one", idempotency_key="authorize")
    snap = surface.snapshot(objective_id="objective / one", directive_id="gmd/one", cursor=0, conversation_id="chat/one")
    assert snap["contract"] == "estate.grace-momentum-client.v1"
    assert snap["links"]["objective_url"] == "/estate/objectives/objective%20%2F%20one"
    assert snap["links"]["conversation_url"].startswith("/open-webui/conversations/chat%2Fone?")
    assert snap["events"] and snap["recovery"]["arbitrary_rerun"] is False


def test_auth_role_authority_and_duplicate_action_suppression(tmp_path):
    denied = ui(tmp_path, "observer").command("momentum.authorize", objective_id="o", idempotency_key="deny")
    assert denied["error"]["code"] == "unauthorized"
    surface = ui(tmp_path)
    first = surface.command("momentum.authorize", objective_id="o", idempotency_key="same")
    second = surface.command("momentum.authorize", objective_id="o", idempotency_key="same")
    assert first == second


def test_event_update_audit_replay_and_blocker_contract_queries(tmp_path):
    surface = ui(tmp_path)
    surface.command("momentum.authorize", objective_id="o", idempotency_key="one")
    before = surface.snapshot(objective_id="o")
    surface.command("escalation.request", objective_id="o", idempotency_key="two")
    after = surface.snapshot(objective_id="o", cursor=before["cursor"])
    assert after["events"][-1]["event_type"] == "escalation.requested"
    assert "audit.trail" in after["queries"] and "replay.state" in after["queries"]
