import copy
import hashlib
import json
from pathlib import Path

import pytest

from estate.cli.engineering_recommendation_confidence import main
from estate.core.engineering_recommendation_confidence import ConfidenceError, assess, compare, explain, history, validate_report

FIXTURES = Path(__file__).parents[1] / "fixtures"
NOW = "2026-07-27T00:00:00Z"

def load(name="complete_evidence"):
    return json.loads((FIXTURES / f"{name}.json").read_text())

def test_complete_evidence_is_reproducible_and_very_high():
    source = load(); before = copy.deepcopy(source)
    first = assess(source, assessed_at=NOW); second = assess(source, assessed_at=NOW)
    assert first == second
    assert source == before
    assert first["assessments"][0]["confidence_level"] == "very_high"
    assert first["assessments"][0]["evidence_summary"]["checks_covered"] == 8
    assert len(first["assessments"][0]["deterministic_confidence_hash"]) == 71
    assert validate_report(first) == []

@pytest.mark.parametrize("fixture,missing,degraded", [
    ("missing_providers", "providers", []),
    ("stale_dashboard", "freshness", []),
    ("degraded_integration", "providers", ["queue"]),
    ("incomplete_validation", "validation", []),
])
def test_incomplete_and_degraded_evidence(fixture, missing, degraded):
    item = assess(load(fixture), assessed_at=NOW)["assessments"][0]
    assert missing in item["missing_evidence"]
    assert item["degraded_providers"] == degraded

def test_conflicting_evidence_forces_low_confidence():
    item = assess(load("conflicting_dependency_graph"), assessed_at=NOW)["assessments"][0]
    assert item["confidence_level"] == "low"
    assert item["conflicting_evidence"] == ["dependency:WP-1->WP-2"]

def test_malformed_and_unsupported_inputs_fail_closed():
    with pytest.raises(json.JSONDecodeError): load("malformed_inputs")
    with pytest.raises(ConfidenceError, match="unsupported schema"):
        assess(load("unsupported_schema"), assessed_at=NOW)

def test_hash_tampering_is_detected():
    report = assess(load(), assessed_at=NOW)
    report["assessments"][0]["confidence_level"] = "low"
    with pytest.raises(ConfidenceError, match="deterministic_content_hash mismatch"):
        validate_report(report)

def test_explain_compare_and_history_are_read_only():
    first=assess(load(),assessed_at=NOW); second=assess(load("stale_dashboard"),assessed_at="2026-07-28T00:00:00Z")
    original=copy.deepcopy(first)
    assert explain(first,"highest_value_next_work:WP-1")["confidence_level"] == "very_high"
    assert compare(first,second)["changed"] == ["highest_value_next_work:WP-1"]
    assert [x["assessed_at"] for x in history([second,first])] == [NOW,"2026-07-28T00:00:00Z"]
    assert first == original

def test_cli_confidence_evidence_explain_compare_validate_history(tmp_path, capsys):
    source=FIXTURES/"complete_evidence.json"
    assert main(["confidence",str(source),"--assessed-at",NOW]) == 0
    report=json.loads(capsys.readouterr().out); report_path=tmp_path/"report.json"; report_path.write_text(json.dumps(report))
    for args in (["evidence",str(source),"--assessed-at",NOW], ["explain",str(report_path),"highest_value_next_work:WP-1"],
                 ["compare",str(report_path),str(report_path)], ["validate",str(report_path)], ["history",str(report_path)]):
        assert main(args) == 0; assert json.loads(capsys.readouterr().out)

def test_cli_does_not_modify_input(tmp_path, capsys):
    source=tmp_path/"sources.json"; source.write_bytes((FIXTURES/"complete_evidence.json").read_bytes())
    before=hashlib.sha256(source.read_bytes()).hexdigest()
    main(["confidence",str(source),"--assessed-at",NOW]); capsys.readouterr()
    assert hashlib.sha256(source.read_bytes()).hexdigest() == before
