import pytest
from estate.core.grace_momentum_service import *

def test_contract_fake_auth_idempotency_and_replay(tmp_path):
    service = FakeGraceMomentumService(tmp_path)
    created = service.command(reference_command("directive.create", idempotency_key="one"), TEST_IDENTITIES["grace"])
    assert service.command(reference_command("directive.create", idempotency_key="one"), TEST_IDENTITIES["grace"]) == created
    event = created["event"]
    assert event["schema_version"] == EVENT_SCHEMA_VERSION and event["actor"] == "test-grace"
    assert service.subscribe()["next_cursor"] == 1
    service.checkpoint(); assert service.recover()["recovered"] is True

def test_authority_and_disabled_mode_fail_closed(tmp_path):
    with pytest.raises(AuthorizationError): FakeGraceMomentumService(tmp_path).command(reference_command("directive.create"), TEST_IDENTITIES["observer"])
    with pytest.raises(AuthorizationError): GraceMomentumService(tmp_path, mode="disabled").command(reference_command("directive.create"), TEST_IDENTITIES["grace"])

def test_public_client_contract_actions_queries_and_unauthorized_shape(tmp_path):
    service = FakeGraceMomentumService(tmp_path); client = GraceMomentumClient(service, TEST_IDENTITIES["grace"])
    objective = client.send(reference_command("objective.create_or_correlate", idempotency_key="objective"))
    directive = client.send(reference_command("momentum.authorize", idempotency_key="directive"))
    assert objective["event"]["event_type"] == "objective.created_or_correlated"
    assert directive["event"]["event_type"] == "directive.authorized"
    assert client.query("objective.summary", objective_id="objective-demo")["query"] == "objective.summary"
    denied = GraceMomentumClient(service, TEST_IDENTITIES["observer"]).send(reference_command("momentum.authorize", idempotency_key="denied"))
    assert denied["error"]["code"] == "unauthorized"

@pytest.mark.parametrize("mode", ["fixture", "shadow", "bounded_live"])
def test_every_mode_suppresses_provider_effects(tmp_path, mode):
    service = GraceMomentumService(tmp_path, mode=mode)
    result = service.command(reference_command("cme.evaluate"), TEST_IDENTITIES["cme"])
    assert result["provider_effect_suppressed"] is True
    assert service.readiness()["provider_effects_enabled"] is False
