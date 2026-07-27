import json
from pathlib import Path
import pytest
from estate.core.engineering_campaign_operations import CampaignOperationError, CampaignStore, EngineeringCampaignOperations


def ops(tmp_path): return EngineeringCampaignOperations(CampaignStore(tmp_path / "store"))
def sources(): return [{"canonical_id":"engineering.backlog_reconciliation.v1","record_id":"one","source_class":"authoritative"}]

def test_deterministic_idempotent_operational_chain(tmp_path):
    runtime = ops(tmp_path)
    snapshot = runtime.reconcile(sources())
    assert snapshot == runtime.reconcile(list(reversed(sources())))
    rec = runtime.recommend(snapshot)
    assert rec == runtime.recommend(snapshot)
    decision = runtime.decide(rec, "accepted", "Engineering", "proof")
    translated = runtime.translate(rec, decision)
    chain = runtime.fixture_execute(translated)
    assert [x["record_type"] for x in chain][-1] == "GraceCompletionReceipt"
    assert all(x["fixture"] and not x["provider_invoked"] for x in chain)
    assert runtime.store.verify()
    before = runtime.inspect()["record_count"]
    runtime.fixture_execute(translated)
    assert runtime.inspect()["record_count"] == before

def test_internal_and_capability_paths_do_not_dispatch_directly(tmp_path):
    runtime = ops(tmp_path); snapshot = runtime.reconcile(sources())
    for classification, expected in [("create_Engineering_internal_work_item", "EngineeringWorkItem"), ("create_Helen_capability_development_request", "CapabilityDevelopmentRequest")]:
        rec = runtime.recommend(snapshot, classification); decision = runtime.decide(rec, "accepted", "Engineering", "proof")
        translated = runtime.translate(rec, decision)
        assert translated["created_record"]["record_type"] == expected
        assert translated["created_record"]["state"] == "proposed"

def test_fail_closed_guards(tmp_path):
    runtime = ops(tmp_path); empty = runtime.reconcile([]); low = runtime.recommend(empty)
    with pytest.raises(CampaignOperationError, match="low-confidence"): runtime.decide(low, "accepted", "Engineering", "no")
    good = runtime.recommend(runtime.reconcile(sources()))
    with pytest.raises(CampaignOperationError, match="conditions"): runtime.decide(good, "accepted_with_conditions", "Engineering", "no")
    rejected = runtime.decide(good, "rejected", "Engineering", "no")
    with pytest.raises(CampaignOperationError, match="accepted"): runtime.translate(good, rejected)

def test_tamper_detection(tmp_path):
    runtime = ops(tmp_path); runtime.reconcile(sources())
    path = runtime.store.ledger
    path.write_text(path.read_text().replace('"record_type":"EngineeringQueueSnapshot"', '"record_type":"BAD"'))
    assert not runtime.store.verify()
