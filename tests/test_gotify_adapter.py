from estate.core.gotify_adapter import gotify_priority, recall_event_to_gotify_payload, send_gotify_recall


def recall_notification(**overrides):
    item = {
        "id": "notification-evt-1",
        "class": "recall",
        "eligible_for_immediate_delivery": True,
        "reason": "constitutional",
        "requested_by": "alfred",
        "priority": "urgent",
        "action": "prepare_recall_delivery",
    }
    item.update(overrides)
    return item


def configured_env():
    return {"ESTATE_GOTIFY_URL": "http://gotify.local", "ESTATE_GOTIFY_TOKEN": "super-secret-token"}


def test_dry_run_send_does_not_contact_gotify(tmp_path):
    calls = []

    def transport(config, payload):
        calls.append((config, payload))

    report = send_gotify_recall(recall_notification(), dry_run=True, env=configured_env(), transport=transport, root=tmp_path)

    assert report["ok"] is True
    assert report["status"] == "dry_run"
    assert calls == []
    assert (tmp_path / "runtime/notifications/gotify_delivery_report.json").exists()


def test_missing_configuration_warns_in_dry_run_and_fails_in_real_send(tmp_path):
    dry = send_gotify_recall(recall_notification(), dry_run=True, env={}, root=tmp_path, write_report=False)
    real = send_gotify_recall(recall_notification(), dry_run=False, env={}, root=tmp_path, write_report=False)

    assert dry["ok"] is True
    assert dry["status"] == "warning"
    assert real["ok"] is False
    assert real["status"] == "failed"
    assert real["reason"] == "missing_configuration"


def test_token_not_exposed_in_output(tmp_path):
    report = send_gotify_recall(recall_notification(), dry_run=True, env=configured_env(), root=tmp_path, write_report=False)

    assert "super-secret-token" not in str(report)
    assert report["configured_token"] is True


def test_retry_once_behavior_using_mocked_transport(tmp_path):
    calls = []

    def flaky_transport(config, payload):
        calls.append(payload)
        if len(calls) == 1:
            raise RuntimeError("temporary outage")
        return {"status_code": 200}

    report = send_gotify_recall(recall_notification(), dry_run=False, env=configured_env(), transport=flaky_transport, root=tmp_path)

    assert report["ok"] is True
    assert report["status"] == "sent"
    assert len(calls) == 2
    assert report["attempts"][0]["ok"] is False
    assert report["attempts"][1]["ok"] is True


def test_correct_mapping_from_router_recall_event_to_gotify_payload():
    payload = recall_event_to_gotify_payload(recall_notification(reason="security", requested_by="alfred", priority="high", action="pause_autonomy"))

    assert payload == {
        "title": "Estate Recall",
        "priority": 8,
        "message": "Recall Steward. reason=security; requested_by=alfred; action=pause_autonomy",
    }
    assert gotify_priority("normal") == 5
