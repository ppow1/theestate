from pathlib import Path

from office_operational_timeline import TimelineEvent, build_timeline, correlate_timeline, export_timeline, filter_timeline


def sample_events(tmp_path: Path):
    evidence = tmp_path / "collaboration/evidence"
    evidence.mkdir(parents=True)
    for name in ["merge.json", "validation.json", "decision.md", "provider.json"]:
        (evidence / name).write_text(name, encoding="utf-8")
    return [
        TimelineEvent("VAL-1", "2026-07-02T10:00:00Z", "validation", "Validation passed", "validation_result", "collaboration/evidence/validation.json", actor="ca5", package="WP-1", project="Office", office="ops", outcome="passed", correlation_id="WP-1"),
        TimelineEvent("MERGE-1", "2026-07-01T09:00:00Z", "merge", "Merge completed", "git_merge", "collaboration/evidence/merge.json", actor="ca4", package="WP-1", project="Office", office="ops", outcome="completed", correlation_id="WP-1"),
        TimelineEvent("DEC-1", "2026-07-03T12:00:00Z", "decision", "Decision accepted", "decision_record", "collaboration/evidence/decision.md", actor="helen", package="WP-2", project="Governance", office="exec", outcome="accepted"),
        TimelineEvent("DUTY-1", "2026-07-08T12:00:00Z", "resident_duty", "Resident duty", "duty_roster", "missing/duty.json", actor="grace", package="WP-3", project="Office", office="ops", outcome="pending"),
        TimelineEvent("PROV-1", "not-a-date", "provider_result", "Provider malformed", "provider", "collaboration/evidence/provider.json", actor="provider", outcome="completed"),
        TimelineEvent("VAL-1-DUP", "2026-07-02T10:00:00Z", "validation", "Validation passed", "validation_result", "collaboration/evidence/validation.json", actor="ca5", package="WP-1", project="Office", office="ops", outcome="passed", correlation_id="WP-1"),
    ]


def test_deterministic_ordering_duplicates_gaps_and_malformed_evidence(tmp_path):
    timeline = build_timeline(sample_events(tmp_path), root=tmp_path, stale_after_days=1)
    assert [event["id"] for event in timeline["events"]] == ["MERGE-1", "VAL-1", "DEC-1", "DUTY-1", "PROV-1"]
    assert "duplicate suppressed: VAL-1-DUP" in timeline["warnings"]
    assert "malformed evidence: PROV-1" in timeline["warnings"]
    assert "missing evidence: DUTY-1" in timeline["warnings"]
    assert timeline["events"][3]["indicators"]["gap_after_previous_days"] == 5
    assert timeline["events"][0]["canonical_artifact"] == "collaboration/evidence/merge.json"


def test_filtering_correlation_and_export(tmp_path):
    timeline = build_timeline(sample_events(tmp_path), root=tmp_path)
    filtered = filter_timeline(timeline, actor="ca5", package="WP-1", project="Office", office="ops", event_type="validation", outcome="passed")
    assert [event["id"] for event in filtered["events"]] == ["VAL-1"]
    dated = filter_timeline(timeline, date_from="2026-07-02T00:00:00Z", date_to="2026-07-03T23:59:59Z")
    assert [event["id"] for event in dated["events"]] == ["VAL-1", "DEC-1"]
    correlations = correlate_timeline(timeline)["correlations"]
    assert correlations["WP-1"] == ["MERGE-1", "VAL-1"]
    csv_output = export_timeline(filtered, format="csv")
    assert "VAL-1" in csv_output and "collaboration/evidence/validation.json" in csv_output
    json_output = export_timeline(filtered, format="json")
    assert '"schema": "estate.office_operational_timeline.v1"' in json_output
