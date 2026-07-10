import json
from pathlib import Path
from estate.core.merge_discovery_consolidation import MergeDiscoveryConsolidator
from estate.core.post_merge_audit_processor import PostMergeAuditProcessor


def rec(i, wp="WP-0504", method="commit_message", sha=None, state="discovered"):
    return {"discovery_id": f"md-{i}", "target_id": "estate-main", "work_package_id": wp, "source_kind": "promotion", "source_commit": sha or f"sha{i}", "source_reference": sha or f"sha{i}", "correlation_method": method, "state": state, "metadata": {}}


def test_receipt_wins_and_weaker_records_superseded(tmp_path):
    c=MergeDiscoveryConsolidator(tmp_path)
    out=c.consolidate(records=[rec(1, method="commit_message"), rec(2, method="implementation_commit"), rec(3, method="receipt_work_package_id")], mode="quarantine", minimum_evidence_level="commit-message-only")
    assert out["summary"]["canonical_candidates"] == 1
    assert out["summary"]["superseded_discoveries"] == 2
    assert out["quarantined_candidates"][0]["discovery_id"] == "md-3"
    assert all(r["superseded_by"] == "md-3" for r in out["superseded_discoveries"])


def test_first_run_quarantines_and_explicit_admission_creates_one_request(tmp_path):
    c=MergeDiscoveryConsolidator(tmp_path)
    out=c.consolidate(records=[rec(1, method="implementation_commit")], mode="quarantine")
    assert out["summary"]["quarantined_discoveries"] == 1
    assert not (tmp_path/"runtime/post_merge_audit/requests").exists()
    admit=c.consolidate(records=[rec(1, method="implementation_commit")], mode="admit")
    assert admit["summary"]["admitted_requests"] == 1
    assert len(list((tmp_path/"runtime/post_merge_audit/requests").glob("*.json"))) == 1


def test_queue_limit_and_ca5_packages_at_most_one_each(tmp_path):
    records=[]
    for wp in ["WP-0504","WP-0505","WP-0506"]:
        records += [rec(wp+"a", wp=wp, method="implementation_commit"), rec(wp+"b", wp=wp, method="receipt_work_package_id")]
    out=MergeDiscoveryConsolidator(tmp_path).consolidate(records=records, mode="admit", max_requests_per_cycle=2)
    assert out["summary"]["canonical_candidates"] == 3
    assert out["summary"]["admitted_requests"] == 2
    reqs=list((tmp_path/"runtime/post_merge_audit/requests").glob("*.json"))
    assert len(reqs) == 2
    assert len({json.loads(p.read_text())["work_package_id"] for p in reqs}) == 2


def test_reconcile_preserves_history_and_processor_skips_superseded(tmp_path):
    reqdir=tmp_path/"runtime/post_merge_audit/requests"; reqdir.mkdir(parents=True)
    base={"target_id":"estate-main","work_package_id":"WP-0504","source_kind":"merge","source_reference":"rev","expected_files":[],"metadata":{"promoted_revision":"rev","correlation_method":"commit_message"},"state":"pending"}
    for aid in ["pma-1","pma-2"]:
        d={**base,"audit_id":aid}; (reqdir/f"{aid}.json").write_text(json.dumps(d))
    out=MergeDiscoveryConsolidator(tmp_path).reconcile_requests()
    assert out["summary"]["reconciled_existing_requests"] == 1
    states=[json.loads(p.read_text())["state"] for p in reqdir.glob("*.json")]
    assert states.count("superseded") == 1
    claimed=PostMergeAuditProcessor(tmp_path).claim_next()
    assert claimed["state"] == "claimed"
    assert claimed["audit_id"] in {"pma-1","pma-2"}


def test_ambiguous_discovery_stays_blocked(tmp_path):
    out=MergeDiscoveryConsolidator(tmp_path).consolidate(records=[rec(1, state="ambiguous")], mode="admit", minimum_evidence_level="commit-message-only")
    assert out["summary"]["ambiguous_discoveries"] == 1
    assert out["summary"]["admitted_requests"] == 0
