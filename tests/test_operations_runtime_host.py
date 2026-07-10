import json

import pytest

from estate.core.operations_runtime_host import TASK_NAME, OperationsRuntimeHost, OperationsRuntimeHostError
from estate.core.operations_runtime_service import OperationsRuntimeService


def test_host_foreground_writes_external_evidence_and_runs_existing_service(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    state = tmp_path / "outside" / "host"
    root.mkdir()
    calls = []

    def fake_run_once(self, **kwargs):
        calls.append(kwargs)
        self.runtime.ensure_dirs()
        return {"cycle_id": "cycle-1", "runtime_state": "running", "latest_audit_verdict": "pass"}

    monkeypatch.setattr(OperationsRuntimeService, "run_once", fake_run_once)
    result = OperationsRuntimeHost(root, state).run_foreground(max_cycles=1, interval_seconds=0, mode="observe-only")

    assert result["cycles_run"] == 1
    assert calls == [{"dry_run": False, "mode": "observe-only", "max_audit_requests": 1}]
    assert (state / "startup.json").exists()
    assert (state / "shutdown.json").exists()
    assert json.loads((state / "last_cycle.json").read_text())["cycle_id"] == "cycle-1"
    assert not (state / "host.lock.json").exists()
    assert not state.resolve().is_relative_to(root.resolve())


def test_host_rejects_duplicate_active_lock(tmp_path):
    host = OperationsRuntimeHost(tmp_path / "repo", tmp_path / "state")
    host.acquire_lock()
    try:
        with pytest.raises(OperationsRuntimeHostError):
            OperationsRuntimeHost(tmp_path / "repo", tmp_path / "state").acquire_lock()
    finally:
        host.release_lock()


def test_host_recovers_stale_lock(tmp_path):
    state = tmp_path / "state"
    state.mkdir()
    (state / "host.lock.json").write_text(json.dumps({"pid": 99999999, "acquired_at": "2000-01-01T00:00:00Z"}), encoding="utf-8")
    payload = OperationsRuntimeHost(tmp_path / "repo", state).acquire_lock()
    assert payload["pid"] != 99999999


def test_host_status_reports_truthful_health_fields(tmp_path):
    root = tmp_path / "repo"
    state = tmp_path / "state"
    root.mkdir()
    service = OperationsRuntimeService(root)
    service.runtime.ensure_dirs()
    service.runtime.write_status({"cycle_id": "c1", "runtime_state": "running", "latest_audit_verdict": "pass", "warnings": ["blocked"]})
    host = OperationsRuntimeHost(root, state)
    host.heartbeat("running", {"cycle_id": "c1"})

    status = host.status()

    assert status["heartbeat_age_seconds"] is not None
    assert status["cycle_state"] == "running"
    assert status["last_verdict"] == "pass"
    assert status["blocking_fault"] == "blocked"


def test_install_uninstall_write_manifest_without_infrastructure(tmp_path):
    host = OperationsRuntimeHost(tmp_path / "repo", tmp_path / "state")
    installed = host.install()
    assert installed["command"][-3:] == ["operations-runtime", "host", "start"]
    assert (tmp_path / "state" / "autostart.json").exists()
    assert host.uninstall()["removed_manifest"] is True


def test_windows_install_executes_and_verifies_scheduled_task(tmp_path, monkeypatch):
    import estate.core.operations_runtime_host as mod
    calls=[]
    class R:
        def __init__(self, rc=0, out="", err=""):
            self.returncode=rc; self.stdout=out; self.stderr=err
    def fake(cmd, cwd=None):
        calls.append(cmd)
        if cmd[:2] == ["schtasks","/Query"]:
            return R(0, "Status: Ready\n")
        return R(0, "ok", "")
    monkeypatch.setattr(mod.os, "name", "nt")
    monkeypatch.setattr(mod, "_run_command", fake)
    test_task_name = "Estate Operations Runtime Host Test Isolation"
    installed = OperationsRuntimeHost(tmp_path/"repo", tmp_path/"state", task_name=test_task_name).install()
    assert calls[0][:4] == ["schtasks","/Create","/SC","ONLOGON"]
    assert calls[0][5] == test_task_name
    assert calls[0][5] != TASK_NAME
    assert installed["scheduled_task_name"] == test_task_name
    assert installed["scheduled_task_verified"] is True
    assert installed["scheduled_task_exists"] is True


def test_windows_uninstall_deletes_and_verifies_removal(tmp_path, monkeypatch):
    import estate.core.operations_runtime_host as mod
    calls=[]
    class R:
        def __init__(self, rc=0):
            self.returncode=rc; self.stdout=""; self.stderr=""
    def fake(cmd, cwd=None):
        calls.append(cmd)
        if cmd[:2] == ["schtasks","/Query"]:
            return R(1)
        return R(0)
    monkeypatch.setattr(mod.os, "name", "nt")
    monkeypatch.setattr(mod, "_run_command", fake)
    test_task_name = "Estate Operations Runtime Host Test Isolation"
    host=OperationsRuntimeHost(tmp_path/"repo", tmp_path/"state", task_name=test_task_name)
    host.install_path.parent.mkdir(parents=True); host.install_path.write_text("{}")
    out=host.uninstall()
    assert calls[0][:3] == ["schtasks","/Delete","/TN"]
    assert calls[0][3] == test_task_name
    assert calls[0][3] != TASK_NAME
    assert out["scheduled_task"] == test_task_name
    assert out["scheduled_task_removed"] is True


def test_host_does_not_recover_live_old_heartbeat_lock(tmp_path, monkeypatch):
    import estate.core.operations_runtime_host as mod

    state = tmp_path / "state"
    state.mkdir()
    (state / "host.lock.json").write_text(json.dumps({"pid": 1234, "acquired_at": "2000-01-01T00:00:00Z", "heartbeat_at": "2000-01-01T00:00:00Z"}), encoding="utf-8")
    monkeypatch.setattr(mod, "_pid_liveness", lambda pid: "alive")

    with pytest.raises(OperationsRuntimeHostError):
        OperationsRuntimeHost(tmp_path / "repo", state).acquire_lock()

    assert json.loads((state / "host.lock.json").read_text(encoding="utf-8"))["pid"] == 1234


def test_host_does_not_recover_unknown_pid_liveness_lock(tmp_path, monkeypatch):
    import estate.core.operations_runtime_host as mod

    state = tmp_path / "state"
    state.mkdir()
    (state / "host.lock.json").write_text(json.dumps({"pid": 1234, "acquired_at": "2000-01-01T00:00:00Z"}), encoding="utf-8")
    monkeypatch.setattr(mod, "_pid_liveness", lambda pid: "unknown")

    with pytest.raises(OperationsRuntimeHostError):
        OperationsRuntimeHost(tmp_path / "repo", state).acquire_lock()

    assert json.loads((state / "host.lock.json").read_text(encoding="utf-8"))["pid"] == 1234


def test_host_recovers_only_dead_pid_lock(tmp_path, monkeypatch):
    import estate.core.operations_runtime_host as mod

    state = tmp_path / "state"
    state.mkdir()
    (state / "host.lock.json").write_text(json.dumps({"pid": 1234, "acquired_at": "2000-01-01T00:00:00Z"}), encoding="utf-8")
    monkeypatch.setattr(mod, "_pid_liveness", lambda pid: "dead")

    payload = OperationsRuntimeHost(tmp_path / "repo", state).acquire_lock()

    assert payload["pid"] != 1234
