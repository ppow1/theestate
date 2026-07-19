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
