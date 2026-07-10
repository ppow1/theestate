import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

from estate.core.merge_discovery_admission import MergeDiscoveryAdmission
from estate.core.operations_runtime import OperationsRuntime


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def candidate(root, wp="WP-0999", **kw):
    data={"target_id":"estate-main","work_package_id":wp,"state":"quarantined","canonical_discovery_id":f"mc-estate-main-{wp}-abc","source_kind":"merge","source_reference":"abc","source_commit":"abc","completion_receipt_path":f"collaboration/work_packages/completions/{wp}_codex_done.json","created_at":datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),"metadata":{"receipt":{"work_package_id":wp}},"provider_execution_performed":False,"dispatch_execution_performed":False}
    data.update(kw)
    write_json(root/"runtime/merge_discovery/canonical"/f"{data['canonical_discovery_id']}.json", data)
    return data


def test_current_receipt_backed_candidate_auto_admits(tmp_path):
    candidate(tmp_path)
    result=MergeDiscoveryAdmission(tmp_path).auto_admit(max_requests=5)
    assert result["summary"]["candidates_auto_admitted"] == 1
    reqs=list((tmp_path/"runtime/post_merge_audit/requests").glob("*.json"))
    assert len(reqs) == 1
    assert json.loads(reqs[0].read_text())["metadata"]["canonical_status"] == "admitted"
    assert result["provider_execution_performed"] is False
    assert result["dispatch_execution_performed"] is False


def test_historical_ambiguous_superseded_and_hold_do_not_admit(tmp_path):
    old=(datetime.now(timezone.utc)-timedelta(hours=96)).replace(microsecond=0).isoformat().replace("+00:00","Z")
    candidate(tmp_path,"WP-1000",created_at=old)
    candidate(tmp_path,"WP-1001",state="ambiguous")
    candidate(tmp_path,"WP-1002",state="superseded")
    candidate(tmp_path,"WP-1003")
    adm=MergeDiscoveryAdmission(tmp_path)
    adm.hold("estate-main","WP-1003")
    result=adm.auto_admit(max_requests=5)
    assert result["summary"]["candidates_auto_admitted"] == 0
    assert result["summary"]["historical_candidates_quarantined"] == 1
    adm.release("estate-main","WP-1003")
    result=adm.auto_admit(max_requests=5)
    assert result["summary"]["candidates_auto_admitted"] == 1


def test_final_verdict_duplicate_skipped_and_limit_enforced(tmp_path):
    candidate(tmp_path,"WP-1004")
    candidate(tmp_path,"WP-1005")
    write_json(tmp_path/"runtime/post_merge_audit/verdicts/v.json", {"target_id":"estate-main","work_package_id":"WP-1004","verdict":"ring2_required"})
    result=MergeDiscoveryAdmission(tmp_path).auto_admit(max_requests=1)
    assert result["summary"]["candidates_auto_admitted"] == 1
    assert result["summary"]["queue_limit_reached"] is False
    reqs=[json.loads(p.read_text()) for p in (tmp_path/"runtime/post_merge_audit/requests").glob("*.json")]
    assert reqs[0]["work_package_id"] == "WP-1005"


def test_runtime_processes_no_more_than_configured_max(monkeypatch, tmp_path):
    for wp in ["WP-1006","WP-1007","WP-1008"]:
        candidate(tmp_path, wp)
    monkeypatch.setattr("estate.core.background_operations_runtime.BackgroundOperationsRuntime.run_cycle", lambda self, write=True: {"requests":[],"events":[],"summary":{}})
    monkeypatch.setattr("estate.core.background_operations_runtime.BackgroundOperationsRuntime.load_watches", lambda self: [])
    monkeypatch.setattr("estate.core.operational_targets_runtime.OperationalTargetRuntime.write_status", lambda self: {"available_targets":[]})
    monkeypatch.setattr("estate.core.post_merge_audit_processor.PostMergeAuditProcessor.process_all", lambda self, max_count=10: {"processed_count": max_count, "results": [{"verdict":{"state":"ring2_required","verdict":"ring2_required","validation_status":"passed","artifacts":{"ring2_prompt":"p"},"verdict_path":"v"}} for _ in range(max_count)]})
    payload=OperationsRuntime(tmp_path).run_cycle(mode="process-audits", max_audit_requests=2)
    assert payload["audits_started"] == 2
    assert payload["audits_ring2_required"] == 2
    assert payload["audits_verdicts_published"] == 2
