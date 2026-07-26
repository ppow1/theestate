import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))
from analytics_engine import AnalyticsError, compare, generate_snapshot, history, trend, validate_snapshot


def observation(state="accepted_for_future_planning", observed="2026-07-02T00:00:00Z"):
    def source(name, **extra): return {"deterministic_content_hash": name * 64, **extra}
    item = {"engineering_lane":{"primary":"Testing"}, "blockers":["waiting"], "dependencies":["WP-1"],
            "diagnostics":["stale", "technical_debt"], "merge_risk_classification":"high", "current_lifecycle_state":"completed"}
    ledger = source("e", ledger_schema_version="estate.engineering-recommendation-ledger/v1",
        recommendations=[{"recommendation_identifier":"r1", "generation_timestamp":"2026-07-01T00:00:00Z"}],
        decisions=[{"linked_recommendation":"r1", "state":state, "review_timestamp":"2026-07-02T00:00:00Z"}])
    dashboard = source("b", dashboard_snapshot={"panels":{"execution_queue":{"records":[item]}, "completed_work":{"records":[item]},
        "validation_status":{"records":[{"status":"passed"}]}, "merge_risk":{"records":[item]}}})
    return {"observed_at":observed, "sources":{"queue":source("a", candidates=[item]), "dashboard":dashboard,
            "integration":source("c"), "recommendations":source("d"), "decision_ledger":ledger}}


def snapshot(state="accepted_for_future_planning", generated="2026-07-02T00:00:00Z"):
    return generate_snapshot(observation(state, generated), generated_at=generated)


def test_generation_is_deterministic_and_has_provenance_hash_and_metrics():
    before = observation(); frozen = copy.deepcopy(before)
    one = generate_snapshot(before, generated_at="2026-07-02T00:00:00Z")
    two = generate_snapshot(before, generated_at="2026-07-02T00:00:00Z")
    assert one == two and before == frozen and validate_snapshot(one) == []
    assert one["metrics"]["acceptance_rate"] == 1 and one["metrics"]["blocker_frequency"] == 1
    assert set(one["source_revisions"]) == set(before["sources"])


def test_trends_comparison_history_and_empty_history():
    left, right = snapshot("deferred"), snapshot("accepted_for_future_planning", "2026-07-03T00:00:00Z")
    report = trend([right, left], "weekly")
    assert report["sample_count"] == 2 and report["metrics"]["acceptance_rate"]["change"] == 1
    assert compare(left, right)["metric_changes"]["deferral_rate"] == -1
    assert history([right, left]) == [left, right]
    assert trend([], "campaign_lifetime")["sample_count"] == 0


def test_malformed_unsupported_and_conflicting_input():
    with pytest.raises(AnalyticsError, match="observed_at"): generate_snapshot({}, generated_at="2026-07-02T00:00:00Z")
    bad = observation(); bad["sources"]["decision_ledger"]["ledger_schema_version"] = "v999"
    with pytest.raises(AnalyticsError, match="unsupported"): generate_snapshot(bad, generated_at="2026-07-02T00:00:00Z")
    broken = snapshot(); broken["metrics"]["acceptance_rate"] = 2
    with pytest.raises(AnalyticsError, match="hash mismatch"): validate_snapshot(broken)


def test_cli_is_repeatable_and_read_only(tmp_path):
    source = tmp_path / "observation.json"; source.write_text(json.dumps(observation()))
    before = source.read_bytes()
    command = [sys.executable, str(ROOT / "analytics_cli.py"), "analytics", str(source), "--generated-at", "2026-07-02T00:00:00Z"]
    first = subprocess.run(command, check=True, capture_output=True, text=True).stdout
    second = subprocess.run(command, check=True, capture_output=True, text=True).stdout
    assert first == second and source.read_bytes() == before
    generated = tmp_path / "snapshot.json"; generated.write_text(first)
    valid = subprocess.run([sys.executable, str(ROOT / "analytics_cli.py"), "validate", str(generated)], check=True, capture_output=True, text=True)
    assert json.loads(valid.stdout) == {"valid": True}
