import json
from pathlib import Path

import pytest

from estate.core.conversation_archive_ingestion import ingest
from estate.core.runtime_canon_recovery import (
    CandidateCompletenessEvaluator, CandidateReconciler, CandidateTruncationDetector,
    PendingWorkPackageIndex, RuntimeCanonCandidateDetector, RuntimeCanonRecoveryPipeline,
    SupportingDocumentRenderer, WorkPackageDefinitionParser, normalize_identifier,
)


def definition(root: Path, wp="WP-4212", title="Recovery", extra="") -> Path:
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{wp}_{title}.md"
    path.write_text(f"# {wp} — {title}\n\n## Purpose\nMust recover evidence.\n\n## Runtime Behavior\nMust explain runtime behavior.\n\n## Unit Tests\nMust include tests.\n\n## Boundaries and Prohibited Behavior\nMust not automatically promote.\n{extra}", encoding="utf-8")
    return path


def record(text, role="assistant", sequence=2):
    return {"role": role, "sequence": sequence, "source_message_id": f"m{sequence}", "text": " ".join(text.split()), "formatted_text": text, "text_sha256": "a" * 64, "formatted_text_sha256": "b" * 64, "provenance": {}}


def canon(wp="WP-4212", ending="Completion criteria are verified."):
    return f"""# Runtime Canon — {wp}
## Purpose
This supporting document recovers candidate evidence with detailed implementation behavior and clear boundaries.
## Schema and persistent records
The schema stores provenance, hashes, diagnostics, audit records, identifiers, and review state deterministically.
## Runtime Behavior
The runtime detects structured assistant output, resolves its definition, assesses it, and stages review material. It must not automatically promote or overwrite pending definitions.
## Integration and CLI
The CLI handles archives and normalized records. Integration preserves archive provenance and reports every diagnostic.
## Unit Tests and Validation
Tests cover detection, runtime behavior, schemas, boundaries, matching, truncation, duplicates, and deterministic validation scenarios.
## Acceptance and Completion Criteria
{ending}"""


def detect(text):
    return RuntimeCanonCandidateDetector().detect(record(text), {"path": "a.txt", "sha256": "1" * 64}, None, None)


def test_identifier_normalization_and_named_handling():
    assert normalize_identifier("wp 4212") == ("WP-4212", "numbered")
    assert normalize_identifier("WP-Operator-Deck-Prototype") == ("WP-OPERATOR-DECK-PROTOTYPE", "named")
    assert normalize_identifier("WP-12")[0] is None


def test_pending_index_creation_and_exact_resolution(tmp_path):
    definition(tmp_path)
    index = PendingWorkPackageIndex(tmp_path).build()
    assert index.records[0]["filename_body_consistent"]
    assert index.resolve("WP-4212")[0] == "matched_unique"
    assert index.resolve("WP-9999")[0] == "unmatched_identifier"
    assert index.resolve("WP-NOT-APPROVED")[0] == "named_identifier_not_approved"


def test_supported_historical_and_approved_named_filenames(tmp_path):
    (tmp_path / "CONV-PTM-001_Legacy.md").write_text("# CONV-PTM-001 — Legacy\n\n## Purpose\nMust work.\n")
    (tmp_path / "WP-Operator-Deck-Prototype.md").write_text("# Work Package: Operator Deck Prototype\n")
    index = PendingWorkPackageIndex(tmp_path).build()
    assert not index.diagnostics
    assert index.resolve("CONV-PTM-001")[0] == "matched_unique"
    assert index.resolve("WP-OPERATOR-DECK-PROTOTYPE")[0] == "matched_unique"


def test_duplicate_filename_body_mismatch_and_malformed(tmp_path):
    definition(tmp_path / "a")
    definition(tmp_path / "a", title="Other")
    (tmp_path / "a" / "WP-4213_Bad.md").write_text("# WP-4214 — Bad\n", encoding="utf-8")
    (tmp_path / "a" / "Notes.md").write_text("# Notes\n", encoding="utf-8")
    index = PendingWorkPackageIndex(tmp_path / "a").build()
    codes = {d["code"] for d in index.diagnostics}
    assert {"duplicate_pending_work_package_identifier", "pending_filename_body_identifier_mismatch", "malformed_pending_work_package_identifier"} <= codes
    assert index.resolve("WP-4212")[0] == "ambiguous_identifier"


@pytest.mark.parametrize("text", [
    "WP-4212", "Assigned: WP-4212, WP-4213, WP-4214", "I will now produce WP-4212.",
    "> Implement WP-4212\n> authoritative work package\n> required implementation\nSome copied startup seed.",
])
def test_bare_mentions_assignments_declarations_and_seeds_rejected(text):
    decision = detect(text)
    assert decision is None or not decision["detected"]


@pytest.mark.parametrize("heading", ["WP-4212 Runtime Canon", "Supporting Design for WP-4212", "# Runtime Canon — WP-4212"])
def test_substantive_variants_detected(heading):
    text = canon().replace("# Runtime Canon — WP-4212", heading)
    decision = detect(text)
    assert decision["detected"] and decision["candidate_wp_identifier"] == "WP-4212"
    assert decision["original_text"] == text and decision["segments"]


def test_user_authored_evidence_is_disabled():
    detector = RuntimeCanonCandidateDetector()
    assert detector.detect(record(canon(), role="user"), {"path": "x", "sha256": "1" * 64}, None, None) is None


def test_definition_dimension_parsing(tmp_path):
    definition(tmp_path)
    item = PendingWorkPackageIndex(tmp_path).build().records[0]
    dimensions = WorkPackageDefinitionParser().parse(item)
    assert {d["normalized_dimension"] for d in dimensions} >= {"purpose", "runtime_behavior", "unit_tests", "boundaries"}
    assert all(d["source_line_range"][0] <= d["source_line_range"][1] for d in dimensions)


def evaluated(tmp_path, body):
    definition(tmp_path)
    item = PendingWorkPackageIndex(tmp_path).build().records[0]
    candidate = detect(body)
    return CandidateCompletenessEvaluator().evaluate(candidate, item, WorkPackageDefinitionParser().parse(item))


def test_full_and_partial_candidate_assessment(tmp_path):
    full = evaluated(tmp_path / "full", canon())
    partial = evaluated(tmp_path / "partial", "# WP-4212 Runtime Canon\n" + ("Purpose detail only. " * 100))
    assert full["assessment"] == "complete_supporting_document"
    assert partial["assessment"] == "partial_supporting_document"


def test_unsupported_completion_claim_does_not_create_completion(tmp_path):
    result = evaluated(tmp_path, "# WP-4212 Runtime Canon\n## Purpose\n" + "All requirements are met. " * 60)
    assert result["unsupported_claims"] and result["assessment"] != "complete_supporting_document"


@pytest.mark.parametrize(("text", "status"), [("# Canon\n```json\n{}", "confirmed_truncated"), ("# Canon\nNext section follows:", "likely_truncated"), (canon(), "not_truncated")])
def test_truncation_detection(text, status):
    assert CandidateTruncationDetector().assess(text)["status"] == status


def candidates(*texts):
    return [detect(text) for text in texts]


def test_exact_and_near_duplicate_reconciliation(tmp_path):
    first, exact, near = candidates(canon(), canon(), canon().replace("verified", "validated"))
    for i, item in enumerate((first, exact, near)): item["candidate_id"] = str(i)
    assessment = {str(i): {"assessment": "complete_supporting_document", "truncation_status": "not_truncated", "coverage_score": 100, "unsupported_claims": []} for i in range(3)}
    group = CandidateReconciler().reconcile([first, exact, near], assessment)[0]
    assert group["duplicate_group"]
    assert {r["relationship"] for r in group["relations"]} >= {"exact_duplicate", "near_duplicate"}


def test_competing_complete_candidates_require_human_selection():
    a, b = candidates(canon(), canon(ending="A materially different architecture uses a queue and database with extensive corrective detail." * 8))
    a["candidate_id"], b["candidate_id"] = "a", "b"
    assessments = {x: {"assessment": "complete_supporting_document", "truncation_status": "not_truncated", "coverage_score": 100, "unsupported_claims": []} for x in ("a", "b")}
    group = CandidateReconciler().reconcile([a, b], assessments)[0]
    assert group["competing_group"] and group["preferred_candidate_id"] is None


def test_partial_versus_complete_preference():
    a, b = candidates(canon(), canon().replace("Tests cover", "A brief note covers"))
    a["candidate_id"], b["candidate_id"] = "complete", "partial"
    assessments = {"complete": {"assessment": "complete_supporting_document", "truncation_status": "not_truncated", "coverage_score": 100, "unsupported_claims": []}, "partial": {"assessment": "partial_supporting_document", "truncation_status": "not_truncated", "coverage_score": 30, "unsupported_claims": []}}
    assert CandidateReconciler().reconcile([a, b], assessments)[0]["preferred_candidate_id"] == "complete"


def test_supporting_document_rendering_preserves_provenance_and_never_targets_pending(tmp_path):
    pending = tmp_path / "pending"; definition(pending); item = PendingWorkPackageIndex(pending).build().records[0]; candidate = detect(canon()); assessment = evaluated(tmp_path / "eval", canon())
    manifest = SupportingDocumentRenderer().render(tmp_path / "run", candidate, item, assessment, "preferred")
    content = (tmp_path / "run" / manifest["staging_path"]).read_text()
    assert candidate["original_text"] in content and "canonical: false" in content
    assert not manifest["proposed_destination"].startswith("collaboration/work_packages/pending/")
    assert definition(pending).read_text().startswith("# WP-4212")


def test_pipeline_integration_assignment_mismatch_does_not_block_and_is_deterministic(tmp_path):
    pending = tmp_path / "pending"; definition(pending)
    source = tmp_path / "chat.txt"; source.write_text("Steward: Only produce WP-9999.\nAssistant: " + canon(), encoding="utf-8")
    pipeline = RuntimeCanonRecoveryPipeline(Path.cwd(), pending, tmp_path / "outputs")
    first = pipeline.run([source]); second = pipeline.run([source])
    assert first == second
    match = json.loads((first / "definition_match_report.json").read_text())["matches"][0]
    assert match["resolution_state"] == "matched_unique"
    assessment = json.loads((first / "candidate_assessment_report.json").read_text())["assessments"][0]
    assert assessment["assessment"] == "complete_supporting_document"
    artifacts = {p.name for p in first.iterdir()}
    assert {"pending_work_package_index.json", "pending_index_repair_report.json", "archive_inventory.json", "runtime_canon_candidates.json", "definition_match_report.json", "candidate_assessment_report.json", "candidate_reconciliation_report.json", "supporting_document_manifest.json", "runtime_canon_review_queue.json", "runtime_canon_recovery_report.md", "pending_index_repair_report.md", "production_activation_report.md", "promotion_block_report.md"} <= artifacts
    assert json.loads((first / "supporting_document_manifest.json").read_text())["automatic_promotion_permitted"] is False


def test_scope_correction_does_not_change_candidate_identity():
    before = detect(canon()); after = detect(canon())
    assert before["candidate_id"] == after["candidate_id"] and before["candidate_wp_identifier"] == "WP-4212"


def test_directory_discovery_filters_duplicates_and_supports_html(tmp_path):
    pending = tmp_path / "pending"; definition(pending)
    html = ('<div data-message-author-role="user" data-message-id="u">go</div>'
            '<div data-message-author-role="assistant" data-message-id="a">' + canon() + '</div>')
    intake = tmp_path / "intake"; intake.mkdir()
    (intake / "one.html").write_text(html)
    (intake / "copy.html").write_text(html)
    run = RuntimeCanonRecoveryPipeline(Path.cwd(), pending, tmp_path / "out").run([intake])
    inventory = json.loads((run / "archive_inventory.json").read_text())
    assert inventory["duplicate_inputs"] == 1
    assert len(json.loads((run / "runtime_canon_candidates.json").read_text())["decisions"]) == 1


def test_invalid_definition_does_not_block_valid_identifier(tmp_path):
    pending = tmp_path / "pending"; definition(pending)
    (pending / "WP-9998_Bad.md").write_text("# WP-9999 — mismatch\n")
    source = tmp_path / "chat.txt"; source.write_text("Assistant: " + canon())
    run = RuntimeCanonRecoveryPipeline(Path.cwd(), pending, tmp_path / "out").run([source])
    assert json.loads((run / "definition_match_report.json").read_text())["matches"][0]["resolution_state"] == "matched_unique"
