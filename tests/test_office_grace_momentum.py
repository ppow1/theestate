import copy
import threading
import pytest

from estate.core.grace_momentum_service import (
    FakeGraceMomentumService, GraceMomentumClient, TEST_IDENTITIES,
    production_http_server,
)
from estate.core.office_grace_momentum import (
    GraceMomentumEstateUI, build_grace_momentum_surface, canonical_links,
    loopback_surface,
)


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
    assert snap["available"] is True and snap["provider_effects_enabled"] is False
    assert set(snap["projection"]) >= {"objective", "directive", "current_responsible_office", "current_blocker", "next_lawful_action", "replay_cursor", "stages"}
    assert set(snap["projection"]["stages"]) >= {"capability", "commission", "cme_evaluation", "provider_governance", "execution_authorization", "dispatch", "reconciliation", "validation", "grace_receipt", "completion"}


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
    assert after["events"][-1]["event_type"] == "escalation.requested"
    assert after["replay"]["next_cursor"] >= before["cursor"]


def test_loopback_client_consumes_canonical_projection_and_reconnects(tmp_path):
    service = FakeGraceMomentumService(tmp_path)
    server = production_http_server(service, port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        endpoint = f"http://127.0.0.1:{server.server_address[1]}"
        surface = loopback_surface(endpoint=endpoint, claims={"iss": "estate-control", "sub": "ui", "office": "Grace", "authority_source": "test", "active": True})
        surface.command("momentum.authorize", objective_id="o", idempotency_key="one")
        snapshot = surface.snapshot(objective_id="o")
        assert snapshot["transport"] == "loopback"
        assert snapshot["projection"]["replay_cursor"] == snapshot["cursor"]
        assert len(snapshot["events"]) == len({event["event_id"] for event in snapshot["events"]})
    finally:
        server.shutdown()
        server.server_close()


def test_unavailable_loopback_fails_closed_and_no_inprocess_default(tmp_path):
    unavailable = build_grace_momentum_surface(str(tmp_path))
    assert unavailable["available"] is False
    assert unavailable["provider_effects_enabled"] is False
    assert all(control["availability"] == "unavailable" for control in unavailable["controls"])
    assert "FakeGraceMomentumService" not in build_grace_momentum_surface.__code__.co_consts


class _ProviderStub:
    def __init__(self, availability, projection):
        self._availability = availability
        self._projection = projection
        self.sent = 0

    def availability(self): return self._availability
    def lifecycle_projection(self, objective_id): return self._projection
    def replay(self, cursor=0, *, limit=100): return {"events": [], "next_cursor": cursor}
    def subscribe(self, cursor=0, *, limit=100): return {"events": [], "next_cursor": cursor}
    def send(self, command): self.sent += 1; return {"disposition": "accepted"}


def _valid_provider_payload(tmp_path):
    service = FakeGraceMomentumService(tmp_path)
    return service.availability(), service.lifecycle_projection("o")


@pytest.mark.parametrize("mutate", [
    lambda value: value.pop("health"),
    lambda value: value.pop("readiness"),
    lambda value: value["health"].pop("healthy"),
    lambda value: value["readiness"].pop("ready"),
    lambda value: value["health"].update(healthy="true"),
    lambda value: value["readiness"].update(ready=1),
    lambda value: value["health"].update(healthy=None),
    lambda value: value["readiness"].update(ready=None),
    lambda value: value.clear() or value.update(available=True),
    lambda value: value["readiness"].update(ready=False),
])
def test_malformed_availability_fails_closed(tmp_path, mutate):
    availability, projection = _valid_provider_payload(tmp_path)
    malformed = copy.deepcopy(availability)
    mutate(malformed)
    client = _ProviderStub(malformed, projection)
    snapshot = GraceMomentumEstateUI(client).snapshot(objective_id="o")
    assert snapshot["available"] is False
    assert all(control["availability"] != "provider_authorized" for control in snapshot["controls"])
    assert GraceMomentumEstateUI(client).command("momentum.authorize", objective_id="o")["disposition"] == "blocked"
    assert client.sent == 0


def test_exact_boolean_availability_allows_projection(tmp_path):
    availability, projection = _valid_provider_payload(tmp_path)
    client = _ProviderStub(availability, projection)
    snapshot = GraceMomentumEstateUI(client).snapshot(objective_id="o")
    assert snapshot["available"] is True
    assert all(control["availability"] == "provider_authorized" for control in snapshot["controls"])


@pytest.mark.parametrize("mutate", [
    lambda value: value.pop("objective_id"),
    lambda value: value.pop("timeline"),
    lambda value: value.update(replay_cursor="0"),
    lambda value: value["stages"].update(execution_authorization="authorized"),
    lambda value: value.update(current_responsible_office=1),
    lambda value: value.update(current_blocker="blocked"),
    lambda value: value.update(next_lawful_action=1),
    lambda value: value.clear(),
])
def test_malformed_projection_fails_closed_and_cannot_mutate(tmp_path, mutate):
    availability, projection = _valid_provider_payload(tmp_path)
    malformed = copy.deepcopy(projection)
    mutate(malformed)
    client = _ProviderStub(availability, malformed)
    surface = GraceMomentumEstateUI(client)
    snapshot = surface.snapshot(objective_id="o")
    assert snapshot["available"] is False
    assert all(control["availability"] == "unavailable" for control in snapshot["controls"])
    assert snapshot["projection"]["objective"] is None
    assert surface.command("momentum.authorize", objective_id="o")["disposition"] == "blocked"
    assert client.sent == 0
