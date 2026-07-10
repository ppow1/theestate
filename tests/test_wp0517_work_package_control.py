import json
from pathlib import Path

from estate.core.assignment_queue import generate_assignment_queue, update_work_package_control
from estate.core.office_command_surface import execute_office_action, controls_for_tab
from estate.core.steward_command_center import generate_command_center


def _wp(root: Path):
    p = root / "collaboration/work_packages/pending/WP-9999_Test_Control.md"
    p.parent.mkdir(parents=True)
    p.write_text("""# WP-9999 - Test Control

Status: Proposed
Priority: High
Owner: Architect

## Mission

Prove controls.

## Blockers

- Needs Steward decision

## Next Action

Assign a worker.
""", encoding="utf-8")
    return p


def test_assignment_state_priority_and_promotion_persist_and_refresh(tmp_path):
    _wp(tmp_path)
    result = execute_office_action("work_packages.assign", root=tmp_path, work_package_id="WP-9999", owner="Codex")
    assert result["outcome"] == "completed"
    result = execute_office_action("work_packages.update_state", root=tmp_path, work_package_id="WP-9999", state="open", priority="urgent")
    assert result["outcome"] == "completed"
    queue = json.loads((tmp_path / "runtime/work_packages/assignment_queue.json").read_text())
    wp = next(w for w in queue["work_packages"] if w["work_package_id"] == "WP-9999")
    assert wp["owner"] == "Codex"
    assert wp["state"] == "open"
    assert wp["priority"] == "urgent"
    promoted = execute_office_action("work_packages.promote", root=tmp_path, work_package_id="WP-9999")
    assert promoted["outcome"] == "completed"
    assert "runtime/work_packages/control_events.jsonl" in promoted["artifacts_written"]
    queue = generate_assignment_queue(root=tmp_path, write=False)
    assert next(w for w in queue["work_packages"] if w["work_package_id"] == "WP-9999")["state"] == "claimed"


def test_evidence_open_filter_blocker_display_and_office_payload(tmp_path):
    source = _wp(tmp_path)
    queue = generate_assignment_queue(root=tmp_path, write=True)
    wp = next(w for w in queue["work_packages"] if w["work_package_id"] == "WP-9999")
    assert wp["blockers"] == ["Needs Steward decision"]
    assert wp["next_action"] == "Assign a worker."
    opened = execute_office_action("work_packages.open_artifact", root=tmp_path, work_package_id="WP-9999", artifact_kind="source")
    assert opened["outcome"] == "completed"
    assert str(source.relative_to(tmp_path)).replace('\\', '/') in opened["artifacts_read"]
    filtered = execute_office_action("work_packages.filter", root=tmp_path, query="Steward", state="blocked")
    assert filtered["outcome"] == "completed"
    assert (tmp_path / "runtime/work_packages/last_filter_result.json").exists()
    controls = {c["action_id"] for c in controls_for_tab("work-packages")}
    assert {"work_packages.assign", "work_packages.update_state", "work_packages.promote", "work_packages.open_artifact", "work_packages.filter"} <= controls
    payload = generate_command_center(tmp_path, write=False)
    html = payload["panels"]["work_package_pipeline"]["data"]["sections"]["blocked"][0]
    assert html["priority"] == "high"
    assert html["evidence"]["source"].endswith("WP-9999_Test_Control.md")


def test_unsupported_transition_reports_failed_truthfully(tmp_path):
    _wp(tmp_path)
    result = execute_office_action("work_packages.update_state", root=tmp_path, work_package_id="WP-9999", state="invalid")
    assert result["outcome"] == "failed"
    assert "Unsupported state" in result["steward_message"]
