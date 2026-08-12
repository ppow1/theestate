import json
import os
import re
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "deploy_grace_comms8_runtime.ps1"


def test_deployment_is_selective_and_contains_accepted_surface():
    text = SCRIPT.read_text(encoding="utf-8")
    manifest_block = text.split("$relativeFiles = @(", 1)[1].split(")", 1)[0]
    manifest = re.findall(r"'([^']+)'", manifest_block)
    assert len(manifest) == 116
    assert "src\\estate\\core\\openwebui_engineering_workflow.py" in manifest
    assert {
        "config\\runtime\\gpu_runtime_lanes.json",
        "config\\providers\\qwen_local_text.json",
        "config\\providers\\qwen_local_text_p100.json",
        "schemas\\execution_provider_adapter_request_v1.schema.json",
        "schemas\\engineering\\commission_execution_authority_v1.schema.json",
        "schemas\\engineering\\commission_ptm_evidence_v1.schema.json",
        "schemas\\engineering\\engineering_authorization_v1.schema.json",
        "schemas\\dispatch\\execution_metadata_v1.schema.json",
        "schemas\\compute_resource_requirements_v1.schema.json",
        "schemas\\operations_control\\operations_decision_v1.schema.json",
        "schemas\\providers\\qwen_local_text_execution_extension_v1.schema.json",
        "schemas\\providers\\provider_receipt_v1.schema.json",
    }.issubset(set(manifest))
    required = [
        "autonomous_chatgpt_mailbox_worker.py",
        "grace_consultation_loop.py",
        "consultation_store.py",
        "openwebui_resident_surface.py",
        "openwebui_engineering_workflow.py",
        "execution_dispatch.py",
        "gpu_runtime_lanes.py",
        "resident_gateway.py",
        "chatgpt_mailbox_worker_browser.cjs",
        "comms8_streamable_http_adapter.py",
    ]
    assert all(name in text for name in required)
    assert "repository wholesale" in text
    assert "Copy-Item" in text
    assert "SourceRoot" in text and "TargetRoot" in text and "PreflightOnly" in text and "Deploy" in text
    assert "ExpectedSourceSha" in text and "PREFLIGHT_BLOCKED" in text


def test_bounded_local_runtime_config_closure_is_finite_and_selective():
    text = SCRIPT.read_text(encoding="utf-8")
    manifest_block = text.split("$relativeFiles = @(", 1)[1].split(")", 1)[0]
    manifest = set(re.findall(r"'([^']+)'", manifest_block))
    required = {
        "config\\runtime\\gpu_runtime_lanes.json",
        "config\\providers\\qwen_local_text.json",
        "config\\providers\\qwen_local_text_p100.json",
        "schemas\\execution_provider_adapter_request_v1.schema.json",
        "schemas\\engineering\\commission_execution_authority_v1.schema.json",
        "schemas\\engineering\\commission_ptm_evidence_v1.schema.json",
        "schemas\\engineering\\engineering_authorization_v1.schema.json",
        "schemas\\dispatch\\execution_metadata_v1.schema.json",
        "schemas\\compute_resource_requirements_v1.schema.json",
        "schemas\\operations_control\\operations_decision_v1.schema.json",
        "schemas\\providers\\qwen_local_text_execution_extension_v1.schema.json",
        "schemas\\providers\\provider_receipt_v1.schema.json",
    }
    assert required <= manifest
    assert "config\\runtime\\openwebui.json" not in manifest
    assert "config\\providers\\unknown_provider.json" not in manifest
    for relative in required:
        assert (ROOT / relative).is_file()


def test_authority_schema_registry_closure_is_explicit_and_finite():
    source = (ROOT / "src/estate/core/authority_schema_runtime.py").read_text(encoding="utf-8")
    expected = {
        "engineering/commission_execution_authority_v1.schema.json",
        "engineering/commission_ptm_evidence_v1.schema.json",
        "engineering/engineering_authorization_v1.schema.json",
        "dispatch/execution_metadata_v1.schema.json",
        "execution_provider_adapter_request_v1.schema.json",
        "compute_resource_requirements_v1.schema.json",
        "operations_control/operations_decision_v1.schema.json",
        "providers/qwen_local_text_execution_extension_v1.schema.json",
        "providers/provider_receipt_v1.schema.json",
    }
    assert set(re.findall(r'"([^"]+\.schema\.json)"', source)) >= expected
    manifest_block = (SCRIPT.read_text(encoding="utf-8").split("$relativeFiles = @(", 1)[1].split(")", 1)[0])
    manifest = set(re.findall(r"'([^']+)'", manifest_block))
    assert {"schemas\\" + path.replace("/", "\\") for path in expected} <= manifest
    assert "schemas\\residents\\resident_capability_manifest_v1.schema.json" not in manifest


def test_grace_catalog_contract_is_canonical():
    source = (ROOT / "src/estate/core/openwebui_resident_surface.py").read_text(encoding="utf-8")
    for name in (
        "grace_runtime_bridge",
        "estate_comms8_create_reasoning_request",
        "estate_comms8_list_requests",
        "estate_comms8_read_request",
        "estate_comms8_claim_request",
        "estate_comms8_acknowledge_request",
        "estate_comms8_respond_request",
        "estate_comms8_resolve_request",
    ):
        assert name in source


def test_deployment_safety_contract_is_fail_closed_and_transactional():
    text = SCRIPT.read_text(encoding="utf-8")
    for marker in (
        "integration/grace-comms8-parallelism", "UNKNOWN_DRIFT", "EXPECTED_PREVIOUS_OVERLAY",
        "INTEGRATION_EQUIVALENT", "pre_target_sha256", "post_target_sha256", "backups",
        "PROVEN_TRACKED_PREDECESSOR", "Find-TrackedBlobProvenance", "CRLF_TO_LF_FOR_GIT_BLOB_ONLY",
        "runtime_import_closure.py", "IMPORT_CLOSURE_BLOCKED", "import_closure",
        "metadata.json", "Target changed after preflight", "Temporary source hash failed",
        "Backup verification failed", "DEPLOYMENT_SUCCESS", "DEPLOYMENT_ROLLED_BACK",
        "ROLLBACK_INCOMPLETE", "rollback_available", "rollback_performed",
    ):
        assert marker in text


def test_preflight_fixture_has_zero_target_mutation():
    # Exercise the real PowerShell parser/contract against an isolated target.
    # The target is disposable and is never the canonical runtime.
    with TemporaryDirectory() as temp:
        target = Path(temp) / "runtime"
        target.mkdir()
        subprocess.run(["git", "init", "-q", str(target)], check=True)
        subprocess.run(["git", "-C", str(target), "-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid", "commit", "--allow-empty", "-qm", "fixture"], check=True)
        command = [
            "pwsh", "-NoLogo", "-NoProfile", "-NonInteractive", "-File", str(SCRIPT),
            "-SourceRoot", str(ROOT), "-TargetRoot", str(target), "-PreflightOnly",
        ]
        before = sorted(str(p.relative_to(target)) for p in target.rglob("*"))
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        after = sorted(str(p.relative_to(target)) for p in target.rglob("*"))
        receipt = json.loads(result.stdout)
        assert receipt["preflight_result"] == "PREFLIGHT_PASS"
        assert before == after
        assert not (target / "runtime" / "deployments").exists()


def test_required_transactional_operations_are_explicitly_covered():
    text = SCRIPT.read_text(encoding="utf-8")
    requirements = {
        "backup_created_before_mutation": "New-Item -ItemType Directory -Path $backup",
        "backup_hash_verification": "Backup verification failed",
        "source_hash_verification": "Temporary source hash failed",
        "atomic_same_volume_replace": "Move-Item -LiteralPath $tmp -Destination $dp -Force",
        "post_hash_verification": "Post-write hash failed",
        "partial_failure_rollback": "foreach($m in $manifest){$bd=Join-Path $backup",
        "exact_restore_verification": "Rollback verification failed",
        "blocked_receipt_status": "PREFLIGHT_BLOCKED",
    }
    for name, marker in requirements.items():
        assert marker in text, name
