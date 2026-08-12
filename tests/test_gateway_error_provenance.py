import json
from pathlib import Path

from estate.core.resident_gateway import BOUNDED_ERROR_PATH, record_gateway_exception


def test_file_not_found_is_sanitized_but_provenance_is_recorded(tmp_path):
    try:
        open(tmp_path / "missing-dependency.json", "rb")
    except FileNotFoundError as exc:
        path = record_gateway_exception(exc, payload={"id": "req-1", "model": "estate/grace", "metadata": {"session_id": "sess-1"}}, root=tmp_path)
    assert path == str(tmp_path / BOUNDED_ERROR_PATH)
    record = json.loads(Path(path).read_text(encoding="utf-8").splitlines()[-1])
    assert record["exception_type"] == "FileNotFoundError"
    assert str(tmp_path / "missing-dependency.json") in record["missing_path"]
    assert record["request_id"] == "req-1"
    assert record["session_id"] == "sess-1"
    assert record["origin"]["function"] == "test_file_not_found_is_sanitized_but_provenance_is_recorded"
    assert record["traceback"]


def test_other_exception_is_recorded_without_changing_type(tmp_path):
    try:
        raise ValueError("internal test failure")
    except ValueError as exc:
        record_gateway_exception(exc, payload={"metadata": {"session_id": "sess-2"}}, root=tmp_path)
    record = json.loads((tmp_path / BOUNDED_ERROR_PATH).read_text(encoding="utf-8").splitlines()[-1])
    assert record["exception_type"] == "ValueError"
    assert record["exception_message"] == "internal test failure"


def test_diagnostic_write_failure_is_non_throwing(monkeypatch, tmp_path):
    monkeypatch.setattr(Path, "open", lambda *args, **kwargs: (_ for _ in ()).throw(OSError("diagnostic unavailable")))
    assert record_gateway_exception(FileNotFoundError(2, "missing", "x.json"), payload={}, root=tmp_path) is None
