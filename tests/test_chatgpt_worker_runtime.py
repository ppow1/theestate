import os
import sys
from pathlib import Path

from estate.core.chatgpt_worker_runtime import validate_worker_runtime


def test_wrong_interpreter_fails_closed_without_secret_value(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    result = validate_worker_runtime(app_root=tmp_path, data_dir=tmp_path / "data", python_executable=tmp_path / "canonical-python.exe")
    assert not result["ok"]
    assert "wrong_python_interpreter" in result["errors"]
    assert "governed_secret_source_unavailable" in result["errors"]
    assert "WEBUI_SECRET_KEY" in result["checks"]["secret"]["variable"]
    assert "value" not in str(result)


def test_missing_canonical_database_fails_closed(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    (tmp_path / ".webui_secret_key").write_text("test-only", encoding="utf-8")
    result = validate_worker_runtime(app_root=tmp_path, data_dir=tmp_path, python_executable=sys.executable)
    assert not result["ok"]
    assert "canonical_data_dir_unavailable" in result["errors"]
    assert result["checks"]["secret"]["source"] == "canonical_key_file"


def test_secret_presence_is_reported_by_source_only(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "EstateCanonicalData").mkdir()
    (tmp_path / "EstateCanonicalData" / "webui.db").write_bytes(b"sqlite")
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "EstateCanonicalData"))
    monkeypatch.setenv("WEBUI_SECRET_KEY", "test-secret-that-must-not-be-returned")
    result = validate_worker_runtime(app_root=tmp_path, data_dir=tmp_path / "EstateCanonicalData", python_executable=sys.executable)
    assert result["checks"]["secret"]["source"] == "environment"
    assert "test-secret" not in str(result)
