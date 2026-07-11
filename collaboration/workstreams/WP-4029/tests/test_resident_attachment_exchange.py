import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
MODULE_PATH = ROOT / "src" / "resident_attachment_exchange.py"
spec = importlib.util.spec_from_file_location("resident_attachment_exchange", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

AttachmentPolicy = mod.AttachmentPolicy
AttachmentRejected = mod.AttachmentRejected
AttachmentSource = mod.AttachmentSource
ResidentAttachmentExchange = mod.ResidentAttachmentExchange


def exchange():
    return ResidentAttachmentExchange(now=lambda: "2026-07-11T00:00:00+00:00")


def source():
    return AttachmentSource(
        owner_id="estate",
        resident_id="alfred",
        source_kind="mail",
        source_id="inbox-1",
        message_id="msg-1",
        task_id="task-9",
        session_id="sess-3",
        conversation_id="conv-7",
    )


def test_intake_links_checksum_classification_and_deterministic_storage_path():
    runtime = exchange()
    record = runtime.intake(name="Report Final.pdf", content=b"%PDF sample", source=source(), classification="confidential", media_type="application/pdf")
    assert record.checksum == "e56409c1e521e2020467138b3e3a04522520f888d0f14d6272db9dcbcfccd302"
    assert record.storage_path == "resident_attachments/estate/alfred/mail/inbox-1/e5/att_e56409c1e521e202.pdf"
    assert record.message_id == "msg-1"
    assert record.task_id == "task-9"
    assert record.session_id == "sess-3"
    assert runtime.audit_events[-1]["event"] == "attachment_intake"


def test_duplicate_detection_keeps_source_links_distinct():
    runtime = exchange()
    first = runtime.intake(name="note.txt", content=b"same", source=source(), classification="internal", media_type="text/plain")
    second_source = AttachmentSource(owner_id="estate", resident_id="grace", source_kind="conversation", source_id="conv-2", conversation_id="conv-2")
    duplicate = runtime.intake(name="copy.txt", content=b"same", source=second_source, classification="internal", media_type="text/plain")
    assert duplicate.duplicate_of == first.attachment_id
    assert duplicate.resident_id == "grace"
    assert duplicate.conversation_id == "conv-2"


def test_dangerous_unsupported_mismatched_and_oversized_inputs_fail_safely():
    runtime = ResidentAttachmentExchange(policy=AttachmentPolicy(max_bytes=4), now=lambda: "2026-07-11T00:00:00+00:00")
    for name, body, media_type in [
        ("run.sh", b"echo no", None),
        ("archive.zip", b"zip", None),
        ("image.png", b"png", "application/pdf"),
        ("large.txt", b"12345", "text/plain"),
    ]:
        try:
            runtime.intake(name=name, content=body, source=source(), classification="internal", media_type=media_type)
        except AttachmentRejected:
            pass
        else:
            raise AssertionError(f"{name} should have been rejected")


def test_summaries_are_distinct_working_artifacts_not_source_content():
    runtime = exchange()
    record = runtime.intake(name="photo.png", content=b"png bytes", source=source(), classification="internal", media_type="image/png")
    summary = runtime.add_summary(record.attachment_id, adapter="image_summary", text="A safe deterministic image summary.")
    payload = runtime.read(record.attachment_id, actor_id="tester", purpose="review")
    assert summary.is_source_content is False
    assert payload["source_content_included"] is False
    assert payload["summaries"][0]["source_checksum"] == record.checksum


def test_sensitive_reads_downloads_exports_and_retention_are_audited_and_controlled():
    runtime = exchange()
    record = runtime.intake(name="private.md", content=b"secret", source=source(), classification="restricted", media_type="text/markdown")
    try:
        runtime.read(record.attachment_id, actor_id="tester", purpose="no grant")
    except AttachmentRejected as exc:
        assert "explicit authorization" in str(exc)
    else:
        raise AssertionError("restricted read should require authorization")
    downloaded = runtime.download(record.attachment_id, actor_id="tester", purpose="approved", include_sensitive=True)
    exported = runtime.export_manifest([record.attachment_id], actor_id="tester", purpose="approved", include_sensitive=True)
    runtime.archive(record.attachment_id, actor_id="tester", reason="case closed")
    assert downloaded["download_allowed"] is True
    assert exported["content_included"] is False
    assert record.retention_state == "archived"
    assert [event["event"] for event in runtime.audit_events][-4:] == ["attachment_download", "attachment_read", "attachment_export", "attachment_retention_changed"]


def test_office_and_open_webui_payloads_do_not_expose_source_content():
    runtime = exchange()
    record = runtime.intake(name="brief.csv", content=b"a,b\n1,2", source=source(), classification="internal", media_type="text/csv")
    payload = runtime.office_payload(record.attachment_id)
    assert payload["kind"] == "office_attachment_card"
    assert payload["open_webui_compatible"] is True
    assert payload["source_content_included"] is False
    assert payload["attachment"]["links"]["message_id"] == "msg-1"
