import json

from estate.core.steward_presence import (
    PRESENCE_JSON,
    PRESENCE_MARKDOWN,
    apply_transition,
    generate_steward_presence_state,
    validate_transition,
)


def test_valid_and_invalid_transitions_are_auditable():
    state = {"current_state": "unknown", "transition_history": [], "warnings": []}
    state = apply_transition(state, "away", evidence="manual-test", reason="approved signal")
    assert state["current_state"] == "away"
    state = apply_transition(state, "recall_sent", evidence="manual-test", reason="bad jump")
    assert state["current_state"] == "away"
    assert state["transition_history"][-1]["ok"] is False
    assert state["warnings"][-1]["type"] == "invalid_transition"
    assert validate_transition("recall_sent", "present")["ok"] is False


def test_missing_evidence_produces_unknown_and_outputs(tmp_path):
    payload = generate_steward_presence_state(root=tmp_path)
    assert payload["current_state"] == "unknown"
    assert any(w["type"] == "unknown_state" for w in payload["warnings"])
    assert (tmp_path / PRESENCE_JSON).exists()
    assert (tmp_path / PRESENCE_MARKDOWN).exists()
    assert "Current state: unknown" in (tmp_path / PRESENCE_MARKDOWN).read_text(encoding="utf-8")


def test_recall_requested_from_notification_router(tmp_path):
    path = tmp_path / "runtime/notifications/notification_router_report.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"notifications": [{"id": "n1", "class": "recall", "created_at": "2026-07-03T00:00:00Z"}]}), encoding="utf-8")

    payload = generate_steward_presence_state(root=tmp_path, write=False)
    assert payload["current_state"] == "recall_requested"
    assert payload["transition_history"][-1]["to_state"] == "recall_requested"


def test_recall_sent_acknowledged_and_resumed_transition_helpers(tmp_path):
    audit = tmp_path / "runtime/audit/recall_audit_log.json"
    audit.parent.mkdir(parents=True)
    audit.write_text(json.dumps({"records": [{"record_id": "r1", "timestamp": "2026-07-03T00:01:00Z", "delivery_result": {"status": "delivered"}, "acknowledgement_state": "acknowledged", "acknowledgement_timestamp": "2026-07-03T00:02:00Z"}]}), encoding="utf-8")

    payload = generate_steward_presence_state(root=tmp_path, write=False)
    assert payload["current_state"] == "recall_acknowledged"
    assert [e["to_state"] for e in payload["transition_history"]] == ["recall_requested", "recall_sent", "recall_acknowledged"]

    resumed = apply_transition(payload, "resumed", evidence="operations/steward/steward_presence_state.md", reason="operation resumed after acknowledgement")
    assert resumed["current_state"] == "resumed"
