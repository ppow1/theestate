import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from estate.core.autonomous_work_queue_scheduler import generate_autonomous_work_queue_scheduler


def write_text(root, rel, text):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def write_json(root, rel, payload):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def worker_summary(root, workers):
    write_json(root, "runtime/workers/worker_runtime_heartbeat.json", {"workers": workers})


def test_dependency_handling_waits_for_unmet_work_package_dependency(tmp_path):
    worker_summary(tmp_path, [{"worker_id": "codex", "status": "idle", "stale": False}])
    write_text(tmp_path, "collaboration/work_packages/pending/WP-0101_SERIES_dep.md", "# WP-0101\n\nOwner: codex\n\nDependencies: WP-0100\n")

    payload = generate_autonomous_work_queue_scheduler(tmp_path, write=False)

    assert payload["summary"]["waiting_count"] == 1
    assert payload["queues"]["waiting"][0]["unmet_dependencies"] == ["WP-0100"]
    assert payload["recommended_next_work_package"] is None


def test_completed_dependency_allows_ready_queue(tmp_path):
    worker_summary(tmp_path, [{"worker_id": "codex", "status": "idle", "stale": False}])
    write_text(tmp_path, "collaboration/work_packages/pending/WP-0101_SERIES_dep.md", "# WP-0101\n\nOwner: codex\n\nDependencies: WP-0100\n")
    write_json(tmp_path, "collaboration/work_packages/completions/WP-0100_codex_done.json", {"work_package_id": "WP-0100", "codex_status": "done"})

    payload = generate_autonomous_work_queue_scheduler(tmp_path, write=False)

    assert payload["summary"]["ready_count"] == 1
    assert payload["recommended_next_work_package"]["work_package_id"] == "WP-0101"


def test_blocked_work_uses_blocked_queue(tmp_path):
    worker_summary(tmp_path, [{"worker_id": "codex", "status": "idle", "stale": False}])
    write_text(tmp_path, "collaboration/work_packages/pending/WP-0102_SERIES_blocked.md", "# WP-0102\n\nOwner: codex\n\n## Blockers\n- Steward approval required\n")

    payload = generate_autonomous_work_queue_scheduler(tmp_path, write=False)

    assert payload["summary"]["blocked_count"] == 1
    assert payload["queues"]["blocked"][0]["work_package_id"] == "WP-0102"


def test_empty_queue_gracefully_reports_no_recommendation(tmp_path):
    worker_summary(tmp_path, [{"worker_id": "codex", "status": "idle", "stale": False}])

    payload = generate_autonomous_work_queue_scheduler(tmp_path, write=False)

    assert payload["summary"]["ready_count"] == 0
    assert payload["recommended_next_work_package"] is None


def test_unavailable_workers_warn_but_do_not_invent_state(tmp_path):
    worker_summary(tmp_path, [{"worker_id": "codex", "status": "offline", "stale": False}])
    write_text(tmp_path, "collaboration/work_packages/pending/WP-0103_SERIES_ready.md", "# WP-0103\n\nOwner: codex\n")

    payload = generate_autonomous_work_queue_scheduler(tmp_path, write=False)

    assert payload["summary"]["ready_count"] == 1
    assert payload["worker_availability"]["available_worker_count"] == 0
    assert any(w["type"] == "no_available_workers" for w in payload["warnings"])


def test_multiple_ready_items_recommend_first_by_assignment_order(tmp_path):
    worker_summary(tmp_path, [{"worker_id": "codex", "status": "idle", "stale": False}])
    write_text(tmp_path, "collaboration/work_packages/pending/WP-0105_SERIES_b.md", "# WP-0105\n\nOwner: codex\n")
    write_text(tmp_path, "collaboration/work_packages/pending/WP-0104_SERIES_a.md", "# WP-0104\n\nOwner: codex\n")

    payload = generate_autonomous_work_queue_scheduler(tmp_path, write=False)

    assert [item["work_package_id"] for item in payload["queues"]["ready"]] == ["WP-0104", "WP-0105"]
    assert payload["recommended_next_work_package"]["work_package_id"] == "WP-0104"


def test_missing_artifacts_are_warnings_when_writing_outputs(tmp_path):
    write_text(tmp_path, "collaboration/work_packages/pending/WP-0106_SERIES_ready.md", "# WP-0106\n\nOwner: codex\n")

    payload = generate_autonomous_work_queue_scheduler(tmp_path)

    assert (tmp_path / "runtime/work_packages/autonomous_work_queue_scheduler.json").exists()
    assert (tmp_path / "operations/work_packages/autonomous_work_queue_scheduler.md").exists()
    assert (tmp_path / "runtime/activity_console/work_queue_scheduler.json").exists()
    assert any(w["type"] == "missing_optional_artifact" for w in payload["warnings"])
