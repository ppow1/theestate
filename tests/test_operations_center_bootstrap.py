from estate.core.operations_center_bootstrap import operations_center_start, operations_center_status, operations_center_stop


def test_operations_center_status_is_local_and_safe():
    payload = operations_center_status()
    assert payload["local_only"] is True
    assert payload["authority"]["executes_work_packages"] is False
    assert payload["authority"]["bypasses_steward_authorization"] is False
    assert payload["entry_point"] == "runtime/steward/command_center.html"


def test_operations_center_start_status_stop_lifecycle():
    stopped = operations_center_stop()
    assert stopped["local_only"] is True

    started = operations_center_start(port=8876)
    try:
        assert started["local_only"] is True
        assert started["started"] is True
        assert started["running"] is True
        assert started["host"] == "127.0.0.1"
        assert started["port"] == 8876
        assert started["settings_loaded"] is True
        assert any(item["name"] == "service_health_preflight" for item in started["preflight"])

        status = operations_center_status()
        assert status["running"] is True
        assert status["http_status"]["reachable"] is True
    finally:
        stopped = operations_center_stop()
        assert stopped["local_only"] is True
        assert stopped["running"] is False
