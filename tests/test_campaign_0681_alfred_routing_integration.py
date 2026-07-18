import json

import pytest

from estate.core.alfred_runtime import (
    OPERATIONAL_MESSAGE_TYPES,
    correlate_operational_response,
    evaluate_operational_route,
    route_operational_message,
)


def write_registries(root):
    registry = root / "data" / "registry"
    registry.mkdir(parents=True)
    (registry / "personnel.json").write_text(
        json.dumps(
            [
                {"employee_id": 1, "mailbox_id": 1, "display_name": "Steward", "current_title": "Steward", "current_office": "Stewardship"},
                {"employee_id": 6, "mailbox_id": 6, "display_name": "Helen", "current_title": "Manager of Human Resources", "current_office": "Human Resources"},
                {"employee_id": 7, "mailbox_id": 7, "display_name": "Alfred", "current_title": "Manager of Administration", "current_office": "Administration"},
                {"employee_id": 9, "mailbox_id": 9, "display_name": "Chief Architect #6", "current_title": "Chief Architect #6", "current_office": "Office of the Chief Architect"},
                {"employee_id": 12, "mailbox_id": 12, "display_name": "Grace", "current_title": "Director of Operations", "current_office": "Office of Operations"},
            ]
        ),
        encoding="utf-8",
    )
    (registry / "mailboxes.json").write_text(
        json.dumps(
            [
                {"mailbox_id": 10001, "mailbox_type": "office", "display_name": "Office of the Chief Architect", "owning_office": "Office of the Chief Architect", "responsible_employee_id": 9},
                {"mailbox_id": 10004, "mailbox_type": "office", "display_name": "Human Resources Office", "owning_office": "Human Resources", "responsible_employee_id": 6},
                {"mailbox_id": 10100, "mailbox_type": "queue", "display_name": "Alfred Routing Intake", "owning_office": "Chief of Staff", "responsible_employee_id": None},
            ]
        ),
        encoding="utf-8",
    )


def message(message_type="coordination_request", **overrides):
    value = {
        "id": f"msg_{message_type}",
        "version": 1,
        "created_at": "2026-07-18T14:00:00+00:00",
        "created_by": "Grace",
        "source": "Grace",
        "source_employee_id": 12,
        "destination": "Office of the Chief Architect",
        "destination_employee_id": 9,
        "destination_mailbox_id": 9,
        "classification": "Estate Internal",
        "message_type": message_type,
        "priority": "normal",
        "status": "open",
        "requires_ack": True,
        "ack_status": "pending",
        "thread_id": f"thread_{message_type}",
        "related_work_package": "WP-0696",
        "payload": {
            "title": f"{message_type} example",
            "summary": "Route through the canonical office lane.",
            "instructions": "Routing grants no execution or decision authority.",
            "artifact_refs": ["evidence/WP-0696.json"],
        },
        "operational_context": {"authorizes_action": False},
    }
    value.update(overrides)
    return value


@pytest.mark.parametrize("message_type", sorted(OPERATIONAL_MESSAGE_TYPES))
def test_supported_operational_message_types_route_through_existing_mailbox(tmp_path, message_type):
    write_registries(tmp_path)
    result = route_operational_message(
        message(message_type), root=tmp_path, now="2026-07-18T14:10:00+00:00"
    )
    assert result["recorded"] is True
    assert result["indexed_destination_employee_id"] == 9
    assert result["indexed_destination_mailbox_id"] == 9
    assert result["routing_is_execution"] is False
    assert result["underlying_work_complete"] is False
    assert result["acceptance_granted"] is False
    assert (tmp_path / result["repository_message_path"]).exists()
    assert (tmp_path / result["mailbox_index_path"]).exists()


def test_route_fails_closed_on_stale_misrouted_or_guessed_destination(tmp_path):
    write_registries(tmp_path)
    stale = evaluate_operational_route(
        message(), root=tmp_path, now="2026-07-20T14:00:01+00:00"
    )
    assert stale["routable"] is False
    assert any("stale" in reason for reason in stale["reasons"])

    misrouted = evaluate_operational_route(
        message(destination_mailbox_id=6), root=tmp_path, now="2026-07-18T14:10:00+00:00"
    )
    assert misrouted["routable"] is False
    assert any("misrouted" in reason or "conflicts" in reason for reason in misrouted["reasons"])

    guessed = message()
    guessed.pop("destination_employee_id")
    guessed.pop("destination_mailbox_id")
    decision = evaluate_operational_route(
        guessed, root=tmp_path, now="2026-07-18T14:10:00+00:00"
    )
    assert decision["routable"] is False
    assert any("may not guess" in reason for reason in decision["reasons"])


def test_duplicate_is_idempotent_but_conflicting_duplicate_is_refused(tmp_path):
    write_registries(tmp_path)
    original = message()
    first = route_operational_message(original, root=tmp_path, now="2026-07-18T14:10:00+00:00")
    second = route_operational_message(original, root=tmp_path, now="2026-07-18T14:10:00+00:00")
    assert first["duplicate"] is False
    assert second["duplicate"] is True

    conflict = message(priority="high")
    decision = evaluate_operational_route(conflict, root=tmp_path, now="2026-07-18T14:10:00+00:00")
    assert decision["routable"] is False
    assert decision["conflicting_duplicate"] is True
    with pytest.raises(ValueError, match="not routable"):
        route_operational_message(conflict, root=tmp_path, now="2026-07-18T14:10:00+00:00")


def test_acknowledgement_and_reply_correlation_do_not_complete_work():
    original = message(thread_id="thread-0696")
    acknowledgement = {
        "id": "msg_ack_0696",
        "message_type": "acknowledgement",
        "acknowledges": original["id"],
        "thread_id": "thread-0696",
    }
    result = correlate_operational_response(original, acknowledgement)
    assert result["correlated"] is True
    assert result["acknowledged"] is True
    assert result["underlying_work_complete"] is False
    assert result["decision_authority_exercised"] is False
    assert result["acceptance_granted"] is False

    unrelated = correlate_operational_response(original, {"id": "msg-other", "thread_id": "different"})
    assert unrelated["correlated"] is False


def test_routing_refuses_message_that_claims_action_authority(tmp_path):
    write_registries(tmp_path)
    value = message(operational_context={"authorizes_action": True})
    decision = evaluate_operational_route(value, root=tmp_path, now="2026-07-18T14:10:00+00:00")
    assert decision["routable"] is False
    assert any("authorize no action" in reason for reason in decision["reasons"])
