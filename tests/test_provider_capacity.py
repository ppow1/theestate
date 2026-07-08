import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from estate.core.provider_capacity import ProviderCapacityRecord, write_capacity_record


def copy_catalog(root):
    target = root / "config" / "providers"
    target.mkdir(parents=True)
    shutil.copy(Path("config/providers/catalog.json"), target / "catalog.json")


def test_valid_capacity_record_accepted():
    rec = ProviderCapacityRecord.create(provider_id="codex.execution.cli", capacity_state="busy", reported_by="Steward", active_jobs=1)
    assert rec.to_dict()["capacity_state"] == "busy"


def test_invalid_capacity_state_rejected():
    rec = ProviderCapacityRecord.create(provider_id="codex.execution.cli", capacity_state="overloaded", reported_by="Steward")
    with pytest.raises(ValueError):
        rec.validate()


def test_capacity_record_artifact_written(tmp_path):
    copy_catalog(tmp_path)
    rec = ProviderCapacityRecord.create(provider_id="codex.execution.cli", capacity_state="busy", reported_by="Steward", active_jobs=1)
    paths = write_capacity_record(rec, root=tmp_path)
    assert paths["record"].exists()
    assert (tmp_path / "runtime/providers/health/status/latest_capacity.json").exists()


def test_catalog_enrichment_works_when_catalog_exists(tmp_path):
    copy_catalog(tmp_path)
    write_capacity_record(ProviderCapacityRecord.create(provider_id="codex.execution.cli", capacity_state="busy", reported_by="Steward", active_jobs=1), root=tmp_path)
    from estate.core.provider_health import generate_provider_health_summary
    provider = next(p for p in generate_provider_health_summary(root=tmp_path)["providers"] if p["provider_id"] == "codex.execution.cli")
    assert provider["display_name"]
    assert provider["provider_type"] == "execution"


def test_cli_capacity_set_succeeds(tmp_path):
    copy_catalog(tmp_path)
    result = subprocess.run([sys.executable, "-m", "estate.cli.main", "providers-capacity-set", "--provider-id", "codex.execution.cli", "--capacity-state", "busy", "--active-jobs", "1", "--reported-by", "Steward"], cwd=tmp_path, text=True, capture_output=True, env={"PYTHONPATH": str(Path.cwd() / "src")})
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Provider capacity recorded" in result.stdout
