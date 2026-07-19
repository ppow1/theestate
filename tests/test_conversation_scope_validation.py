import json
from pathlib import Path

from estate.core.conversation_archive_ingestion import ingest, validate_bundle
from estate.core.conversation_scope_validation import validate_scope


FIXTURES = Path(__file__).parent / "fixtures" / "conversations"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def run_fixture(tmp_path, name):
    source = FIXTURES / name
    bundle = ingest(source, tmp_path / "ingestion", repository_root=Path.cwd())
    assert validate_bundle(bundle, source)["valid"]
    output = validate_scope(bundle, tmp_path / "review")
    return bundle, output


def test_plain_text_intake_preserves_roles_lines_and_hashes(tmp_path):
    bundle, _ = run_fixture(tmp_path, "wp_4107_4116_wrong_canons.txt")
    manifest = load(bundle / "manifest.json")
    messages = [json.loads(line) for line in (bundle / "messages.jsonl").read_text().splitlines()]
    assert manifest["source"]["media_type"] == "text/plain"
    assert [m["role"] for m in messages] == ["user", "assistant", "user", "assistant"]
    assert messages[0]["provenance"]["line_start"] == 1
    assert all(m["provenance"]["archive_sha256"] == manifest["source"]["sha256"] for m in messages)


def test_wrong_runtime_canons_are_out_of_scope_and_missing_assignment(tmp_path):
    _, output = run_fixture(tmp_path, "wp_4107_4116_wrong_canons.txt")
    report = load(output / "scope_validation_report.json")
    diagnostics = load(output / "conversation_diagnostics.json")["diagnostics"]
    codes = {d["code"] for d in diagnostics}
    assert report["status"] == "review_blocked"
    assert report["expected"] == [f"WP-{n:04d}" for n in range(4107, 4117)]
    assert report["found_expected"] == []
    assert report["unexpected"] == ["WP-0026", "WP-0027"]
    assert {"out_of_scope_runtime_canon", "unexpected_work_package",
            "assignment_scope_violation", "incomplete_or_truncated_runtime_canon",
            "missing_expected_work_package", "unsupported_completion_or_stop_claim"} <= codes
    execution = load(output / "execution_timeline.json")["events"]
    assert next(e for e in execution if e.get("wp_id") == "WP-0027")["completeness"] == "incomplete_or_truncated"


def test_scope_correction_supersedes_and_repeated_go_refusal_blocks(tmp_path):
    _, output = run_fixture(tmp_path, "wp_4117_correction_refusal.txt")
    scope = load(output / "scope_timeline.json")
    diagnostics = load(output / "conversation_diagnostics.json")["diagnostics"]
    codes = {d["code"] for d in diagnostics}
    assert scope["final_scope"] == [
        *[f"WP-{n:04d}" for n in range(4127, 4131)], "WP-Operator-Deck-Prototype"
    ]
    assert [e["event"] for e in scope["events"]] == [
        "scope_assignment", "assistant_restatement", "scope_correction", "assistant_restatement"
    ]
    assert scope["events"][-1]["authoritative"] is False
    assert scope["events"][2]["supersedes_sequence"] == 1
    assert {"ignored_scope_correction", "contradictory_assistant_scope_statement",
            "repeated_go_without_expected_output", "execution_refusal_after_go",
            "unsupported_completion_or_stop_claim", "stale_or_invalid_stop_condition",
            "missing_expected_work_package"} <= codes


def test_outputs_are_deterministic_review_only_and_complete(tmp_path):
    source = FIXTURES / "wp_4117_correction_refusal.txt"
    bundle = ingest(source, tmp_path / "ingestion")
    first = validate_scope(bundle, tmp_path / "first")
    second = validate_scope(bundle, tmp_path / "second")
    names = {"scope_timeline.json", "execution_timeline.json", "scope_validation_report.json",
             "conversation_diagnostics.json", "promotion_block_report.md"}
    assert names == {p.name for p in first.iterdir()}
    for name in names:
        assert (first / name).read_bytes() == (second / name).read_bytes()
    assert load(first / "scope_validation_report.json")["promotion_permitted"] is False
    assert "Automatic promotion is prohibited" in (first / "promotion_block_report.md").read_text()
    assert load(first / "scope_timeline.json")["source_message_provenance"]
    assert "Source-message provenance" in (first / "promotion_block_report.md").read_text()


def test_correction_with_rejected_old_range_uses_final_range_and_naked_heading(tmp_path):
    source = tmp_path / "capture.txt"
    source.write_text(
        "Steward: Assign WP-4117 through WP-4126.\n"
        "Steward: Correction: not WP-4117 through WP-4126; instead WP-4127 through WP-4130.\n"
        "Assistant: WP-4127 — Runtime Queue\nBody.\n",
        encoding="utf-8",
    )
    bundle = ingest(source, tmp_path / "ingested")
    output = validate_scope(bundle, tmp_path / "review")
    assert load(output / "scope_timeline.json")["final_scope"] == [
        "WP-4127", "WP-4128", "WP-4129", "WP-4130"
    ]
    events = load(output / "execution_timeline.json")["events"]
    assert any(e.get("wp_id") == "WP-4127" and e["in_scope"] for e in events)
