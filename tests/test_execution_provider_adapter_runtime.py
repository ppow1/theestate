import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import json
from pathlib import Path

from estate.core.execution_provider_adapter import ExecutionProviderAdapterRequest
from estate.core.execution_provider_adapter_runtime import (
    LATEST_STATUS,
    SUMMARY_STATUS,
    load_adapter_request,
    run_dry_run_adapter,
    validate_adapter_request_file,
    write_adapter_request,
)


def request():
    return ExecutionProviderAdapterRequest.from_dict({
        "adapter_request_id": "adapter-runtime-001",
        "dispatch_id": "dispatch-runtime-001",
        "provider_id": "dry-run-provider",
        "provider_type": "dry-run",
        "classification": "Estate Internal",
        "prompt_source": "collaboration/work_packages/pending/WP-0613_Execution_Provider_Adapter_Contract.md",
        "created_at": "2026-07-09T00:00:00Z",
    })


def test_request_artifact_written_and_loaded(tmp_path):
    path = write_adapter_request(request(), root=tmp_path)
    assert path.is_file()
    loaded = load_adapter_request(path)
    assert loaded.adapter_request_id == "adapter-runtime-001"


def test_dry_run_result_artifact_written(tmp_path):
    payload = run_dry_run_adapter(request(), root=tmp_path)
    result_path = Path(payload["result_path"])
    assert result_path.is_file()
    data = json.loads(result_path.read_text(encoding="utf-8"))
    assert data["status"] == "dry_run_completed"
    assert data["metadata"]["live_provider_called"] is False


def test_latest_status_artifact_written(tmp_path):
    payload = run_dry_run_adapter(request(), root=tmp_path)
    assert Path(payload["latest_status_path"]).is_file()
    assert (tmp_path / LATEST_STATUS).is_file()
    latest = json.loads((tmp_path / LATEST_STATUS).read_text(encoding="utf-8"))
    summary = json.loads((tmp_path / SUMMARY_STATUS).read_text(encoding="utf-8"))
    assert latest["adapter_request_id"] == "adapter-runtime-001"
    assert summary["live_provider_called"] is False


def test_validate_request_file(tmp_path):
    path = write_adapter_request(request(), root=tmp_path)
    payload = validate_adapter_request_file(path)
    assert payload["validation"]["status"] == "accepted"
