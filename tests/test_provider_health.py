import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from estate.core.provider_health import ProviderHealthRecord, generate_provider_health_summary, write_health_record
from estate.core.provider_capacity import ProviderCapacityRecord, write_capacity_record


def copy_catalog(root):
    target = root / "config" / "providers"
    target.mkdir(parents=True)
    shutil.copy(Path("config/providers/catalog.json"), target / "catalog.json")


def test_valid_health_record_accepted():
    rec = ProviderHealthRecord.create(provider_id="codex.execution.cli", status="available", reported_by="Steward", message="ok")
    assert rec.to_dict()["status"] == "available"


def test_invalid_health_status_rejected():
    rec = ProviderHealthRecord.create(provider_id="codex.execution.cli", status="bad", reported_by="Steward", message="ok")
    with pytest.raises(ValueError):
        rec.validate()


def test_unknown_classification_rejected():
    rec = ProviderHealthRecord.create(provider_id="codex.execution.cli", status="available", reported_by="Steward", message="ok", classification="Secret")
    with pytest.raises(ValueError):
        rec.validate()


def test_health_record_artifact_written(tmp_path):
    copy_catalog(tmp_path)
    rec = ProviderHealthRecord.create(provider_id="codex.execution.cli", status="available", reported_by="Steward", message="ok")
    paths = write_health_record(rec, root=tmp_path)
    assert paths["record"].exists()
    assert (tmp_path / "runtime/providers/health/status/latest.json").exists()


def test_summary_artifact_generated_and_redacts_sensitive_by_default(tmp_path):
    copy_catalog(tmp_path)
    write_health_record(ProviderHealthRecord.create(provider_id="codex.execution.cli", status="blocked", reported_by="Steward", message="private account detail", classification="Restricted"), root=tmp_path)
    write_capacity_record(ProviderCapacityRecord.create(provider_id="codex.execution.cli", capacity_state="busy", reported_by="Steward", active_jobs=1, max_jobs=2), root=tmp_path)
    summary = generate_provider_health_summary(root=tmp_path, write=True)
    provider = next(p for p in summary["providers"] if p["provider_id"] == "codex.execution.cli")
    assert provider["safe_message"] == "Sensitive provider health message redacted."
    assert provider["display_name"]
    assert (tmp_path / "runtime/providers/health/status/summary.json").exists()
    assert (tmp_path / "runtime/providers/health/status/summary.md").exists()


def test_summary_safe_messages_displayed(tmp_path):
    copy_catalog(tmp_path)
    write_health_record(ProviderHealthRecord.create(provider_id="codex.execution.cli", status="degraded", reported_by="Steward", message="safe degraded", classification="Restricted", metadata={"summary_safe": True}), root=tmp_path)
    provider = next(p for p in generate_provider_health_summary(root=tmp_path)["providers"] if p["provider_id"] == "codex.execution.cli")
    assert provider["safe_message"] == "safe degraded"


def test_cli_health_set_succeeds(tmp_path):
    copy_catalog(tmp_path)
    result = subprocess.run([sys.executable, "-m", "estate.cli.main", "providers-health-set", "--provider-id", "codex.execution.cli", "--status", "available", "--reported-by", "Steward", "--message", "ok"], cwd=tmp_path, text=True, capture_output=True, env={"PYTHONPATH": str(Path.cwd() / "src")})
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Provider health recorded" in result.stdout


def test_cli_summary_succeeds_with_no_records(tmp_path):
    copy_catalog(tmp_path)
    result = subprocess.run([sys.executable, "-m", "estate.cli.main", "providers-health-summary"], cwd=tmp_path, text=True, capture_output=True, env={"PYTHONPATH": str(Path.cwd() / "src")})
    assert result.returncode == 0
    assert "Provider Health Summary" in result.stdout


def test_cli_summary_reports_available_degraded_blocked_providers(tmp_path):
    copy_catalog(tmp_path)
    env={"PYTHONPATH": str(Path.cwd() / "src")}
    for pid, status in [("codex.execution.cli", "available"), ("chatgpt.planning.external", "degraded"), ("estate.audit.local", "blocked")]:
        result = subprocess.run([sys.executable, "-m", "estate.cli.main", "providers-health-set", "--provider-id", pid, "--status", status, "--reported-by", "Steward", "--message", status, "--force"], cwd=tmp_path, text=True, capture_output=True, env=env)
        assert result.returncode == 0, result.stdout + result.stderr
    result = subprocess.run([sys.executable, "-m", "estate.cli.main", "providers-health-summary"], cwd=tmp_path, text=True, capture_output=True, env=env)
    assert "available" in result.stdout and "degraded" in result.stdout and "blocked" in result.stdout
