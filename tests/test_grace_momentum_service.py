import threading
import pytest
import estate.core.grace_momentum_service as control
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

def test_bounded_replay_availability_and_lifecycle_projection(tmp_path):
    service = FakeGraceMomentumService(tmp_path); client = GraceMomentumClient(service, TEST_IDENTITIES["grace"])
    client.send(reference_command("objective.create_or_correlate", idempotency_key="one"))
    client.send(reference_command("momentum.authorize", idempotency_key="two"))
    replay = client.subscribe(0, limit=1)
    assert replay["next_cursor"] == 1 and replay["has_more"] is True
    assert client.availability()["event_consumption"]["api"] == "bounded_polling_replay"
    projection = client.lifecycle_projection("objective-demo")
    assert projection["directive"]["operational_owner"] == "Grace"
    assert projection["stages"]["provider_governance"]["provider_effects_enabled"] is False

def test_claim_mapping_and_config_fail_closed(tmp_path):
    service = FakeGraceMomentumService(tmp_path)
    assert service.configure(ProductionControlConfig(authentication_issuer="issuer", execution_mode="shadow"))["provider_effects_enabled"] is False
    assert identity_from_claims({"iss":"issuer", "sub":"a", "office":"Grace", "authority_source":"a", "active":True}, issuer="issuer").actor_id == "a"
    with pytest.raises(AuthenticationError): identity_from_claims({"iss":"wrong"}, issuer="issuer")

def _loopback(service):
    server = production_http_server(service, port=0, authentication_issuer="issuer")
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    return server, f"http://127.0.0.1:{server.server_port}"

def test_loopback_client_submission_replay_availability_and_projection(tmp_path):
    service = FakeGraceMomentumService(tmp_path); server, url = _loopback(service)
    try:
        claims = {"iss":"issuer", "sub":"grace", "office":"Grace", "authority_source":"test/grace", "active":True}
        client = LoopbackGraceMomentumClient(url, claims)
        assert client.send(reference_command("objective.create_or_correlate", idempotency_key="http-one"))["record"]["objective_id"] == "objective-demo"
        assert client.replay(0, limit=1)["next_cursor"] == 1
        assert client.availability()["operationally_available"] is True
        assert client.lifecycle_projection("objective-demo")["objective_id"] == "objective-demo"
    finally: server.shutdown(); server.server_close()

def test_loopback_client_fails_closed_for_transport_and_not_ready(tmp_path):
    with pytest.raises(TransportError): LoopbackGraceMomentumClient("http://127.0.0.1:9", {}).health()
    service = FakeGraceMomentumService(tmp_path, mode="disabled"); server, url = _loopback(service)
    try:
        client = LoopbackGraceMomentumClient(url, {"iss":"issuer", "sub":"grace", "office":"Grace", "authority_source":"test/grace", "active":True})
        assert client.availability()["operationally_available"] is False
    finally: server.shutdown(); server.server_close()

def test_loopback_client_rejects_timeout_malformed_and_non_2xx(monkeypatch):
    client = LoopbackGraceMomentumClient("http://127.0.0.1:8765", {})
    monkeypatch.setattr(control, "urlopen", lambda *args, **kwargs: (_ for _ in ()).throw(TimeoutError()))
    with pytest.raises(TransportError): client.health()
    class Reply:
        status = 200
        def read(self): return b"not-json"
        def __enter__(self): return self
        def __exit__(self, *args): return False
    monkeypatch.setattr(control, "urlopen", lambda *args, **kwargs: Reply())
    with pytest.raises(MalformedResponseError): client.health()
    class FailedReply(Reply): status = 503
    monkeypatch.setattr(control, "urlopen", lambda *args, **kwargs: FailedReply())
    with pytest.raises(TransportError): client.health()

def test_availability_interpretation_rejects_unhealthy_and_provider_enabled():
    assert interpret_availability({"health":{"healthy":False}, "readiness":{"ready":True,"provider_effects_enabled":False,"mode":"shadow"}}) is False
    assert interpret_availability({"health":{"healthy":True}, "readiness":{"ready":True,"provider_effects_enabled":True,"mode":"shadow"}}) is False

@pytest.mark.parametrize("mode", ["fixture", "shadow", "bounded_live"])
def test_every_mode_suppresses_provider_effects(tmp_path, mode):
    service = GraceMomentumService(tmp_path, mode=mode)
    result = service.command(reference_command("cme.evaluate"), TEST_IDENTITIES["cme"])
    assert result["provider_effect_suppressed"] is True
    assert service.readiness()["provider_effects_enabled"] is False
