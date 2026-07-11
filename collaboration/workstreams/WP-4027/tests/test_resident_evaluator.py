from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from resident_evaluator import EvaluationError, evaluate_records, load_record, validate_record

FIXTURE = ROOT / "fixtures" / "sample_evaluation_record.json"


def test_fixture_record_is_valid_and_source_linked():
    record = load_record(FIXTURE)
    validate_record(record)
    assert record["source"]["uri"]
    assert record["source"]["evidence_hash"].startswith("sha256:")


def test_report_separates_evidence_interpretation_and_follow_up():
    report = evaluate_records([load_record(FIXTURE)])
    assert set(report) >= {"measured_evidence", "interpretation", "recommended_follow_up"}
    assert report["measured_evidence"]["sources"][0]["record_id"] == "eval-2026-07-11-alfred-001"
    assert report["interpretation"]["identity_and_boundary_failures_visible"] is True
    assert "boundary_compliance" in report["interpretation"]["boundary_failure_dimensions"]
    assert report["interpretation"]["unsupported_claims_recorded_distinctly"] is True
    assert isinstance(report["interpretation"]["deterministic_score"], int)
    assert report["boundaries"]["no_model_assignment_changes"] is True


def test_unsupported_claim_requires_claim_text_when_present():
    record = load_record(FIXTURE)
    unsupported = next(item for item in record["measurements"] if item["dimension"] == "unsupported_claims")
    unsupported.pop("claim_text")
    try:
        validate_record(record)
    except EvaluationError as exc:
        assert "unsupported claims require claim_text" in str(exc)
    else:
        raise AssertionError("expected unsupported claim validation failure")
