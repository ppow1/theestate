from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "Validate-GovernedCodexCommission.ps1"


def valid_request() -> dict:
    now = datetime.now(timezone.utc)
    return {
        "commission_id": "commission-test-001",
        "grace_objective_id": "grace-obj-test-001",
        "capability_inquiry_id": "capinq-test-001",
        "helen_assessment_reference": "runtime/helen/assessment-test.json",
        "ptm_dependency_reference": "ptm/dependency-test-001",
        "dispatch_id": "dispatch-test-001",
        "provider_id": "codex.execution.cli",
        "adapter_id": "codex-cli-execution-adapter",
        "adapter_version": "1.0.0",
        "requested_capabilities": ["documentation_draft"],
        "classification": "Estate Internal",
        "repository_root": ".",
        "source_commit": "a" * 40,
        "sandbox_mode": "workspace-write",
        "authorized_read_paths": ["docs", "src"],
        "authorized_write_paths": ["docs/operations/example.md"],
        "prohibited_paths": [".git", "archive", "runtime"],
        "exact_expected_outputs": ["docs/operations/example.md"],
        "acceptance_criteria": ["artifact exists"],
        "validation_commands": ["python -m pytest -q"],
        "timeout_seconds": 180,
        "cancellation_state": "not_requested",
        "steward_authorization_reference": "steward/authorization-test-001",
        "traffic_controller_authorization_reference": "traffic/authorization-test-001",
        "decision_reference": "decision/test-001",
        "boundary_review_reference": "boundary/test-001",
        "evidence": {
            "observed_at": now.isoformat().replace("+00:00", "Z"),
            "expires_at": (now + timedelta(minutes=30)).isoformat().replace("+00:00", "Z"),
            "qualification_references": ["qualification/test.json"],
            "health_references": ["health/test.json"],
            "availability_references": ["availability/test.json"],
            "capacity_references": ["capacity/test.json"],
            "authorization_references": ["authorization/test.json"],
        },
        "unrestricted_shell_authority": False,
        "automatic_merge_authority": False,
        "autonomous_institutional_acceptance_authority": False,
    }


def run_validator(tmp_path: Path, payload: object, *, json_output: bool = False):
    request_path = tmp_path / "request.json"
    request_path.write_text(json.dumps(payload), encoding="utf-8")
    command = ["pwsh", "-NoProfile", "-File", str(SCRIPT), "-RequestPath", str(request_path)]
    if json_output:
        command.append("-Json")
    before = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*"))
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    after = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*"))
    return result, before, after


def test_valid_bounded_documentation_commission(tmp_path):
    result, before, after = run_validator(tmp_path, valid_request())
    assert result.returncode == 0, result.stdout + result.stderr
    assert "VALID" in result.stdout
    assert before == after


def test_malformed_json(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{not json", encoding="utf-8")
    result = subprocess.run(["pwsh", "-NoProfile", "-File", str(SCRIPT), "-RequestPath", str(path), "-Json"], capture_output=True, text=True, check=False)
    assert result.returncode != 0
    assert json.loads(result.stdout)["valid"] is False


def test_missing_required_field_is_reported(tmp_path):
    payload = valid_request(); del payload["decision_reference"]
    result, _, _ = run_validator(tmp_path, payload)
    assert result.returncode != 0
    assert "decision_reference" in result.stdout


def test_provider_adapter_and_capability_fail_closed(tmp_path):
    payload = valid_request(); payload["provider_id"] = "other"; payload["adapter_id"] = "wrong"; payload["requested_capabilities"] = ["not-supported"]
    result, _, _ = run_validator(tmp_path, payload)
    assert result.returncode != 0
    assert "provider_id" in result.stdout and "adapter_id" in result.stdout and "unsupported capability" in result.stdout


def test_danger_full_access_and_authority_flags_fail_closed(tmp_path):
    payload = valid_request(); payload["sandbox_mode"] = "danger-full-access"; payload["unrestricted_shell_authority"] = True; payload["automatic_merge_authority"] = True; payload["autonomous_institutional_acceptance_authority"] = True
    result, _, _ = run_validator(tmp_path, payload)
    assert result.returncode != 0
    assert "danger-full-access" in result.stdout and "merge authority" in result.stdout


def test_bridge_policy_profile_bypass_and_cloud_controls_fail_closed(tmp_path):
    payload = valid_request()
    payload.update({
        "codex_provider_profile": "unapproved-profile",
        "approval_policy": "on-request",
        "bypass_flags": ["dangerously-skip-permissions"],
        "cloud_allowed": True,
        "cloud_apply_requested": True,
        "cloud_dispatch_requested": True,
    })
    result, before, after = run_validator(tmp_path, payload, json_output=True)
    body = json.loads(result.stdout)
    assert result.returncode != 0
    assert len(body["errors"]) >= 5
    assert before == after


def test_workspace_write_requires_explicit_write_scope(tmp_path):
    payload = valid_request()
    payload["authorized_write_paths"] = []
    result, _, _ = run_validator(tmp_path, payload)
    assert result.returncode != 0
    assert "workspace-write" in result.stdout


def test_paths_fail_closed(tmp_path):
    for output in ["C:/outside.md", "docs/../outside.md", "archive/out.md"]:
        payload = valid_request(); payload["exact_expected_outputs"] = [output]
        result, _, _ = run_validator(tmp_path, payload)
        assert result.returncode != 0
    payload = valid_request(); payload["authorized_write_paths"] = ["runtime/output"]
    result, _, _ = run_validator(tmp_path, payload)
    assert result.returncode != 0


def test_expired_evidence_authorization_and_required_lists_fail_closed(tmp_path):
    payload = valid_request(); payload["evidence"]["expires_at"] = "2000-01-01T00:00:00Z"; payload["steward_authorization_reference"] = ""; payload["exact_expected_outputs"] = []; payload["acceptance_criteria"] = []; payload["validation_commands"] = []
    result, _, _ = run_validator(tmp_path, payload)
    assert result.returncode != 0
    assert "expired" in result.stdout and "expected output" in result.stdout


def test_cancellation_is_truthful_and_validator_does_not_invoke_provider(tmp_path):
    payload = valid_request(); payload["cancellation_state"] = "requested"
    result, before, after = run_validator(tmp_path, payload, json_output=True)
    body = json.loads(result.stdout)
    assert result.returncode != 0 and body["valid"] is False
    assert body["provider_invoked"] is False and body["lifecycle_mutated"] is False
    assert before == after


def test_json_output_is_machine_readable_and_accumulates_errors(tmp_path):
    payload = valid_request(); payload["provider_id"] = "wrong"; payload["adapter_id"] = "wrong"; payload["exact_expected_outputs"] = ["/outside"]
    result, _, _ = run_validator(tmp_path, payload, json_output=True)
    body = json.loads(result.stdout)
    assert result.returncode != 0 and len(body["errors"]) >= 3
    assert body["validation_only"] is True and body["provider_invoked"] is False
