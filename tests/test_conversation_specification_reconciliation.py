from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from estate.core.conversation_specification_reconciliation import (
    ReconciliationError, reconcile_bundles, validate_reconciliation,
)


AREAS = ["Policy and governing principles", "Schemas and persistent records", "Runtime behavior",
         "Decision and escalation logic", "Boundaries and prohibited behavior", "Estate system integrations",
         "Audit and review surfaces", "Diagnostics and failure handling", "Operator documentation",
         "Unit tests", "Integration tests", "Validation scenarios", "Anti-patterns", "Completion criteria"]


def canon(wp="WP-9001", extra=""):
    sections = "\n".join(f"## {name}\n" + "This section defines deterministic review requirements and preserves evidence for authorized human assessment only. " * 3 for name in AREAS)
    return f"# {wp} — Candidate\n{sections}\n{extra}\n"


def pending(root: Path, wp="WP-9001"):
    path = root / "collaboration/work_packages/pending" / f"{wp}_Test.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# Objective\nPolicy schema runtime behavior decision escalation boundaries prohibited integration audit review diagnostics failure operator documentation unit test integration test validation scenario anti-pattern completion acceptance criteria.\n")


def bundle(root: Path, name: str, contents: list[tuple[str, str, str | None]], archive="a" * 64) -> Path:
    path = root / name
    (path / "candidates").mkdir(parents=True)
    candidates = []
    run = hashlib.sha256(name.encode()).hexdigest()[:16]
    for index, (wp, content, destination) in enumerate(contents):
        artifact = f"candidates/{wp}-{index}.md"
        (path / artifact).write_text(content)
        candidates.append({"wp_id": wp, "title": "Test", "proposed_destination": destination or f"specifications/{wp}.md",
            "staging_artifact": artifact, "content_sha256": hashlib.sha256(content.encode()).hexdigest(), "diagnostics": [],
            "provenance": {"source_archive_sha256": archive, "extraction_run": run, "wp_identifier": wp,
                           "source_message_id": f"m{index}", "source_sequence": index + 1}})
    report = {"schema_version": "estate.conversation-specification-extraction/v1", "run_id": run,
              "canonical_status": "non_canonical_review_material", "candidates": candidates,
              "source": {"archive_sha256": archive}}
    (path / "validation_report.json").write_text(json.dumps(report))
    return path


def run(tmp_path: Path, bundles, expected=("WP-9001",), drafts=False):
    return reconcile_bundles(bundles, list(expected), tmp_path / "out", repository_root=tmp_path,
                             generate_drafts=drafts)


def test_valid_single_candidate_outputs_complete_review_bundle(tmp_path: Path):
    pending(tmp_path)
    result = run(tmp_path, [bundle(tmp_path, "one", [("WP-9001", canon(), None)])])
    assert validate_reconciliation(result)["status"] == "ready_for_human_review"
    required = {"reconciliation_manifest.json", "coverage_report.json", "candidate_assessments.jsonl",
                "duplicate_comparisons.json", "reconciliation_report.md", "promotion_plan.json", "diagnostics.json"}
    assert required <= {p.name for p in result.iterdir()}
    assert json.loads((result / "promotion_plan.json").read_text())["mode"] == "review_only_no_writes"


@pytest.mark.parametrize("replacement,code", [("", "runtime_area_absent"), ("## Unit tests\nTBD\n", "runtime_area_present_substantively_empty")])
def test_missing_and_empty_runtime_sections_block(tmp_path: Path, replacement: str, code: str):
    pending(tmp_path)
    text = canon().replace("## Unit tests\n" + "This section defines deterministic review requirements and preserves evidence for authorized human assessment only. " * 3, replacement)
    result = run(tmp_path, [bundle(tmp_path, "bad", [("WP-9001", text, None)])])
    assessment = json.loads((result / "candidate_assessments.jsonl").read_text())
    assert code in assessment["diagnostics"]


def test_unsupported_completion_claim_blocks(tmp_path: Path):
    pending(tmp_path)
    result = run(tmp_path, [bundle(tmp_path, "claim", [("WP-9001", canon(extra="Implementation completed."), None)])])
    assert "unsupported_completion_claim" in json.loads((result / "candidate_assessments.jsonl").read_text())["diagnostics"]


def status(result: Path):
    return json.loads((result / "duplicate_comparisons.json").read_text())["comparisons"][0]["status"]


def test_identical_and_three_candidate_duplicates(tmp_path: Path):
    pending(tmp_path)
    b1 = bundle(tmp_path, "a", [("WP-9001", canon(), None)])
    b2 = bundle(tmp_path, "b", [("WP-9001", canon(), None)])
    b3 = bundle(tmp_path, "c", [("WP-9001", canon(), None)])
    result = run(tmp_path, [b1, b2, b3])
    assert status(result) == "duplicate_identical"
    assert json.loads((result / "duplicate_comparisons.json").read_text())["comparisons"][0]["candidate_count"] == 3


def test_compatible_duplicates_generate_provenanced_review_draft(tmp_path: Path):
    pending(tmp_path)
    a, b = canon(extra="## Source A Detail\nUnique alpha evidence."), canon(extra="## Source B Detail\nUnique beta evidence.")
    result = run(tmp_path, [bundle(tmp_path, "a", [("WP-9001", a, None)]), bundle(tmp_path, "b", [("WP-9001", b, None)])], drafts=True)
    assert status(result) == "duplicate_compatible_merge_possible"
    draft = (result / "reconciled_candidates/WP-9001.md").read_text()
    assert "NON-CANONICAL" in draft and "source-sha256" in draft


def test_material_conflict_refuses_merge(tmp_path: Path):
    pending(tmp_path)
    a = canon(extra="## Authority Choice\nThe operator must allow automatic promotion.")
    b = canon(extra="## Authority Choice\nThe operator must not allow automatic promotion.")
    result = run(tmp_path, [bundle(tmp_path, "a", [("WP-9001", a, None)]), bundle(tmp_path, "b", [("WP-9001", b, None)])], drafts=True)
    assert status(result) == "duplicate_material_conflict"
    assert not (result / "reconciled_candidates/WP-9001.md").exists()


def test_expected_range_missing_unexpected_and_invalid(tmp_path: Path):
    for wp in ("WP-9001", "WP-9002", "WP-9003"): pending(tmp_path, wp)
    result = run(tmp_path, [bundle(tmp_path, "range", [("WP-9001", canon("WP-9001"), None), ("WP-9003", canon("WP-9003"), None), ("BAD", canon("BAD"), None)])], expected=("WP-9001", "WP-9002"))
    coverage = json.loads((result / "coverage_report.json").read_text())
    assert coverage["missing"] == ["WP-9002"] and coverage["unexpected"] == ["WP-9003"] and coverage["invalid"] == ["BAD"]


def test_hash_tampering_and_provenance_mismatch(tmp_path: Path):
    pending(tmp_path)
    source = bundle(tmp_path, "bad", [("WP-9001", canon(), None)])
    report = json.loads((source / "validation_report.json").read_text())
    report["candidates"][0]["content_sha256"] = "0" * 64
    report["candidates"][0]["provenance"]["extraction_run"] = "wrong"
    (source / "validation_report.json").write_text(json.dumps(report))
    result = run(tmp_path, [source])
    diagnostics = json.loads((result / "candidate_assessments.jsonl").read_text())["diagnostics"]
    assert {"candidate_hash_tampering", "provenance_mismatch"} <= set(diagnostics)


@pytest.mark.parametrize("destination,expected", [
    ("collaboration/work_packages/pending/WP-9001_Test.md", "pending_definition_overwrite"),
    ("../outside.md", "ambiguous_destination"),
])
def test_unsafe_destinations(tmp_path: Path, destination: str, expected: str):
    pending(tmp_path)
    result = run(tmp_path, [bundle(tmp_path, "dest", [("WP-9001", canon(), destination)])])
    assert json.loads((result / "candidate_assessments.jsonl").read_text())["destination_assessment"]["status"] == expected


def test_existing_and_cross_candidate_destination_collisions(tmp_path: Path):
    pending(tmp_path); pending(tmp_path, "WP-9002")
    (tmp_path / "specifications").mkdir(); (tmp_path / "specifications/existing.md").write_text("canonical")
    one = bundle(tmp_path, "one", [("WP-9001", canon(), "specifications/existing.md")])
    result = run(tmp_path, [one])
    assert json.loads((result / "candidate_assessments.jsonl").read_text())["destination_assessment"]["status"] == "existing_destination_collision"
    shared = bundle(tmp_path, "shared", [("WP-9001", canon(), "specifications/shared.md"), ("WP-9002", canon("WP-9002"), "specifications/shared.md")])
    result = run(tmp_path / "other", [shared], expected=("WP-9001", "WP-9002"))
    assert "cross_candidate_destination_collision" in (result / "diagnostics.json").read_text()


def test_deterministic_rerun_and_artifact_tampering_detection(tmp_path: Path):
    pending(tmp_path)
    source = bundle(tmp_path, "same", [("WP-9001", canon(), None)])
    first = run(tmp_path, [source]); snapshot = {p.relative_to(first): p.read_bytes() for p in first.rglob("*") if p.is_file()}
    second = run(tmp_path, [source]); assert snapshot == {p.relative_to(second): p.read_bytes() for p in second.rglob("*") if p.is_file()}
    (second / "coverage_report.json").write_text("tampered")
    with pytest.raises(ReconciliationError, match="integrity"): validate_reconciliation(second)

