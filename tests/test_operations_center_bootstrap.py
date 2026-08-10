import json

from estate.core import operations_center_bootstrap as bootstrap
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


def write_pid(root, pid=4321, **extra):
    path = root / "runtime/steward/operations_center_server.pid"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"pid": pid, "host": "127.0.0.1", "port": 8876, **extra}), encoding="utf-8")


def test_operations_center_stop_windows_graceful_shutdown(monkeypatch, tmp_path):
    write_pid(tmp_path, windows_creation_token=17)
    alive = iter([True, True, False, False])
    killed = []
    monkeypatch.setattr(bootstrap.os, "name", "nt")
    monkeypatch.setattr(bootstrap, "_process_alive", lambda pid: next(alive))
    monkeypatch.setattr(bootstrap.os, "kill", lambda pid, sig: killed.append((pid, sig)))
    monkeypatch.setattr(bootstrap, "_windows_process_matches_server", lambda pid, info: (_ for _ in ()).throw(AssertionError("force fallback should not run")))

    result = operations_center_stop(root=tmp_path)

    assert result["stopped"] is True
    assert result["running"] is False
    assert killed == [(4321, bootstrap.signal.SIGTERM)]
    assert not (tmp_path / "runtime/steward/operations_center_server.pid").exists()


def test_operations_center_stop_cleans_already_dead_stale_pid(monkeypatch, tmp_path):
    write_pid(tmp_path, pid=4322)
    monkeypatch.setattr(bootstrap, "_process_alive", lambda pid: False)

    result = operations_center_stop(root=tmp_path)

    assert result["stopped"] is False
    assert result["running"] is False
    assert not (tmp_path / "runtime/steward/operations_center_server.pid").exists()


def test_operations_center_stop_windows_uses_bounded_force_fallback(monkeypatch, tmp_path):
    write_pid(tmp_path, pid=4323, windows_creation_token=18)
    waits = iter([False, True])
    killed = []
    forced = []
    monkeypatch.setattr(bootstrap.os, "name", "nt")
    monkeypatch.setattr(bootstrap, "_process_alive", lambda pid: True)
    monkeypatch.setattr(bootstrap.os, "kill", lambda pid, sig: killed.append((pid, sig)))
    monkeypatch.setattr(bootstrap, "_wait_for_process_exit", lambda pid: next(waits))
    monkeypatch.setattr(bootstrap, "_windows_process_matches_server", lambda pid, info: True)
    monkeypatch.setattr(bootstrap, "_windows_force_terminate", lambda pid: forced.append(pid) or True)

    result = operations_center_stop(root=tmp_path)

    assert killed == [(4323, bootstrap.signal.SIGTERM)]
    assert forced == [4323]
    assert result["stopped"] is True
    assert not (tmp_path / "runtime/steward/operations_center_server.pid").exists()


def test_operations_center_stop_windows_refuses_unowned_pid_fallback(monkeypatch, tmp_path):
    write_pid(tmp_path, pid=4324, windows_creation_token=19)
    monkeypatch.setattr(bootstrap.os, "name", "nt")
    monkeypatch.setattr(bootstrap, "_process_alive", lambda pid: True)
    monkeypatch.setattr(bootstrap.os, "kill", lambda pid, sig: None)
    monkeypatch.setattr(bootstrap, "_wait_for_process_exit", lambda pid: False)
    monkeypatch.setattr(bootstrap, "_windows_process_matches_server", lambda pid, info: False)
    monkeypatch.setattr(bootstrap, "_windows_force_terminate", lambda pid: (_ for _ in ()).throw(AssertionError("unowned process must not be terminated")))

    result = operations_center_stop(root=tmp_path)

    assert result["stopped"] is False
    assert result["running"] is True
    assert (tmp_path / "runtime/steward/operations_center_server.pid").exists()
