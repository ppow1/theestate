from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))
from reconciler.engine import ReconciliationError, discover, reconcile, render_report, validate_queue
FIXTURE = ROOT / "fixtures/representative"

@pytest.fixture
def records():
    return discover(FIXTURE)

@pytest.fixture
def queue(records):
    return reconcile(records, "fixture-revision")

def rows(queue):
    return {r["item_identifier"]: r for r in queue["rows"]}

def test_discovery_identity_and_order_are_stable(records):
    assert records == discover(FIXTURE)
    assert records == sorted(records, key=lambda r:(r["id"],r["source_locator"],r["source_digest"]))
    assert all(r["source_digest"] and r["source_locator"] for r in records)

def test_duplicate_and_supersession(queue):
    r=rows(queue)
    assert r["WP-DUP-ALIAS"]["reconciliation_classification"] == "duplicate"
    assert r["WP-OLD"]["readiness_classification"] == "superseded"
    assert r["WP-MAYBE"]["readiness_classification"] == "needs_review"

def test_implementation_and_validation_evidence(queue):
    r=rows(queue)
    assert r["WP-8002"]["reconciliation_classification"] == "partially_implemented"
    assert r["WP-8003"]["reconciliation_classification"] == "implemented_but_not_validated"
    assert r["WP-8004"]["reconciliation_classification"] == "implemented_and_complete"

def test_dependency_missing_and_cycle_block(queue):
    r=rows(queue)
    assert "missing_dependency:WP-NOT-FOUND" in r["WP-MISSING"]["diagnostics"]
    assert r["WP-CYCLE-A"]["readiness_classification"] == "blocked"
    assert r["WP-CYCLE-B"]["readiness_classification"] == "blocked"

def test_lanes_touch_points_risk_and_parallel(queue):
    r=rows(queue)
    assert r["WP-SAFE"]["engineering_lane"]["primary"] == "Documentation"
    assert r["WP-SAFE"]["parallel_safety_classification"] == "safe"
    assert r["WP-RISK"]["merge_risk_classification"] == "high"
    assert r["WP-CONFLICT"]["blockers"] == ["conflicting_touch_points"]

def test_stale_ambiguous_and_parking_lot(queue):
    r=rows(queue)
    assert r["PL-001"]["reconciliation_classification"] == "captured"
    assert r["PL-002"]["reconciliation_classification"] == "promoted"
    assert r["PL-STALE"]["reconciliation_classification"] == "stale"
    assert r["WP-AMBIG"]["reconciliation_classification"] == "ambiguous_requires_review"

def test_optional_adapters_absent_or_present(queue):
    r=rows(queue)
    assert r["WP-ADAPTERS"]["duration_estimate_reference"] == "estimate-1"
    assert r["WP-ADAPTERS"]["git_readiness_reference"] == "git-ready-1"
    assert r["WP-SAFE"]["duration_estimate_reference"] is None

def test_schema_fields_provenance_and_report(queue):
    validate_queue(queue)
    assert all(r["provenance"] for r in queue["rows"])
    assert "Advisory" in render_report(queue)

def test_deterministic_hash_ignores_timestamp(records):
    a=reconcile(records,"rev","2026-01-01T00:00:00Z")
    b=reconcile(list(reversed(records)),"rev","2027-01-01T00:00:00Z")
    assert a["deterministic_content_hash"] == b["deterministic_content_hash"]
    assert a["rows"] == b["rows"]

def test_malformed_input():
    with pytest.raises(ReconciliationError, match="malformed source record"):
        discover(ROOT/"fixtures/malformed")

def test_validation_failure(queue):
    queue["advisory_only"] = False
    with pytest.raises(ReconciliationError):
        validate_queue(queue)

def test_cli_read_only_success_failure_and_equivalence(tmp_path):
    before={p: p.read_bytes() for p in FIXTURE.rglob("*") if p.is_file()}
    out1, out2, cli=tmp_path/"one", tmp_path/"two", ROOT/"reconcile.py"
    base=[sys.executable,str(cli),"generate","--source",str(FIXTURE),"--revision","rev"]
    assert subprocess.run(base+["--output",str(out1)],capture_output=True,text=True).returncode == 0
    assert subprocess.run(base+["--output",str(out2)],capture_output=True,text=True).returncode == 0
    compare=subprocess.run([sys.executable,str(cli),"compare",str(out1/"engineering_queue_v1.json"),str(out2/"engineering_queue_v1.json")],capture_output=True,text=True)
    assert compare.returncode == 0 and "equivalent" in compare.stdout
    assert before == {p:p.read_bytes() for p in FIXTURE.rglob("*") if p.is_file()}
    bad=subprocess.run(base+["--output",str(FIXTURE/"out")],capture_output=True,text=True)
    assert bad.returncode == 2 and not (FIXTURE/"out").exists()
