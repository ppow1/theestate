import json

import pytest

from estate.core.operations_runtime_host import OperationsRuntimeHost, OperationsRuntimeHostError
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
