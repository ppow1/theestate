from __future__ import annotations
import copy, json, subprocess, sys
from pathlib import Path
import pytest
ROOT=Path(__file__).parents[1]
sys.path.insert(0,str(ROOT))
from dashboard.projection import DashboardError, PANEL_NAMES, build_snapshot, operator_summary, validate_snapshot
QUEUE=json.loads((ROOT.parent/"WP-4218/examples/engineering_queue_v1.json").read_text())
@pytest.fixture
def snapshot(): return build_snapshot(copy.deepcopy(QUEUE))
def test_queue_ingestion_snapshot_schema_immutable_and_all_panels(snapshot):
    validate_snapshot(snapshot)
    assert tuple(snapshot["panel_index"]) == PANEL_NAMES
    assert all(p["panel_schema_version"].endswith("/v1") and p["provenance"] for p in snapshot["panels"].values())
    with pytest.raises(TypeError): hash(snapshot)
def test_executive_filters_graph_cycle_parallel_risk_and_metrics(snapshot):
    s=snapshot["executive_summary"]
    assert s["total_queued_work"] == len(QUEUE["rows"])
    assert all(r["readiness_classification"] in {"ready","ready_with_coordination"} for r in snapshot["panels"]["ready_work"]["records"])
    assert all(r["readiness_classification"] == "blocked" for r in snapshot["panels"]["blocked_work"]["records"])
    graph=snapshot["panels"]["dependency_graph"]["records"][0]
    assert graph["dependency_cycles"] and graph["missing_dependencies"] == ["WP-NOT-FOUND"]
    assert snapshot["panels"]["parallel_opportunities"]["records"][0]["advisory_only"] is True
    assert {r["item_identifier"] for r in snapshot["panels"]["merge_risk"]["records"]} == {"WP-RISK","WP-CONFLICT"}
    metrics={m["metric_id"]:m for m in snapshot["panels"]["engineering_metrics"]["records"]}
    assert metrics["average_implementation_duration"]["status"] == "unavailable"
    assert metrics["blocked_work"]["value"] == s["blocked_work"]
def test_provider_degradation_empty_unavailable_freshness_and_summary(snapshot):
    assert snapshot["degradation_status"] == "degraded"
    assert snapshot["panels"]["recent_activity"]["state"] == "unavailable"
    assert snapshot["panels"]["audit_history"]["state"] == "unavailable"
    stale=build_snapshot(copy.deepcopy(QUEUE),as_of="2100-01-01T00:00:00Z")
    assert stale["freshness_status"] == "stale"
    assert "Advisory read-only" in operator_summary(snapshot)
def test_provenance_order_hash_and_repeated_run_equivalence():
    a=build_snapshot(copy.deepcopy(QUEUE),"2026-01-01T00:00:00Z")
    altered=copy.deepcopy(QUEUE); altered["rows"].reverse()
    b=build_snapshot(altered,"2027-01-01T00:00:00Z")
    assert a["deterministic_content_hash"] == b["deterministic_content_hash"]
    assert a["snapshot_identifier"] == b["snapshot_identifier"]
    assert all(r["provenance"] for r in a["panels"]["execution_queue"]["records"])
def test_malformed_unsupported_duplicate_and_hash_validation(snapshot):
    for mutation, message in [(lambda q:q.pop("rows"),"required"),(lambda q:q.update(queue_schema_version="estate.engineering-queue/v9"),"unsupported"),(lambda q:q["rows"].append(copy.deepcopy(q["rows"][0])),"duplicate")]:
        q=copy.deepcopy(QUEUE); mutation(q)
        with pytest.raises(DashboardError,match=message): build_snapshot(q)
    snapshot["campaign_health"]="healthy"
    with pytest.raises(DashboardError,match="hash mismatch"): validate_snapshot(snapshot)
def test_cli_success_degraded_fatal_compare_and_read_only(tmp_path):
    queue=tmp_path/"queue.json"; queue.write_text(json.dumps(QUEUE)); before=queue.read_bytes()
    cli=ROOT/"dashboard_cli.py"; one=tmp_path/"one"; two=tmp_path/"two"; base=[sys.executable,str(cli),"generate","--queue",str(queue)]
    first=subprocess.run(base+["--output",str(one),"--generated-at","2026-01-01T00:00:00Z"],capture_output=True,text=True)
    second=subprocess.run(base+["--output",str(two),"--generated-at","2027-01-01T00:00:00Z"],capture_output=True,text=True)
    assert first.returncode == second.returncode == 0 and '"degradation_status": "degraded"' in first.stdout
    cmp=subprocess.run([sys.executable,str(cli),"compare",str(one/"dashboard_snapshot_v1.json"),str(two/"dashboard_snapshot_v1.json")],capture_output=True,text=True)
    assert cmp.returncode == 0 and "equivalent" in cmp.stdout and queue.read_bytes() == before
    bad=tmp_path/"bad.json"; bad.write_text("{}")
    fatal=subprocess.run([sys.executable,str(cli),"generate","--queue",str(bad),"--output",str(tmp_path/"bad-out")],capture_output=True,text=True)
    assert fatal.returncode == 2 and not (tmp_path/"bad-out").exists()
    overlap=subprocess.run(base+["--output",str(queue.parent)],capture_output=True,text=True)
    assert overlap.returncode == 2
