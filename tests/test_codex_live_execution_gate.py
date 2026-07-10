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
    subprocess.run(["git", "commit", "-m", "prepare"], cwd=tmp_path, check=True, capture_output=True)
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


def test_valid_authorization_record_acceptance_and_preview_no_provider_call(tmp_path):
    prepared = prepared_root(tmp_path)
    calls = []
    result = gate(tmp_path, calls).preview("dispatch-wp-0506", auth(tmp_path, prepared))
    assert result["status"] == "preview_ready"
    assert result["live_provider_called"] is False
    assert calls == []


def test_required_authority_rejections(tmp_path):
    assert any("steward_approval_reference" in e for e in assert_blocked(tmp_path / "a", steward_approval_reference="")["errors"])
    assert any("traffic_controller_authorization_reference" in e for e in assert_blocked(tmp_path / "b", traffic_controller_authorization_reference="")["errors"])


def test_mismatch_expired_and_revoked_rejections(tmp_path):
    assert any("dispatch_id mismatch" in e for e in assert_blocked(tmp_path / "a", dispatch_id="other")["errors"])
    assert any("adapter_request_id mismatch" in e for e in assert_blocked(tmp_path / "b", adapter_request_id="other")["errors"])
    past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat().replace("+00:00", "Z")
    assert any("expired" in e for e in assert_blocked(tmp_path / "c", expires_at=past)["errors"])
    assert any("revoked" in e for e in assert_blocked(tmp_path / "d", revoked=True)["errors"])


def test_workspace_commit_mismatch_dirty_and_missing_binary_rejections(tmp_path):
    assert any("commit" in e for e in assert_blocked(tmp_path / "a", workspace_commit="deadbeef")["errors"])
    prepared = prepared_root(tmp_path / "b")
    (tmp_path / "b" / "dirty.txt").write_text("dirty")
    assert any("dirty" in e for e in gate(tmp_path / "b").preview("dispatch-wp-0506", auth(tmp_path / "b", prepared))["errors"])
    prepared = prepared_root(tmp_path / "c")
    assert any("binary" in e for e in gate(tmp_path / "c", binary=False).preview("dispatch-wp-0506", auth(tmp_path / "c", prepared))["errors"])


def test_profile_sandbox_path_and_confirmation_rejections(tmp_path):
    assert any("profile" in e for e in assert_blocked(tmp_path / "a", approved_codex_profile="missing")["errors"])
    assert any("sandbox" in e for e in assert_blocked(tmp_path / "b", allowed_sandbox="danger-full-access")["errors"])
    assert any("write path outside authorization" in e for e in assert_blocked(tmp_path / "c", allowed_write_paths=["archive"])["errors"])
    prepared = prepared_root(tmp_path / "d")
    result = gate(tmp_path / "d").execute("dispatch-wp-0506", auth(tmp_path / "d", prepared), confirm_live_execution=False)
    assert any("confirmation" in e for e in result["errors"])
    assert result["live_provider_called"] is False


def test_fake_runner_execute_success_exactly_once_and_dispatch_running(tmp_path):
    prepared = prepared_root(tmp_path)
    calls = []
    result = gate(tmp_path, calls).execute("dispatch-wp-0506", auth(tmp_path, prepared), confirm_live_execution=True)
    assert result["status"] == "completed"
    assert result["live_provider_called"] is True
    assert len(calls) == 1
    assert inspect_dispatch_item("dispatch-wp-0506", tmp_path).state == "Running"


def test_fake_runner_execute_failure_records_live_call_without_completion_or_repair(tmp_path):
    prepared = prepared_root(tmp_path)
    calls = []
    result = gate(tmp_path, calls, fail=True).execute("dispatch-wp-0506", auth(tmp_path, prepared), confirm_live_execution=True)
    assert result["status"] == "failed"
    assert result["live_provider_called"] is True
    assert len(calls) == 1
    assert inspect_dispatch_item("dispatch-wp-0506", tmp_path).state == "Running"
    text = json.dumps(result).lower()
    assert "stash" not in text and "reset" not in text and "clean" not in text and "merge" not in text and "institutional_acceptance" not in text
