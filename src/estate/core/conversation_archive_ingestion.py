"""Deterministic, provenance-preserving ingestion of conversation MHTML archives.

The archive is evidence.  This module only reads it and writes a derived run bundle;
it never promotes conversation statements into Estate institutional truth.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from dataclasses import asdict, dataclass
from email import policy
from email.parser import BytesParser
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable

SCHEMA_VERSION = "estate.conversation-ingestion/v1"
ALLOWED_ROLES = {"user", "assistant", "system", "tool"}


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


class _MessageHTMLParser(HTMLParser):
    """Capture text contained by ChatGPT message-role elements using stdlib only."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.capture_div_depth = 0
        self.role = ""
        self.message_id = ""
        self.parts: list[str] = []
        self.messages: list[tuple[str, str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if not self.capture_div_depth and values.get("data-message-author-role"):
            self.capture_div_depth = 1
            self.role = values["data-message-author-role"] or ""
            self.message_id = values.get("data-message-id") or ""
            self.parts = []
        elif self.capture_div_depth and tag == "div":
            self.capture_div_depth += 1
        if self.capture_div_depth and tag in {"br", "p", "li", "pre", "h1", "h2", "h3"}:
            self.parts.append("\n")

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_data(self, data: str) -> None:
        if self.capture_div_depth:
            self.parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if self.capture_div_depth and tag == "div":
            self.capture_div_depth -= 1
            if not self.capture_div_depth:
                self.messages.append((self.role, self.message_id, _normalize("".join(self.parts))))


@dataclass(frozen=True)
class Message:
    sequence: int
    source_message_id: str
    role: str
    text: str
    text_sha256: str
    provenance: dict[str, object]


class IngestionError(ValueError):
    pass


def extract_messages(archive: Path, source_sha256: str) -> tuple[list[Message], str]:
    with archive.open("rb") as stream:
        mime = BytesParser(policy=policy.default).parse(stream)
    html_parts = [part for part in mime.walk() if part.get_content_type() == "text/html"]
    if not html_parts:
        raise IngestionError("archive contains no text/html MIME part")
    primary = max(html_parts, key=lambda part: len(part.get_payload(decode=True) or b""))
    payload = primary.get_payload(decode=True) or b""
    charset = primary.get_content_charset() or "utf-8"
    parser = _MessageHTMLParser()
    parser.feed(payload.decode(charset, errors="replace"))
    if not parser.messages:
        raise IngestionError("HTML contains no data-message-author-role elements")
    location = primary.get("Content-Location", "")
    messages = []
    for sequence, (role, source_id, text) in enumerate(parser.messages, 1):
        if role not in ALLOWED_ROLES:
            raise IngestionError(f"unsupported message role: {role!r}")
        messages.append(Message(
            sequence=sequence,
            source_message_id=source_id,
            role=role,
            text=text,
            text_sha256=_sha256(text.encode()),
            provenance={
                "archive_sha256": source_sha256,
                "mime_content_location": location,
                "selector": f'[data-message-id="{source_id}"]' if source_id else None,
            },
        ))
    return messages, location


def _write_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def ingest(archive: Path, output_root: Path, *, repository_root: Path | None = None) -> Path:
    archive = archive.resolve()
    source_bytes = archive.read_bytes()
    source_hash = _sha256(source_bytes)
    messages, location = extract_messages(archive, source_hash)
    run_id = source_hash[:16]
    run_dir = output_root / archive.stem / run_id
    try:
        source_path = str(archive.relative_to((repository_root or Path.cwd()).resolve()))
    except ValueError:
        source_path = str(archive)

    records = "".join(json.dumps(asdict(item), ensure_ascii=False, sort_keys=True) + "\n" for item in messages)
    transcript = ["# Verbatim Conversation Extraction", "", "> Derived extraction; not accepted Estate canon.", ""]
    for item in messages:
        transcript += [f"## {item.sequence}. {item.role}", "", item.text, "", f"Source message: `{item.source_message_id or 'unavailable'}`", ""]
    derived = {
        "schema_version": SCHEMA_VERSION,
        "status": "review_required",
        "notice": "No interpretation or institutional artifact is generated or accepted automatically.",
        "interpretations": [],
        "institutional_artifact_candidates": [],
    }
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "source": {"path": source_path, "sha256": source_hash, "bytes": len(source_bytes), "media_type": "multipart/related", "content_location": location},
        "extraction": {"message_count": len(messages), "roles": {r: sum(m.role == r for m in messages) for r in sorted({m.role for m in messages})}},
        "classification": "Estate Internal",
        "canonical_status": "non_canonical_review_material",
        "artifacts": ["manifest.json", "messages.jsonl", "verbatim_transcript.md", "derived_review.json"],
    }
    _write_atomic(run_dir / "messages.jsonl", records)
    _write_atomic(run_dir / "verbatim_transcript.md", "\n".join(transcript))
    _write_atomic(run_dir / "derived_review.json", json.dumps(derived, indent=2, sort_keys=True) + "\n")
    _write_atomic(run_dir / "manifest.json", json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    validate_bundle(run_dir, archive)
    return run_dir


def validate_bundle(run_dir: Path, archive: Path | None = None) -> dict[str, object]:
    manifest = json.loads((run_dir / "manifest.json").read_text())
    required = {"schema_version", "run_id", "source", "extraction", "canonical_status", "artifacts"}
    if not required.issubset(manifest) or manifest["schema_version"] != SCHEMA_VERSION:
        raise IngestionError("invalid manifest contract")
    lines = (run_dir / "messages.jsonl").read_text().splitlines()
    records = [json.loads(line) for line in lines]
    if len(records) != manifest["extraction"]["message_count"]:
        raise IngestionError("message count mismatch")
    if [r["sequence"] for r in records] != list(range(1, len(records) + 1)):
        raise IngestionError("message sequence is not contiguous")
    for record in records:
        if record["role"] not in ALLOWED_ROLES or _sha256(record["text"].encode()) != record["text_sha256"]:
            raise IngestionError("message integrity validation failed")
    if archive is not None and _sha256(archive.read_bytes()) != manifest["source"]["sha256"]:
        raise IngestionError("source archive hash mismatch")
    return {"valid": True, "run_id": manifest["run_id"], "message_count": len(records)}


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--output-root", type=Path, default=Path("ingestion/conversations/derived"))
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    run_dir = ingest(args.archive, args.output_root, repository_root=args.repository_root)
    result = validate_bundle(run_dir, args.archive.resolve())
    print(json.dumps({**result, "output": str(run_dir)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
