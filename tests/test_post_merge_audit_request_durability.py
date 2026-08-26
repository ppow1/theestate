import hashlib
import json

import pytest

from estate.core.post_merge_audit_processor import PostMergeAuditProcessor
from estate.core.post_merge_audit_runtime import PostMergeAuditRuntime
from estate.core.runtime_recovery import _atomic_write_json


def _request(root, name="pma-valid.json", payload=None):
    path = root / "runtime/post_merge_audit/requests" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload or {"audit_id": name[:-5], "state": "pending"}), encoding="utf-8")
    return path


def test_valid_request_is_written_as_complete_json_without_temp_artifact(tmp_path):
    request = PostMergeAuditRuntime(tmp_path).create_request("estate-main", "WP-0618", expected_files=[])
    path = tmp_path / "runtime/post_merge_audit/requests" / f"{request.audit_id}.json"
    assert json.loads(path.read_text(encoding="utf-8"))["audit_id"] == request.audit_id
    assert not list(path.parent.glob(f".{path.name}.*"))


def test_interrupted_replace_keeps_previous_complete_json(tmp_path, monkeypatch):
    path = tmp_path / "runtime/post_merge_audit/requests/pma.json"
    _atomic_write_json(path, {"version": 1})
    import estate.core.runtime_recovery as recovery
    monkeypatch.setattr(recovery.os, "replace", lambda *_: (_ for _ in ()).throw(OSError("interrupted")))
    with pytest.raises(OSError):
        _atomic_write_json(path, {"version": 2})
    assert json.loads(path.read_text(encoding="utf-8")) == {"version": 1}
    assert not list(path.parent.glob(f".{path.name}.*"))


def test_malformed_request_is_quarantined_and_siblings_remain_discoverable(tmp_path):
    bad = _request(tmp_path, "pma-bad.json")
    bad.write_bytes(b"\x00" * 454)
    good = _request(tmp_path, "pma-good.json", {"audit_id": "good", "state": "pending"})
    processor = PostMergeAuditProcessor(tmp_path)
    found = processor.list_requests()
    assert [row["audit_id"] for row in found] == ["good"]
    assert not bad.exists()
    quarantined = tmp_path / "runtime/post_merge_audit/quarantine/pma-bad.json"
    receipt = tmp_path / "runtime/post_merge_audit/recovery/pma-bad.json"
    assert quarantined.read_bytes() == b"\x00" * 454
    evidence = json.loads(receipt.read_text(encoding="utf-8"))
    assert evidence["corruption_type"] == "nul_filled"
    assert evidence["original_byte_count"] == 454
    assert evidence["original_sha256"] == hashlib.sha256(b"\x00" * 454).hexdigest()
    assert evidence["executable_request_discovery"] == "excluded"
    assert good.exists()


def test_corrupt_request_is_not_reported_as_valid_or_pending(tmp_path):
    _request(tmp_path, "pma-bad.json").write_text("{not-json", encoding="utf-8")
    processor = PostMergeAuditProcessor(tmp_path)
    assert processor.list_requests("pending") == []
    assert processor.summary()["quarantined_corrupt_request_count"] == 1


def test_unknown_filesystem_error_fails_closed(tmp_path, monkeypatch):
    _request(tmp_path, "pma-bad.json").write_text("{not-json", encoding="utf-8")
    processor = PostMergeAuditProcessor(tmp_path)
    monkeypatch.setattr(processor, "quarantine_request", lambda *args, **kwargs: (_ for _ in ()).throw(OSError("disk unavailable")))
    with pytest.raises(OSError, match="disk unavailable"):
        processor.list_requests()
