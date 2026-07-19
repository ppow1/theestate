import json
from email.message import EmailMessage
from pathlib import Path

import pytest

from estate.core.conversation_archive_ingestion import ingest
from estate.core.conversation_specification_extraction import (
    SpecificationError,
    extract_specifications,
    parse_expected,
    validate_extraction,
)


def make_archive(path: Path, messages: list[tuple[str, str, str]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    mime = EmailMessage()
    mime["MIME-Version"] = "1.0"
    html = "".join(f'<div data-message-author-role="{role}" data-message-id="{identifier}">{body}</div>' for role, identifier, body in messages)
    mime.set_content(html, subtype="html")
    mime["Content-Location"] = "https://chatgpt.example/c/multi-wp"
    path.write_bytes(mime.as_bytes())
    return path


def run(tmp_path: Path, messages: list[tuple[str, str, str]], expected: list[str]):
    bundle = ingest(make_archive(tmp_path / "chat.mhtml", messages), tmp_path / "ingested", repository_root=tmp_path)
    output = extract_specifications(bundle, expected, tmp_path / "staged", repository_root=tmp_path)
    return output, json.loads((output / "validation_report.json").read_text())


def canon(wp: str, title: str, extra: str = "") -> str:
    return f"<h2>{wp} — {title}</h2><p>Runtime canon paragraph.</p><ul><li>Rule one</li><li>Rule two</li></ul><pre>command --check\n  --strict</pre>{extra}"


def test_multi_wp_coverage_format_provenance_and_classification(tmp_path: Path) -> None:
    output, report = run(tmp_path, [
        ("user", "seed", "Continuation startup seed"), ("user", "go", "go"),
        ("assistant", "a1", canon("WP-4107", "Alpha") + canon("WP-4108", "Beta")),
        ("assistant", "done", "Handoff complete and ready for review."),
    ], ["WP-4107", "WP-4108"])
    assert report["status"] == "valid"
    assert report["found"] == ["WP-4107", "WP-4108"] and not report["missing"]
    candidate = report["candidates"][0]
    assert candidate["provenance"] == {
        "conversation_location": "https://chatgpt.example/c/multi-wp", "extraction_run": report["run_id"],
        "source_archive_sha256": report["source"]["archive_sha256"], "source_message_id": "a1",
        "source_sequence": 3, "wp_identifier": "WP-4107",
    }
    text = (output / candidate["staging_artifact"]).read_text()
    assert "## WP-4107" in text and "- Rule one" in text and "```" in text and "  --strict" in text
    assert [item["classification"] for item in report["message_classifications"]] == [
        "continuation_startup_seed", "automatic_go", "assistant_runtime_canon", "completion_handoff"]
    assert validate_extraction(output)["valid"] is True


@pytest.mark.parametrize("value,count", [("WP-4107 through WP-4116", 10), ("WP-4117..WP-4126", 10), ("WP-4127:WP-4130", 4)])
def test_bounded_expected_ranges(value: str, count: int) -> None:
    assert len(parse_expected(value)) == count


def test_reports_missing_and_duplicate_without_silent_omission(tmp_path: Path) -> None:
    _, report = run(tmp_path, [("assistant", "a1", canon("WP-4107", "One")), ("assistant", "a2", canon("WP-4107", "Again"))], ["WP-4107", "WP-4108"])
    assert report["missing"] == ["WP-4108"] and report["duplicates"] == ["WP-4107"]
    assert {d["code"] for d in report["diagnostics"]} >= {"missing_expected_wp", "duplicate_wp_output"}


def test_malformed_heading_and_collapsed_formatting_are_diagnostics(tmp_path: Path) -> None:
    _, malformed = run(tmp_path, [("assistant", "a", "<h2>WP-123 — Bad</h2><p>text</p>")], ["WP-4107"])
    assert "malformed_wp_heading" in {d["code"] for d in malformed["diagnostics"]}
    _, collapsed = run(tmp_path / "second", [("assistant", "a", "## WP-4107 — Flat\nall structure was flattened")], ["WP-4107"])
    assert "WP-4107" in collapsed["ambiguous"]
    assert "collapsed_formatting" in collapsed["candidates"][0]["diagnostics"]


def test_ambiguous_destination_and_pending_overwrite_are_blocked(tmp_path: Path) -> None:
    pending = tmp_path / "collaboration/work_packages/pending"
    pending.mkdir(parents=True)
    (pending / "WP-4107_A.md").write_text("a")
    (pending / "WP-4107_B.md").write_text("b")
    _, ambiguous = run(tmp_path, [("assistant", "a", canon("WP-4107", "Title"))], ["WP-4107"])
    assert "ambiguous_destination" in ambiguous["candidates"][0]["diagnostics"]
    _, overwrite = run(tmp_path / "overwrite", [("assistant", "a", canon("WP-4107", "Title", "<p>Destination: collaboration/work_packages/pending/WP-4107_Title.md</p>"))], ["WP-4107"])
    assert "pending_definition_overwrite" in overwrite["candidates"][0]["diagnostics"]
    assert overwrite["candidates"][0]["proposed_destination"] is None


def test_truncated_response_and_candidate_tampering(tmp_path: Path) -> None:
    _, report = run(tmp_path, [("assistant", "a", "<h2>WP-4107 — Cut off</h2><pre>unterminated")], ["WP-4107"])
    assert "truncated_assistant_response" in report["candidates"][0]["diagnostics"]
    output, clean = run(tmp_path / "clean", [("assistant", "a", canon("WP-4107", "Good"))], ["WP-4107"])
    (output / clean["candidates"][0]["staging_artifact"]).write_text("tampered")
    with pytest.raises(SpecificationError, match="integrity"):
        validate_extraction(output)


def test_real_archive_fixture_is_ingested_and_every_expected_wp_reported(tmp_path: Path) -> None:
    source = Path("ingestion/conversations/Chief_Architect_Renewal_Verification_2026-07-19.mhtml")
    if not source.exists():
        pytest.skip("real archived conversation is not present")
    bundle = ingest(source, tmp_path / "ingested", repository_root=Path.cwd())
    output = extract_specifications(bundle, ["WP-4209"], tmp_path / "staged", repository_root=Path.cwd())
    report = json.loads((output / "validation_report.json").read_text())
    assert report["found"] + report["missing"] == ["WP-4209"]
