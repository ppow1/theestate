import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from estate.core.steward_command_center import generate_command_center, render_command_center_html
from estate.core.office_command_surface import controls_for_tab, execute_office_action
from estate.core.execution_session_controller import ExecutionSessionController
from estate.core.execution_attempt_runtime import ExecutionAttemptRuntime
from estate.core.execution_result_reconciliation_runtime import inspect_reconciliation
from estate.core.execution_provider_adapter_runtime import write_adapter_result

import importlib.util

def _load_test_helper(name):
    path = Path(__file__).resolve().parent / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module

_session_helpers = _load_test_helper("test_execution_session_controller")
_reconciliation_helpers = _load_test_helper("test_execution_result_reconciliation_runtime")
prepared_root = _session_helpers.prepared_root
auth = _session_helpers.auth
gate = _session_helpers.gate
rec_dispatch_payload = _reconciliation_helpers.dispatch_payload
rec_result = _reconciliation_helpers.result
from estate.core.execution_dispatch import enqueue_dispatch_request, inspect_dispatch_item


def test_execution_workspace_tab_payload_and_html(tmp_path):
    payload = generate_command_center(tmp_path)
    assert any(t["id"] == "execution-control" for t in payload["tabs"])
    assert "execution-control" in payload["office_actions"]
    html = render_command_center_html(payload)
    assert "Execution Control" in html
    assert "Preview execution session" in html
    assert "data-action-input='dispatch_id'" in html


def test_required_controls_registered():
    ids = {c["action_id"] for c in controls_for_tab("execution-control")}
    assert {
        "execution_session.preview", "execution_session.start", "execution_session.resume", "execution_session.status", "execution_session.report",
        "execution_attempt.cancel_request", "execution_attempt.inspect_recovery", "execution_attempt.retry_eligibility", "execution_attempt.release_stale",
        "execution_result.inspect_reconciliation", "execution_result.reconcile", "execution_result.report",
    } <= ids


def test_preview_real_controller_writes_evidence_and_no_provider_call(tmp_path, monkeypatch):
    prepared = prepared_root(tmp_path)
    a = auth(tmp_path, prepared)
    calls = []
    monkeypatch.setattr("estate.core.office_command_surface.ExecutionSessionController", lambda root: ExecutionSessionController(root=root, gate=gate(root, calls)))
    out = execute_office_action("execution_session.preview", root=tmp_path, dispatch_id="dispatch-wp-0506", authorization_path=str(a))
    assert out["outcome"] == "completed"
    assert out["authority_gating_status"] == "governed_preview_no_provider_call"
    assert (tmp_path / "runtime/execution_adapters/status/sessions_summary.json").is_file()
    summary = json.loads((tmp_path / "runtime/execution_adapters/status/sessions_summary.json").read_text())
    assert summary["sessions"][-1]["live_provider_called"] is False
    assert calls == []


def test_start_blocks_without_confirmation_and_authorization(tmp_path):
    prepared_root(tmp_path)
    out = execute_office_action("execution_session.start", root=tmp_path, dispatch_id="dispatch-wp-0506", authorization_path="missing.json")
    assert out["outcome"] == "blocked"
    assert "confirmation" in out["steward_message"]
    out2 = execute_office_action("execution_session.start", root=tmp_path, dispatch_id="dispatch-wp-0506", confirm_live_execution="true")
    assert out2["outcome"] == "blocked"


def test_fake_runner_start_exactly_once_and_status_report_resume(tmp_path, monkeypatch):
    prepared = prepared_root(tmp_path)
    a = auth(tmp_path, prepared)
    calls = []
    monkeypatch.setattr("estate.core.office_command_surface.ExecutionSessionController", lambda root: ExecutionSessionController(root=root, gate=gate(root, calls)))
    out = execute_office_action("execution_session.start", root=tmp_path, dispatch_id="dispatch-wp-0506", authorization_path=str(a), confirm_live_execution="true")
    assert out["outcome"] == "completed"
    assert len(calls) == 1
    sid = json.loads((tmp_path / "runtime/execution_adapters/status/sessions_summary.json").read_text())["sessions"][-1]["execution_session_id"]
    assert execute_office_action("execution_session.status", root=tmp_path, session_id=sid)["outcome"] == "completed"
    assert execute_office_action("execution_session.report", root=tmp_path, session_id=sid)["outcome"] == "completed"
    assert execute_office_action("execution_session.resume", root=tmp_path, session_id=sid)["outcome"] == "completed"
    assert len(calls) == 1


def test_attempt_controls_cancellation_recovery_retry_stale_release(tmp_path):
    rt = ExecutionAttemptRuntime(root=tmp_path, stale_after_seconds=0)
    acquired = rt.acquire_lease(dispatch_id="dispatch-a", adapter_request_id="adapter-a", provider_id="provider-a", provider_type="fake", lease_ttl_seconds=1)
    aid = acquired["attempt"]["execution_attempt_id"]
    cancel = execute_office_action("execution_attempt.cancel_request", root=tmp_path, dispatch_id="dispatch-a", attempt_id=aid, actor="Steward", reason="test")
    assert cancel["outcome"] == "completed"
    assert (tmp_path / f"runtime/execution_adapters/cancellations/{aid}.json").is_file()
    recovery = execute_office_action("execution_attempt.inspect_recovery", root=tmp_path, dispatch_id="dispatch-a")
    assert recovery["outcome"] == "completed"
    retry = execute_office_action("execution_attempt.retry_eligibility", root=tmp_path, dispatch_id="dispatch-a")
    assert retry["outcome"] == "completed"
    assert rt.status("dispatch-a")["attempts"][-1]["state"] != "stale"
    blocked = execute_office_action("execution_attempt.release_stale", root=tmp_path, dispatch_id="dispatch-a", attempt_id=aid, reason="test")
    assert blocked["outcome"] == "blocked"
    released = execute_office_action("execution_attempt.release_stale", root=tmp_path, dispatch_id="dispatch-a", attempt_id=aid, reason="test", confirm_stale_release="true")
    assert released["outcome"] in {"completed", "blocked"}


def test_non_stale_release_blocked(tmp_path):
    rt = ExecutionAttemptRuntime(root=tmp_path, stale_after_seconds=999999)
    aid = rt.acquire_lease(dispatch_id="dispatch-b", adapter_request_id="adapter-b", provider_id="provider-b", provider_type="fake")["attempt"]["execution_attempt_id"]
    out = execute_office_action("execution_attempt.release_stale", root=tmp_path, dispatch_id="dispatch-b", attempt_id=aid, reason="test", confirm_stale_release="true")
    assert out["outcome"] == "blocked"
    assert "not proven stale-safe" in out["steward_message"]


def test_reconciliation_controls_real_runtime_no_acceptance(tmp_path):
    enqueue_dispatch_request(rec_dispatch_payload(), tmp_path)
    rpath = write_adapter_result(rec_result(), root=tmp_path)
    inspect = execute_office_action("execution_result.inspect_reconciliation", root=tmp_path, dispatch_id="dispatch-result-001")
    assert inspect["outcome"] == "completed"
    out = execute_office_action("execution_result.reconcile", root=tmp_path, dispatch_id="dispatch-result-001", result_path=str(rpath))
    assert out["outcome"] == "completed"
    assert inspect_dispatch_item("dispatch-result-001", tmp_path).provider_metadata["institutional_acceptance_state"] == "not_granted"
    assert inspect_reconciliation("dispatch-result-001", tmp_path)["institutional_acceptance_state"] == "not_granted"
    assert execute_office_action("execution_result.report", root=tmp_path, dispatch_id="dispatch-result-001")["outcome"] == "completed"


def test_unknown_and_missing_fields_rejected(tmp_path):
    assert execute_office_action("unknown.action", root=tmp_path)["outcome"] == "blocked"
    assert execute_office_action("execution_session.preview", root=tmp_path)["outcome"] == "blocked"
