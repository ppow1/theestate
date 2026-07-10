from datetime import datetime, timedelta, timezone

import pytest

from estate.core.research_office import ResearchOfficeRuntime


def test_citation_integrity_and_source_inspection(tmp_path):
    rt = ResearchOfficeRuntime(tmp_path)
    req = rt.create_request("LLM routing", "Which routing approach is best?", "QA")
    src = rt.intake_source(req["request_id"], "Paper", "technical_paper", "file://paper.pdf", "Benchmarks", quality_rating="primary")
    finding = rt.record_finding(req["request_id"], "Approach A is faster.", [src["source_id"]], confidence="high")
    inspected = rt.inspect_source(src["source_id"])
    assert finding["citation_links"] == [f"sources/{src['source_id']}.json"]
    assert inspected["findings"][0]["finding_id"] == finding["finding_id"]


def test_duplicate_sources_are_reused_and_linked(tmp_path):
    rt = ResearchOfficeRuntime(tmp_path)
    r1 = rt.create_request("A", "Question A", "QA")
    r2 = rt.create_request("B", "Question B", "QA")
    s1 = rt.intake_source(r1["request_id"], "Vendor doc", "web", "https://example.test/doc", "Doc")
    s2 = rt.intake_source(r2["request_id"], "Vendor doc", "web", "https://example.test/doc", "Doc")
    assert s1["source_id"] == s2["source_id"]
    assert set(s2["linked_request_ids"]) == {r1["request_id"], r2["request_id"]}


def test_conflicting_claims_are_preserved(tmp_path):
    rt = ResearchOfficeRuntime(tmp_path)
    req = rt.create_request("Conflict", "What changed?", "QA")
    supporting = rt.intake_source(req["request_id"], "Doc A", "web", "https://a.test", "Supports")
    conflicting = rt.intake_source(req["request_id"], "Doc B", "web", "https://b.test", "Conflicts")
    finding = rt.record_finding(req["request_id"], "Feature exists.", [supporting["source_id"]], conflicting_source_ids=[conflicting["source_id"]])
    report = rt.review()
    assert finding["finding_id"] in report["conflicting_findings"]


def test_stale_findings_are_detectable(tmp_path):
    rt = ResearchOfficeRuntime(tmp_path)
    req = rt.create_request("Stale", "Is it current?", "QA")
    src = rt.intake_source(req["request_id"], "Old source", "manual_evidence", "manual:old", "Old")
    finding = rt.record_finding(req["request_id"], "Old claim.", [src["source_id"]], stale_after_days=1)
    path = tmp_path / "runtime/research_office/findings" / f"{finding['finding_id']}.json"
    data = path.read_text()
    old = (datetime.now(timezone.utc) - timedelta(days=3)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    path.write_text(data.replace(finding["reviewed_at"], old))
    assert finding["finding_id"] in rt.review()["stale_findings"]


def test_unsupported_recommendations_are_rejected(tmp_path):
    rt = ResearchOfficeRuntime(tmp_path)
    req = rt.create_request("Rec", "What should we do?", "QA")
    with pytest.raises(ValueError, match="unsupported recommendation"):
        rt.recommend(req["request_id"], "Adopt X", ["find-missing"], "No support")
