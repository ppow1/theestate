import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from estate.core.office_executive_workspace import build_executive_workspace, render_executive_workspace_markdown

NOW = datetime(2026, 7, 10, 12, 0, tzinfo=timezone.utc)


def write(root, rel, text):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def touch_old(path, days):
    ts = (NOW - timedelta(days=days)).timestamp()
    import os
    os.utime(path, (ts, ts))


def test_deterministic_attention_ranking_prioritizes_blockers(tmp_path):
    write(tmp_path, "collaboration/work_packages/pending/WP-1.md", "blocked by Steward attention")
    write(tmp_path, "operations/services/service_status_board.md", "provider warning")
    payload = build_executive_workspace(tmp_path, now=NOW)
    assert payload["attention_queue"][0]["category"] == "current_blockers"
    assert payload["attention_queue"][0]["priority_score"] > payload["attention_queue"][1]["priority_score"]


def test_readiness_verdict_blocks_short_unattended_operation_on_failed_validation(tmp_path):
    write(tmp_path, "operations/validation/latest.md", "validation failed; not production ready")
    payload = build_executive_workspace(tmp_path, now=NOW)
    assert payload["readiness_verdict"]["short_unattended_operation"] == "not_ready"
    assert payload["readiness_verdict"]["safe_to_leave_unattended"] is False


def test_evidence_links_and_drill_down_paths_are_relative(tmp_path):
    write(tmp_path, "collaboration/work_packages/reviews/WP-2.md", "review")
    payload = build_executive_workspace(tmp_path, now=NOW)
    item = next(i for i in payload["attention_queue"] if i["category"] == "pending_reviews")
    assert item["evidence"][0]["path"] == "collaboration/work_packages/reviews/WP-2.md"
    assert "collaboration" in payload["drill_down"]["controlling_workspaces"]


def test_missing_data_behavior_is_truthful_and_conditional(tmp_path):
    payload = build_executive_workspace(tmp_path, now=NOW)
    assert payload["uncertainty"]["missing_evidence"]
    assert payload["readiness_verdict"]["short_unattended_operation"] == "conditional"
    assert "does not approve" in payload["uncertainty"]["truthful_limitations"]


def test_stale_work_detection_uses_pending_and_active_mtime(tmp_path):
    p = write(tmp_path, "collaboration/work_packages/active/WP-old.md", "active work")
    touch_old(p, 9)
    payload = build_executive_workspace(tmp_path, now=NOW)
    assert any(i["category"] == "stale_work" for i in payload["attention_queue"])


def test_no_autonomous_approval_or_execution_and_renderer_discloses_boundary(tmp_path):
    write(tmp_path, "collaboration/work_packages/pending/WP-3.md", "blocker")
    payload = build_executive_workspace(tmp_path, now=NOW)
    assert payload["authority_boundaries"] == {"recommendations_are_decisions": False, "autonomous_approval": False, "autonomous_execution": False}
    assert all(item["autonomous_execution"] is False and item["decision_status"] == "recommendation_only" for item in payload["attention_queue"])
    md = render_executive_workspace_markdown(payload)
    assert "Recommendations are evidence, not decisions" in md
