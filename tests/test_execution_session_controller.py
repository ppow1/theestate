import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from estate.core.execution_session_controller import ExecutionSessionController, SESSION_STAGES, SESSION_STATES
from estate.core.codex_live_execution_gate import CodexLiveExecutionGate
from estate.core.codex_bridge import run_codex_bridge_request
from estate.core.execution_attempt_runtime import ExecutionAttemptRuntime

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from estate.core.codex_bridge import run_codex_bridge_request
from estate.core.codex_live_execution_gate import CodexLiveExecutionGate, current_workspace
from estate.core.execution_adapter_handoff_runtime import prepare_handoff
from estate.core.execution_dispatch import enqueue_dispatch_request, inspect_dispatch_item


def write_prompt(root):
    p = root / "collaboration/work_packages/pending/WP-0506.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("Do WP-0506.\n", encoding="utf-8")


def init_git(root):
    import subprocess
    root.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Tester"], cwd=root, check=True)
    write_prompt(root)
    (root / ".gitignore").write_text("runtime/\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=root, check=True, capture_output=True)


def dispatch_payload(**overrides):
    data = {
        "dispatch_id": "dispatch-wp-0506",
        "work_package_id": "WP-0506",
        "title": "Live gate",
        "provider": "codex-cli-openai",
        "profile_label": "default",
        "classification": "Estate Internal",
        "state": "Ready",
        "prompt_source": "collaboration/work_packages/pending/WP-0506.md",
        "sandbox": "workspace-write",
        "allowed_read_paths": ["collaboration/work_packages/pending"],
        "allowed_write_paths": ["src/estate/core", "tests", "docs/integration"],
        "allowed_providers": ["codex-cli-openai"],
        "provider_metadata": {
            "decision_reference": "traffic-controller/WP-0506/authorized",
            "provider_type": "codex-cli",
            "codex_home_profile": "default",
            "traffic_controller_authorization_reference": "traffic-controller/WP-0506/movement",
        },
    }
    data.update(overrides)
    return data


def prepared_root(tmp_path):
    init_git(tmp_path)
    enqueue_dispatch_request(dispatch_payload(), tmp_path)
    prepared = prepare_handoff("dispatch-wp-0506", tmp_path)
    assert prepared["status"] == "handoff_validated"
    import subprocess
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "--allow-empty", "-m", "prepare"], cwd=tmp_path, check=True, capture_output=True)
    return prepared


def auth(root, prepared, **overrides):
    commit = current_workspace(root)["commit"]
    data = {
        "execution_authorization_id": "auth-wp-0506",
        "dispatch_id": "dispatch-wp-0506",
        "adapter_request_id": prepared["adapter_request"]["adapter_request_id"],
        "provider_id": "codex-cli-openai",
        "provider_type": "codex-cli",
        "work_package_id": "WP-0506",
        "decision_reference": "traffic-controller/WP-0506/authorized",
        "traffic_controller_authorization_reference": "traffic-controller/WP-0506/movement",
        "steward_approval_reference": "steward/WP-0506/live-approved",
        "approved_by": "Steward",
        "approved_at": "2026-07-10T00:00:00Z",
        "approval_scope": "single dispatch execute",
        "allowed_sandbox": "workspace-write",
        "allowed_read_paths": ["collaboration/work_packages/pending"],
        "allowed_write_paths": ["src/estate/core", "tests", "docs/integration"],
        "approved_codex_profile": "default",
        "workspace_commit": commit,
        "workspace_clean_required": True,
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat().replace("+00:00", "Z"),
        "revoked": False,
        "metadata": {},
    }
    data.update(overrides)
    path = root.parent / f"{root.name}_auth.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def gate(root, calls=None, fail=False, binary=True):
    def fake_runner(bridge_request, **kwargs):
        if calls is not None:
            calls.append(bridge_request.request_id)
        result = run_codex_bridge_request(bridge_request, root=root, dry_run=True)
        result.status = "failed" if fail else "succeeded"
        result.stderr = "fake failure" if fail else ""
        result.final_message = "fake done"
        return result
    return CodexLiveExecutionGate(root=root, bridge_runner=fake_runner, codex_binary_checker=lambda _b: binary)


def assert_blocked(tmp_path, **auth_overrides):
    prepared = prepared_root(tmp_path)
    path = auth(tmp_path, prepared, **auth_overrides)
    result = gate(tmp_path).preview("dispatch-wp-0506", path)
    assert result["status"] == "blocked"
    assert result["live_provider_called"] is False
    return result




def gate(root, calls=None, fail=False):
    def fake_runner(bridge_request, **kwargs):
        if calls is not None:
            calls.append(bridge_request.request_id)
        result = run_codex_bridge_request(bridge_request, root=root, dry_run=True)
        result.status = "failed" if fail else "succeeded"
        result.stderr = "fake failure" if fail else ""
        result.final_message = "fake done"
        return result
    return CodexLiveExecutionGate(root=root, bridge_runner=fake_runner, codex_binary_checker=lambda _b: True)


def test_successful_preview_with_no_provider_call(tmp_path):
    prepared = prepared_root(tmp_path)
    calls = []
    result = ExecutionSessionController(root=tmp_path, gate=gate(tmp_path, calls)).preview("dispatch-wp-0506", auth(tmp_path, prepared))
    assert result["state"] == "previewed"
    assert result["live_provider_called"] is False
    assert calls == []
    assert (tmp_path / "runtime/execution_adapters/sessions" / f'{result["execution_session_id"]}.json').is_file()


def test_successful_fake_runner_start_exactly_once_validation_ready(tmp_path):
    prepared = prepared_root(tmp_path)
    calls = []
    result = ExecutionSessionController(root=tmp_path, gate=gate(tmp_path, calls)).start("dispatch-wp-0506", auth(tmp_path, prepared), confirm_live_execution=True)
    assert result["state"] == "completed_execution"
    assert result["live_provider_called"] is True
    assert len(calls) == 1
    assert result["reconciliation_reference"]
    assert "institutional_acceptance" not in json.dumps(result).lower()


def test_missing_authorization_blocks(tmp_path):
    prepared_root(tmp_path)
    result = ExecutionSessionController(root=tmp_path, gate=gate(tmp_path)).preview("dispatch-wp-0506", tmp_path / "missing.json")
    assert result["state"] == "blocked"
    assert result["live_provider_called"] is False


def test_dirty_workspace_blocks_start(tmp_path):
    prepared = prepared_root(tmp_path)
    (tmp_path / "dirty.txt").write_text("dirty", encoding="utf-8")
    result = ExecutionSessionController(root=tmp_path, gate=gate(tmp_path)).start("dispatch-wp-0506", auth(tmp_path, prepared), confirm_live_execution=True)
    assert result["state"] == "blocked"
    assert "dirty" in json.dumps(result).lower()


def test_active_conflicting_lease_blocks(tmp_path):
    prepared = prepared_root(tmp_path)
    authorization = auth(tmp_path, prepared)
    ExecutionAttemptRuntime(root=tmp_path).acquire_lease(dispatch_id="dispatch-wp-0506", adapter_request_id=prepared["adapter_request"]["adapter_request_id"], provider_id="codex-cli-openai", provider_type="codex-cli", work_package_id="WP-0506")
    result = ExecutionSessionController(root=tmp_path, gate=gate(tmp_path)).start("dispatch-wp-0506", authorization, confirm_live_execution=True)
    assert result["state"] == "blocked"
    assert "active execution lease" in json.dumps(result)


def test_provider_failure_preserves_single_call(tmp_path):
    prepared = prepared_root(tmp_path)
    calls = []
    result = ExecutionSessionController(root=tmp_path, gate=gate(tmp_path, calls, fail=True)).start("dispatch-wp-0506", auth(tmp_path, prepared), confirm_live_execution=True)
    assert result["state"] == "failed"
    assert result["live_provider_called"] is True
    assert len(calls) == 1
    assert result["result_reference"]


def test_resume_refuses_ambiguous_provider_call(tmp_path):
    prepared = prepared_root(tmp_path)
    controller = ExecutionSessionController(root=tmp_path, gate=gate(tmp_path))
    result = controller.preview("dispatch-wp-0506", auth(tmp_path, prepared))
    path = tmp_path / "runtime/execution_adapters/sessions" / f'{result["execution_session_id"]}.json'
    data = json.loads(path.read_text())
    data["live_provider_called"] = True
    data["result_reference"] = None
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    resumed = controller.resume(result["execution_session_id"])
    assert resumed["state"] == "failed"
    assert "ambiguous" in resumed["attention_reason"]


def test_status_and_report_are_idempotent(tmp_path):
    prepared = prepared_root(tmp_path)
    controller = ExecutionSessionController(root=tmp_path, gate=gate(tmp_path))
    result = controller.preview("dispatch-wp-0506", auth(tmp_path, prepared))
    assert controller.status(result["execution_session_id"]) == controller.status(result["execution_session_id"])
    assert controller.report(result["execution_session_id"]) == controller.report(result["execution_session_id"])


def test_stage_and_state_constants_cover_required_values():
    assert "provider_execution_preview_or_start" in SESSION_STAGES
    assert "validation_ready" in SESSION_STATES
    assert "completed_execution" in SESSION_STATES
