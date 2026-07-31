from __future__ import annotations

import json
import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from estate.core.execution_provider_adapter import ExecutionProviderAdapterRequest
from estate.core.execution_provider_adapter_runtime import load_registered_adapter
import estate.core.qwen_local_text_execution_provider_adapter as qwen_adapter_module
from estate.core.qwen_local_text_execution_provider_adapter import QwenLocalTextExecutionProviderAdapter

CONFIG_PATH = Path("config/providers/qwen_local_text.json")


def _request(tmp_path: Path, output_path: str = "docs/operations/examples/qwen-test.md", receipt_path: str = "runtime/engineering_adapter_receipts/qwen-adapter-qwen-test.json", **metadata):
    now = datetime.now(timezone.utc).replace(microsecond=0)
    values = {
        "requested_capability": "documentation_draft",
        "authorization_reference": "steward/qwen-test-authorization",
        "evidence_observed_at": now.isoformat().replace("+00:00", "Z"),
        "evidence_expires_at": (now + timedelta(hours=1)).isoformat().replace("+00:00", "Z"),
        "authorized_model_identity": "qwen3:8b",
        "prompt_text": "Explain the governed boundary in one sentence.",
        "grace_objective_id": "grace-qwen-test",
        "capability_inquiry_reference": "capinq-qwen-test",
        "helen_assessment_reference": "capassess-qwen-test",
        "source_commit": "a" * 40,
        "sandbox": "workspace-write",
        "shell_authority": False,
        "automatic_merge_authority": False,
        "institutional_acceptance_authority": False,
        "provider_receipt_path": receipt_path,
    }
    values.update(metadata)
    return ExecutionProviderAdapterRequest.create(
        adapter_request_id="adapter-qwen-test",
        dispatch_id="dispatch-qwen-test",
        provider_id="qwen.local.text",
        provider_type="execution",
        prompt_source="test prompt",
        write_scope_paths=[output_path, receipt_path] if receipt_path else [output_path],
        expected_outputs=[output_path, receipt_path] if receipt_path else [output_path],
        metadata=values,
    )


def _transport(response_text="Generated local Qwen text.", model="qwen3:8b", health=True, health_model="qwen3:8b"):
    def call(method, url, payload, timeout):
        if method == "GET":
            return (200, {"models": [{"name": health_model}]}) if health else (503, {})
        return (200, {"model": model, "response": response_text})
    return call


def _inject_partial_fdopen(monkeypatch, failing_call: int, phase: str = "write"):
    original_fdopen = qwen_adapter_module.os.fdopen
    calls = {"count": 0}

    def fdopen(fd, *args, **kwargs):
        calls["count"] += 1
        stream = original_fdopen(fd, *args, **kwargs)
        if calls["count"] != failing_call:
            return stream

        class FailingStream:
            write_calls = 0

            def write(self, data):
                self.write_calls += 1
                if phase == "write":
                    stream.write(data[:max(1, len(data) // 2)])
                    raise OSError("injected write failure")
                if phase == "short":
                    return stream.write(data[:max(1, len(data) // 2)])
                if phase == "zero_after_partial":
                    if self.write_calls == 1:
                        return stream.write(data[:max(1, len(data) // 2)])
                    return 0
                return stream.write(data)

            def flush(self):
                if phase == "flush":
                    stream.flush()
                    raise OSError("injected flush failure")
                return stream.flush()

            def fileno(self):
                return stream.fileno()

            def close(self):
                if phase == "close":
                    stream.close()
                    raise OSError("injected close failure")
                return stream.close()

        return FailingStream()

    monkeypatch.setattr(qwen_adapter_module.os, "fdopen", fdopen)
    return calls


def test_provider_catalog_registration_and_adapter_identity(tmp_path):
    adapter = load_registered_adapter(_request(tmp_path), root=Path.cwd())
    assert isinstance(adapter, QwenLocalTextExecutionProviderAdapter)
    assert adapter.provider_id == "qwen.local.text"
    assert adapter.adapter_id == "qwen-local-ollama-text-adapter"


def test_valid_documentation_request_uses_mock_local_service(tmp_path):
    adapter = QwenLocalTextExecutionProviderAdapter(root=tmp_path, config_path=CONFIG_PATH, http_call=_transport())
    result = adapter.submit(_request(tmp_path))
    assert result.status == "completed"
    assert result.metadata["live_provider_called"] is True
    assert (tmp_path / "docs/operations/examples/qwen-test.md").read_text() == "Generated local Qwen text."
    receipt = tmp_path / result.metadata["provider_receipt"]
    payload = json.loads(receipt.read_text())
    assert payload["provider_id"] == "qwen.local.text"
    assert payload["actual_model_identity"] == "qwen3:8b"
    assert payload["endpoint_local"] is True
    assert payload["artifacts"][0]["sha256"]
    assert result.metadata["provider_receipt"] == "runtime/engineering_adapter_receipts/qwen-adapter-qwen-test.json"
    assert payload["provider_result_state"] == "completed"
    assert payload["declared_artifact_paths"] == result.artifacts


def test_unsupported_capability_is_rejected_before_provider_call(tmp_path):
    calls = []
    adapter = QwenLocalTextExecutionProviderAdapter(root=tmp_path, config_path=CONFIG_PATH, http_call=lambda *args: calls.append(args))
    result = adapter.submit(_request(tmp_path, requested_capability="repository_implementation"))
    assert result.status == "blocked" and calls == []


def test_missing_model_and_endpoint_configuration_fail_closed(tmp_path):
    config = json.loads((tmp_path / "config/providers/qwen_local_text.json").read_text()) if (tmp_path / "config/providers/qwen_local_text.json").exists() else json.loads(Path("config/providers/qwen_local_text.json").read_text())
    config["model_identity"] = ""
    path = tmp_path / "qwen.json"; path.write_text(json.dumps(config))
    adapter = QwenLocalTextExecutionProviderAdapter(root=tmp_path, config_path=path)
    assert adapter.submit(_request(tmp_path)).status == "blocked"
    config["model_identity"] = "qwen3:8b"; config["endpoint_address"] = "http://example.invalid:11434"; path.write_text(json.dumps(config))
    assert adapter.submit(_request(tmp_path)).status == "blocked"


def test_missing_configuration_fails_closed_without_provider_call(tmp_path):
    calls = []
    adapter = QwenLocalTextExecutionProviderAdapter(
        root=tmp_path,
        config_path=tmp_path / "missing-qwen.json",
        http_call=lambda *args: calls.append(args),
    )
    result = adapter.submit(_request(tmp_path))
    assert result.status == "blocked"
    assert calls == []


def test_health_failure_and_stale_evidence_fail_closed(tmp_path):
    adapter = QwenLocalTextExecutionProviderAdapter(root=tmp_path, config_path=CONFIG_PATH, http_call=_transport(health=False))
    result = adapter.submit(_request(tmp_path))
    assert result.status == "failed"
    failure = json.loads((tmp_path / result.metadata["provider_receipt"]).read_text())
    assert failure["provider_result_state"] == "failed" and failure["validation_result"] == "failed"
    assert not (tmp_path / "docs/operations/examples/qwen-test.md").exists()
    old = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat().replace("+00:00", "Z")
    assert adapter.submit(_request(tmp_path, evidence_expires_at=old)).status == "blocked"


def test_remote_endpoint_and_model_mismatch_fail_closed(tmp_path):
    config = json.loads(Path("config/providers/qwen_local_text.json").read_text())
    config["endpoint_address"] = "https://example.invalid"
    path = tmp_path / "qwen.json"; path.write_text(json.dumps(config))
    assert QwenLocalTextExecutionProviderAdapter(root=tmp_path, config_path=path).submit(_request(tmp_path)).status == "blocked"
    adapter = QwenLocalTextExecutionProviderAdapter(root=tmp_path, config_path=CONFIG_PATH, http_call=_transport(model="qwen2.5-coder:7b", health_model="qwen3:8b"))
    result = adapter.submit(_request(tmp_path))
    assert result.status == "failed"
    failure = json.loads((tmp_path / result.metadata["provider_receipt"]).read_text())
    assert failure["actual_model_identity"] == "qwen2.5-coder:7b"


def test_cancellation_timeout_authority_and_shell_boundaries(tmp_path):
    calls = []
    adapter = QwenLocalTextExecutionProviderAdapter(root=tmp_path, config_path=CONFIG_PATH, http_call=lambda *args: calls.append(args))
    result = adapter.submit(_request(tmp_path, cancel_requested=True, shell_authority=True, automatic_merge_authority=True, institutional_acceptance_authority=True))
    assert result.status == "blocked" and calls == []


def test_malformed_response_and_exact_output_enforcement(tmp_path):
    def malformed(method, url, payload, timeout):
        return (200, {"model": "qwen3:8b"})
    result = QwenLocalTextExecutionProviderAdapter(root=tmp_path, config_path=CONFIG_PATH, http_call=malformed).submit(_request(tmp_path))
    assert result.status == "failed"
    assert result.metadata["provider_receipt"]
    adapter = QwenLocalTextExecutionProviderAdapter(root=tmp_path, config_path=CONFIG_PATH, http_call=_transport())
    result = adapter.submit(_request(tmp_path, output_path="runtime/other.md"))
    assert result.status == "blocked"


def test_unbounded_output_is_rejected_before_artifact_write(tmp_path):
    config = json.loads(Path("config/providers/qwen_local_text.json").read_text())
    config["output_limits"]["max_artifact_bytes"] = 8
    path = tmp_path / "qwen.json"
    path.write_text(json.dumps(config))
    adapter = QwenLocalTextExecutionProviderAdapter(
        root=tmp_path,
        config_path=path,
        http_call=_transport(response_text="this output is too large"),
    )
    result = adapter.submit(_request(tmp_path))
    assert result.status == "failed"
    assert not (tmp_path / "docs/operations/examples/qwen-test.md").exists()


def test_dry_run_does_not_call_service_or_grant_authority(tmp_path):
    calls = []
    adapter = QwenLocalTextExecutionProviderAdapter(root=tmp_path, config_path=CONFIG_PATH, http_call=lambda *args: calls.append(args))
    result = adapter.dry_run(_request(tmp_path))
    assert result.status == "dry_run_completed" and calls == []
    assert result.metadata["live_provider_called"] is False


def test_missing_receipt_path_blocks_before_provider_call(tmp_path):
    calls = []
    request = _request(tmp_path); request.metadata.pop("provider_receipt_path")
    adapter = QwenLocalTextExecutionProviderAdapter(root=tmp_path, config_path=CONFIG_PATH, http_call=lambda *args: calls.append(args))
    result = adapter.submit(request)
    assert result.status == "blocked" and calls == []
    assert not list(tmp_path.rglob("*"))


def test_receipt_scope_and_expected_output_authority_fail_closed(tmp_path):
    for receipt_path, mutate in [
        ("runtime/other/qwen.json", None),
        ("runtime/engineering_adapter_receipts", None),
        ("runtime/engineering_adapter_receipts/qwen-other.json", "expected"),
        ("runtime/engineering_adapter_receipts/qwen-other.json", "scope"),
    ]:
        request = _request(tmp_path, receipt_path=receipt_path)
        if mutate == "expected":
            request.expected_outputs = [request.expected_outputs[0], "runtime/engineering_adapter_receipts/qwen-adapter-qwen-test.json"]
        if mutate == "scope":
            request.write_scope_paths = [request.write_scope_paths[0], "runtime/engineering_adapter_receipts/qwen-adapter-qwen-test.json"]
        calls = []
        result = QwenLocalTextExecutionProviderAdapter(root=tmp_path, config_path=CONFIG_PATH, http_call=lambda *args: calls.append(args)).submit(request)
        assert result.status == "blocked" and calls == []
    assert not list(tmp_path.rglob("*"))


def test_timeout_failure_receipt_is_truthful_and_prompt_is_not_stored(tmp_path):
    def timeout(method, url, payload, limit):
        if method == "GET":
            return (200, {"models": [{"name": "qwen3:8b"}]})
        raise TimeoutError("bounded test timeout")
    request = _request(tmp_path, prompt_text="private prompt that must never be stored")
    result = QwenLocalTextExecutionProviderAdapter(root=tmp_path, config_path=CONFIG_PATH, http_call=timeout).submit(request)
    assert result.status == "failed"
    receipt = json.loads((tmp_path / result.metadata["provider_receipt"]).read_text())
    assert receipt["timeout_state"] == "timed_out"
    assert "private prompt" not in json.dumps(receipt)
    assert receipt["artifacts"] == []
    assert not (tmp_path / "docs/operations/examples/qwen-test.md").exists()


def test_receipt_write_failure_removes_new_artifact(tmp_path, monkeypatch):
    adapter = QwenLocalTextExecutionProviderAdapter(root=tmp_path, config_path=CONFIG_PATH, http_call=_transport())
    monkeypatch.setattr(adapter, "_write_receipt", lambda *args, **kwargs: (_ for _ in ()).throw(OSError("receipt write failed")))
    result = adapter.submit(_request(tmp_path))
    assert result.status == "failed"
    assert not (tmp_path / "docs/operations/examples/qwen-test.md").exists()


def test_existing_document_blocks_before_provider_and_preserves_bytes(tmp_path):
    document = tmp_path / "docs/operations/examples/qwen-test.md"
    document.parent.mkdir(parents=True); document.write_bytes(b"prior document")
    calls = []
    result = QwenLocalTextExecutionProviderAdapter(root=tmp_path, config_path=CONFIG_PATH, http_call=lambda *args: calls.append(args)).submit(_request(tmp_path))
    assert result.status == "blocked" and result.metadata["live_provider_called"] is False and calls == []
    assert document.read_bytes() == b"prior document"
    assert not (tmp_path / "runtime/engineering_adapter_receipts/qwen-adapter-qwen-test.json").exists()


def test_existing_receipt_blocks_before_provider_and_preserves_bytes(tmp_path):
    receipt = tmp_path / "runtime/engineering_adapter_receipts/qwen-adapter-qwen-test.json"
    receipt.parent.mkdir(parents=True); receipt.write_bytes(b"prior receipt")
    calls = []
    result = QwenLocalTextExecutionProviderAdapter(root=tmp_path, config_path=CONFIG_PATH, http_call=lambda *args: calls.append(args)).submit(_request(tmp_path))
    assert result.status == "blocked" and result.metadata["live_provider_called"] is False and calls == []
    assert receipt.read_bytes() == b"prior receipt"
    assert not (tmp_path / "docs/operations/examples/qwen-test.md").exists()


def test_existing_directories_and_same_target_block_without_mutation(tmp_path):
    document = tmp_path / "docs/operations/examples/qwen-test.md"; document.mkdir(parents=True)
    result = QwenLocalTextExecutionProviderAdapter(root=tmp_path, config_path=CONFIG_PATH, http_call=lambda *args: (_ for _ in ()).throw(AssertionError("provider called"))).submit(_request(tmp_path))
    assert result.status == "blocked"
    receipt = tmp_path / "runtime/engineering_adapter_receipts/qwen-adapter-qwen-test.json"; receipt.mkdir(parents=True)
    result = QwenLocalTextExecutionProviderAdapter(root=tmp_path, config_path=CONFIG_PATH, http_call=lambda *args: (_ for _ in ()).throw(AssertionError("provider called"))).submit(_request(tmp_path))
    assert result.status == "blocked"
    same = _request(tmp_path, output_path="runtime/engineering_adapter_receipts/qwen-adapter-qwen-test.json")
    result = QwenLocalTextExecutionProviderAdapter(root=tmp_path, config_path=CONFIG_PATH, http_call=lambda *args: (_ for _ in ()).throw(AssertionError("provider called"))).submit(same)
    assert result.status == "blocked"


def test_late_document_collision_uses_exclusive_create(tmp_path):
    adapter = QwenLocalTextExecutionProviderAdapter(root=tmp_path, config_path=CONFIG_PATH, http_call=_transport())
    original = adapter._target_collision_errors
    def race(request):
        errors, document, receipt = original(request)
        document.parent.mkdir(parents=True, exist_ok=True); document.write_bytes(b"competing document")
        return errors, document, receipt
    adapter._target_collision_errors = race
    result = adapter.submit(_request(tmp_path))
    assert result.status == "failed"
    assert (tmp_path / "docs/operations/examples/qwen-test.md").read_bytes() == b"competing document"
    assert result.metadata["provider_receipt"]


def test_late_receipt_collision_preserves_competitor_and_removes_new_document(tmp_path, monkeypatch):
    adapter = QwenLocalTextExecutionProviderAdapter(root=tmp_path, config_path=CONFIG_PATH, http_call=_transport())
    original = adapter._write_receipt
    raced = {"done": False}
    def race(request, config, **kwargs):
        if not raced["done"]:
            raced["done"] = True
            receipt = tmp_path / request.metadata["provider_receipt_path"]
            receipt.parent.mkdir(parents=True, exist_ok=True); receipt.write_bytes(b"competing receipt")
        return original(request, config, **kwargs)
    monkeypatch.setattr(adapter, "_write_receipt", race)
    result = adapter.submit(_request(tmp_path))
    assert result.status == "failed"
    assert (tmp_path / "runtime/engineering_adapter_receipts/qwen-adapter-qwen-test.json").read_bytes() == b"competing receipt"
    assert not (tmp_path / "docs/operations/examples/qwen-test.md").exists()
    assert any("failure receipt persistence failed" in error for error in result.errors)


def test_document_partial_write_is_cleaned_and_failure_receipt_is_truthful(tmp_path, monkeypatch):
    _inject_partial_fdopen(monkeypatch, failing_call=1, phase="write")
    adapter = QwenLocalTextExecutionProviderAdapter(root=tmp_path, config_path=CONFIG_PATH, http_call=_transport())
    result = adapter.submit(_request(tmp_path, prompt_text="private prompt must remain redacted"))
    assert result.status == "failed"
    assert not (tmp_path / "docs/operations/examples/qwen-test.md").exists()
    receipt = tmp_path / result.metadata["provider_receipt"]
    payload = json.loads(receipt.read_text())
    assert payload["provider_result_state"] == "failed"
    assert payload["artifacts"] == []
    assert "document persistence" in " ".join(result.errors)
    assert "private prompt" not in receipt.read_text()


def test_success_receipt_partial_write_is_cleaned_then_replaced_by_failure_receipt(tmp_path, monkeypatch):
    _inject_partial_fdopen(monkeypatch, failing_call=2, phase="write")
    adapter = QwenLocalTextExecutionProviderAdapter(root=tmp_path, config_path=CONFIG_PATH, http_call=_transport())
    result = adapter.submit(_request(tmp_path))
    assert result.status == "failed"
    assert not (tmp_path / "docs/operations/examples/qwen-test.md").exists()
    payload = json.loads((tmp_path / result.metadata["provider_receipt"]).read_text())
    assert payload["provider_result_state"] == "failed"
    assert payload["validation_result"] == "failed"
    assert payload["artifacts"] == []


def test_failure_receipt_partial_write_leaves_no_receipt_and_does_not_retry(tmp_path, monkeypatch):
    calls = _inject_partial_fdopen(monkeypatch, failing_call=1, phase="write")
    adapter = QwenLocalTextExecutionProviderAdapter(root=tmp_path, config_path=CONFIG_PATH, http_call=_transport(health=False))
    result = adapter.submit(_request(tmp_path))
    assert result.status == "failed"
    assert result.metadata["provider_receipt"] is None
    assert result.metadata["receipt_reference"] is None
    assert calls["count"] == 1
    assert not list((tmp_path / "runtime/engineering_adapter_receipts").glob("*.json"))
    assert any("failure receipt persistence failed" in error for error in result.errors)


def test_short_failure_receipt_writes_complete_failed_evidence(tmp_path, monkeypatch):
    _inject_partial_fdopen(monkeypatch, failing_call=1, phase="short")
    adapter = QwenLocalTextExecutionProviderAdapter(root=tmp_path, config_path=CONFIG_PATH, http_call=_transport(health=False))
    result = adapter.submit(_request(tmp_path))
    assert result.status == "failed"
    payload = json.loads((tmp_path / result.metadata["provider_receipt"]).read_text())
    assert payload["provider_result_state"] == "failed"
    assert payload["validation_result"] == "failed"


@pytest.mark.parametrize("phase", ["flush", "close"])
def test_flush_and_close_failures_remove_owned_target_and_preserve_primary_error(tmp_path, monkeypatch, phase):
    _inject_partial_fdopen(monkeypatch, failing_call=1, phase=phase)
    target = tmp_path / "owned.json"
    adapter = QwenLocalTextExecutionProviderAdapter(root=tmp_path, config_path=CONFIG_PATH)
    with pytest.raises(OSError, match=f"injected {phase} failure"):
        adapter._exclusive_write_text(target, "content")
    assert not target.exists()


def test_fsync_failure_removes_owned_target_and_preserves_primary_error(tmp_path, monkeypatch):
    def fail_fsync(_descriptor):
        raise OSError("injected fsync failure")

    monkeypatch.setattr(qwen_adapter_module.os, "fsync", fail_fsync)
    target = tmp_path / "owned.json"
    adapter = QwenLocalTextExecutionProviderAdapter(root=tmp_path, config_path=CONFIG_PATH)
    with pytest.raises(OSError, match="injected fsync failure"):
        adapter._exclusive_write_text(target, "content")
    assert not target.exists()


def test_short_document_writes_complete_and_hash_matches_receipt(tmp_path, monkeypatch):
    _inject_partial_fdopen(monkeypatch, failing_call=1, phase="short")
    adapter = QwenLocalTextExecutionProviderAdapter(root=tmp_path, config_path=CONFIG_PATH, http_call=_transport())
    result = adapter.submit(_request(tmp_path))
    assert result.status == "completed"
    document = tmp_path / "docs/operations/examples/qwen-test.md"
    receipt = tmp_path / result.metadata["provider_receipt"]
    payload = json.loads(receipt.read_text())
    assert document.read_text() == "Generated local Qwen text."
    assert payload["artifacts"][0]["sha256"] == hashlib.sha256(document.read_bytes()).hexdigest()


def test_zero_progress_document_write_fails_closed_and_writes_failure_receipt(tmp_path, monkeypatch):
    _inject_partial_fdopen(monkeypatch, failing_call=1, phase="zero_after_partial")
    adapter = QwenLocalTextExecutionProviderAdapter(root=tmp_path, config_path=CONFIG_PATH, http_call=_transport())
    result = adapter.submit(_request(tmp_path))
    assert result.status == "failed"
    assert not (tmp_path / "docs/operations/examples/qwen-test.md").exists()
    assert json.loads((tmp_path / result.metadata["provider_receipt"]).read_text())["artifacts"] == []


def test_short_success_receipt_writes_complete_and_completion_is_reported_after_commit(tmp_path, monkeypatch):
    _inject_partial_fdopen(monkeypatch, failing_call=2, phase="short")
    adapter = QwenLocalTextExecutionProviderAdapter(root=tmp_path, config_path=CONFIG_PATH, http_call=_transport())
    result = adapter.submit(_request(tmp_path))
    assert result.status == "completed"
    assert json.loads((tmp_path / result.metadata["provider_receipt"]).read_text())["provider_result_state"] == "completed"


def test_zero_progress_success_receipt_removes_owned_document_and_writes_one_failure_receipt(tmp_path, monkeypatch):
    _inject_partial_fdopen(monkeypatch, failing_call=2, phase="zero_after_partial")
    adapter = QwenLocalTextExecutionProviderAdapter(root=tmp_path, config_path=CONFIG_PATH, http_call=_transport())
    result = adapter.submit(_request(tmp_path))
    assert result.status == "failed"
    assert not (tmp_path / "docs/operations/examples/qwen-test.md").exists()
    assert json.loads((tmp_path / result.metadata["provider_receipt"]).read_text())["provider_result_state"] == "failed"


def test_receipt_failure_does_not_remove_replacement_document(tmp_path, monkeypatch):
    adapter = QwenLocalTextExecutionProviderAdapter(root=tmp_path, config_path=CONFIG_PATH, http_call=_transport())
    original = adapter._write_receipt
    replaced = {"done": False}

    def fail_after_replacement(request, config, **kwargs):
        if not replaced["done"]:
            replaced["done"] = True
            document = tmp_path / "docs/operations/examples/qwen-test.md"
            document.unlink()
            document.write_bytes(b"replacement document")
            raise OSError("injected success receipt failure")
        return original(request, config, **kwargs)

    monkeypatch.setattr(adapter, "_write_receipt", fail_after_replacement)
    result = adapter.submit(_request(tmp_path))
    document = tmp_path / "docs/operations/examples/qwen-test.md"
    assert result.status == "failed"
    assert document.read_bytes() == b"replacement document"
    assert any("identity changed" in error for error in result.errors)


def test_quarantine_cleanup_rejects_replacement_before_move(tmp_path, monkeypatch):
    adapter = QwenLocalTextExecutionProviderAdapter(root=tmp_path, config_path=CONFIG_PATH)
    token = adapter._exclusive_write_text(tmp_path / "owned.txt", "owned")

    def replace_before_move(_token):
        _token.path.unlink()
        _token.path.write_bytes(b"replacement")

    monkeypatch.setattr(adapter, "_before_quarantine_move", replace_before_move)
    warning = adapter._remove_if_owned(token)
    assert "identity changed" in warning
    assert token.path.read_bytes() == b"replacement"


def test_quarantine_cleanup_preserves_replacement_after_move(tmp_path, monkeypatch):
    adapter = QwenLocalTextExecutionProviderAdapter(root=tmp_path, config_path=CONFIG_PATH)
    token = adapter._exclusive_write_text(tmp_path / "owned.txt", "owned")
    quarantine_paths = []
    original_name = adapter._new_quarantine_path

    def capture_name(path):
        quarantine = original_name(path)
        quarantine_paths.append(quarantine)
        return quarantine

    def replace_after_move(_token, quarantine):
        _token.path.write_bytes(b"replacement")

    monkeypatch.setattr(adapter, "_new_quarantine_path", capture_name)
    monkeypatch.setattr(adapter, "_after_quarantine_move", replace_after_move)
    assert adapter._remove_if_owned(token) is None
    assert token.path.read_bytes() == b"replacement"
    assert quarantine_paths and not quarantine_paths[0].exists()


def test_quarantine_name_collision_fails_without_overwrite(tmp_path, monkeypatch):
    adapter = QwenLocalTextExecutionProviderAdapter(root=tmp_path, config_path=CONFIG_PATH)
    token = adapter._exclusive_write_text(tmp_path / "owned.txt", "owned")
    quarantine = tmp_path / ".owned.txt.qwen-cleanup-fixed"
    quarantine.write_bytes(b"competing quarantine")
    monkeypatch.setattr(adapter, "_new_quarantine_path", lambda _path: quarantine)
    warning = adapter._remove_if_owned(token)
    assert "quarantine path already exists" in warning
    assert token.path.read_text() == "owned"
    assert quarantine.read_bytes() == b"competing quarantine"


def test_quarantine_identity_mismatch_is_not_deleted(tmp_path, monkeypatch):
    adapter = QwenLocalTextExecutionProviderAdapter(root=tmp_path, config_path=CONFIG_PATH)
    token = adapter._exclusive_write_text(tmp_path / "owned.txt", "owned")

    def replace_quarantine(_token, quarantine):
        quarantine.unlink()
        quarantine.write_bytes(b"mismatched quarantine")

    monkeypatch.setattr(adapter, "_after_quarantine_move", replace_quarantine)
    warning = adapter._remove_if_owned(token)
    assert "quarantined file identity changed" in warning
    assert not token.path.exists()
    assert list(tmp_path.glob(".owned.txt.qwen-cleanup-*"))[0].read_bytes() == b"mismatched quarantine"


def test_normal_quarantine_cleanup_removes_owned_file_without_residue(tmp_path):
    adapter = QwenLocalTextExecutionProviderAdapter(root=tmp_path, config_path=CONFIG_PATH)
    token = adapter._exclusive_write_text(tmp_path / "owned.txt", "owned")
    assert adapter._remove_if_owned(token) is None
    assert not token.path.exists()
    assert not list(tmp_path.glob(".owned.txt.qwen-cleanup-*"))
