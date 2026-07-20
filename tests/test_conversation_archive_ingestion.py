import hashlib
import json
from email.message import EmailMessage
from pathlib import Path

import pytest

from estate.core.conversation_archive_ingestion import IngestionError, ingest, validate_bundle


def archive(path: Path) -> bytes:
    message = EmailMessage()
    message["MIME-Version"] = "1.0"
    message["Content-Location"] = "https://chatgpt.example/c/test"
    message.set_content(
        '<div data-message-author-role="user" data-message-id="u1"><p>Hello</p></div>'
        '<div data-message-author-role="assistant" data-message-id="a1"><p>Draft only.</p></div>',
        subtype="html",
    )
    raw = message.as_bytes()
    path.write_bytes(raw)
    return raw


def test_ingestion_is_deterministic_idempotent_and_preserves_source(tmp_path: Path) -> None:
    source = tmp_path / "source.mhtml"
    original = archive(source)
    output = tmp_path / "derived"
    first = ingest(source, output, repository_root=tmp_path)
    snapshot = {p.name: p.read_bytes() for p in first.iterdir()}
    second = ingest(source, output, repository_root=tmp_path)

    assert first == second
    assert snapshot == {p.name: p.read_bytes() for p in second.iterdir()}
    assert source.read_bytes() == original
    manifest = json.loads((first / "manifest.json").read_text())
    assert manifest["source"]["sha256"] == hashlib.sha256(original).hexdigest()
    assert manifest["canonical_status"] == "non_canonical_review_material"
    assert validate_bundle(first, source) == {"valid": True, "run_id": manifest["run_id"], "message_count": 2}
    assert json.loads((first / "derived_review.json").read_text())["institutional_artifact_candidates"] == []


def test_validator_detects_tampering(tmp_path: Path) -> None:
    source = tmp_path / "source.mhtml"
    archive(source)
    bundle = ingest(source, tmp_path / "derived", repository_root=tmp_path)
    records = (bundle / "messages.jsonl").read_text().replace("Hello", "Changed")
    (bundle / "messages.jsonl").write_text(records)
    with pytest.raises(IngestionError, match="integrity"):
        validate_bundle(bundle, source)


def test_rejects_non_conversation_html(tmp_path: Path) -> None:
    source = tmp_path / "empty.mhtml"
    message = EmailMessage()
    message.set_content("<p>Not a chat</p>", subtype="html")
    source.write_bytes(message.as_bytes())
    with pytest.raises(IngestionError, match="no data-message"):
        ingest(source, tmp_path / "derived")


FIXTURES = Path(__file__).parent / "fixtures" / "conversation_archives"


def raw_mhtml(payload: bytes, charset: str | None, *, malformed_header: bool = False) -> bytes:
    content_type = b"Content-Type: text/html" + (b"; charset=" + charset.encode("ascii") if charset else b"")
    location = b"Content-Location: =?utf-8?Q?https=3A//example.test/caf=C3=A9?="
    if malformed_header:
        location = b"Content-Location: bad-\xff-location"
    return b"MIME-Version: 1.0\r\n" + location + b"\r\n" + content_type + b"\r\nContent-Disposition: inline; filename=\"=?utf-8?Q?caf=C3=A9.html?=\"\r\nContent-Transfer-Encoding: 8bit\r\n\r\n" + payload


def conversation(text: str, encoding: str = "utf-8") -> bytes:
    html = f'<div data-message-author-role="user" data-message-id="u1"><p>{text}</p></div>'
    return html.encode(encoding)


@pytest.mark.parametrize(("declared", "payload", "used", "fallback"), [
    ("utf-8", conversation("snowman ☃"), "utf-8", False),
    ("windows-1252", conversation("€ quote “ok”", "cp1252"), "cp1252", False),
    (None, conversation("plain utf8 ☃"), "utf-8", False),
    ("us-ascii", conversation("actually utf8 ☃"), "utf-8", True),
    ("not-a-codec", conversation("invalid declaration ☃"), "utf-8", True),
    (None, conversation("€ cp payload", "cp1252"), "windows-1252", True),
])
def test_mhtml_charset_selection(tmp_path: Path, declared, payload, used, fallback) -> None:
    source = tmp_path / "charset.mhtml"
    source.write_bytes(raw_mhtml(payload, declared))
    bundle = ingest(source, tmp_path / "out")
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    evidence = manifest["extraction"]["decoding"]
    assert evidence["declared_charset"] == declared
    assert evidence["charset_used"] == used
    assert evidence["fallback_occurred"] is fallback
    assert evidence["replacement_character_count"] == 0


def test_reported_0x9d_fixture_uses_final_replacement_without_rewriting(tmp_path: Path) -> None:
    source = FIXTURES / "edge_cp1252_undefined_0x9d.mhtml"
    original = source.read_bytes()
    bundle = ingest(source, tmp_path / "out")
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    evidence = manifest["extraction"]["decoding"]
    assert evidence["charset_used"] == "windows-1252"
    assert evidence["fallback_occurred"] is True
    assert evidence["replacement_character_count"] == 1
    assert evidence["diagnostics"]
    assert source.read_bytes() == original
    assert manifest["source"]["sha256"] == hashlib.sha256(original).hexdigest()


def test_malformed_mime_header_is_preserved_safely(tmp_path: Path) -> None:
    source = tmp_path / "malformed.mhtml"
    source.write_bytes(raw_mhtml(conversation("safe"), "utf-8", malformed_header=True))
    manifest = json.loads((ingest(source, tmp_path / "out") / "manifest.json").read_text(encoding="utf-8"))
    assert isinstance(manifest["source"]["content_location"], str)
    assert manifest["extraction"]["decoding"]["mime_filename"] == "café.html"


def test_ingestion_code_has_no_platform_default_text_io() -> None:
    sources = [Path("src/estate/core/conversation_archive_ingestion.py"), Path("src/estate/core/runtime_canon_recovery.py")]
    for source in sources:
        text = source.read_text(encoding="utf-8")
        assert not __import__("re").search(r"\.read_text\(\)", text)
        assert not __import__("re").search(r"open\([^\n]*,[ ]*[\"'](?:r|w|a|x)t?[\"'](?![^\n]*encoding=)", text)


def test_existing_html_and_plain_text_contracts(tmp_path: Path) -> None:
    html = tmp_path / "chat.html"
    html.write_bytes(conversation("HTML unchanged"))
    plain = tmp_path / "chat.txt"
    plain.write_bytes(b"User: Plain unchanged\nAssistant: Still unchanged\n")
    html_records = (ingest(html, tmp_path / "out") / "messages.jsonl").read_text(encoding="utf-8")
    plain_records = (ingest(plain, tmp_path / "out") / "messages.jsonl").read_text(encoding="utf-8")
    assert "HTML unchanged" in html_records
    assert "Plain unchanged" in plain_records
