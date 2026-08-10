import json
import threading
import urllib.request

from estate.core.office_command_surface import execute_office_action
from estate.core.steward_annunciator import present_attention, watch_attention
from estate.core.steward_command_center import _steward_attention_html, generate_command_center, render_command_center_html, serve_command_center


class Recorder:
    def __init__(self): self.items = []
    def announce(self, item): self.items.append(item["id"])


def seed(root):
    registry = root / "data/registry/residents.json"
    registry.parent.mkdir(parents=True)
    registry.write_text(json.dumps([{"id": "RES-5", "name": "Project 5", "role": "Project"}]))
    task = root / "runtime/residents/task_status.json"
    task.parent.mkdir(parents=True)
    task.write_text(json.dumps({"residents": [{"resident_id": "RES-5", "current_task": "waiting for Steward input", "waiting_on": "steward"}]}))


def test_watch_presents_canonical_attention_source_once(tmp_path):
    seed(tmp_path); recorder = Recorder()
    result = watch_attention(tmp_path, interval_seconds=1, max_cycles=2, presenter=recorder)
    assert result["cycles_run"] == 2
    assert result["cycles"][0]["presented_count"] == 0
    assert result["cycles"][1]["new_item_count"] == 0
    assert len(recorder.items) == 0


def test_operations_center_banner_and_existing_acknowledge_action_clear(tmp_path):
    seed(tmp_path); state = present_attention(tmp_path, presenter=Recorder())
    payload = generate_command_center(tmp_path, write=False)
    html = render_command_center_html(payload)
    assert payload["panels"]["steward_attention"]["data"]["focus_policy"]["steals_keyboard_focus"] is False
    assert "steward-annunciator-banner" in html
    assert "Acknowledge" in html
    result = execute_office_action("attention.acknowledge", root=tmp_path, item_id=state["active_item_ids"][0], actor="Steward")
    assert result["outcome"] == "completed"
    cleared = json.loads((tmp_path / "runtime/office/steward_annunciator.json").read_text())
    assert cleared["active"] is False
    assert cleared["active_item_ids"] == []


def visual_item(item_id, classification="decision_required"):
    return {"id": item_id, "title": item_id, "summary": item_id, "classification": classification, "status": "open", "requested_steward_action": "review"}


def visual_panel(aggregate_items, annunciator_items):
    return {"data": {"aggregate": {"items": aggregate_items}, "annunciator": {"active": bool(annunciator_items), "severity": "decision_required", "severity_label": "DECISION REQUIRED", "items": annunciator_items}}}


def test_historical_visual_baseline_is_hidden_but_detail_backlog_remains(tmp_path):
    historical = [visual_item(f"WP-{i:04d}") for i in range(100)]
    panel = visual_panel(historical, [])

    banner = _steward_attention_html(panel, banner=True)
    detail = _steward_attention_html(panel)

    assert " hidden" in banner
    assert all(item["id"] not in banner for item in historical)
    assert all(item["id"] in detail for item in historical)


def test_visual_annunciator_shows_one_new_item_and_no_duplicate(tmp_path):
    item = visual_item("new-item")
    panel = visual_panel([item], [item])
    banner = _steward_attention_html(panel, banner=True)

    assert banner.count("data-item-id='new-item'") == 1
    assert " hidden" not in banner


def test_visual_annunciator_bounds_multiple_new_items(tmp_path):
    items = [visual_item(f"new-{i}") for i in range(5)]
    banner = _steward_attention_html(visual_panel(items, items), banner=True)

    assert "data-item-id='new-0'" in banner
    assert "data-item-id='new-2'" in banner
    assert "data-item-id='new-3'" not in banner
    assert "+2 additional new item(s)" in banner


def test_acknowledging_new_visual_item_clears_annunciator_without_mutating_backlog(tmp_path):
    seed(tmp_path); state = present_attention(tmp_path, presenter=Recorder())
    before = json.loads((tmp_path / "runtime/office/steward_attention_items.json").read_text())
    result = execute_office_action("attention.acknowledge", root=tmp_path, item_id=state["active_item_ids"][0], actor="Steward")
    after_state = json.loads((tmp_path / "runtime/office/steward_annunciator.json").read_text())
    after = json.loads((tmp_path / "runtime/office/steward_attention_items.json").read_text())

    assert result["outcome"] == "completed"
    assert after_state["active"] is False
    assert after_state["active_item_ids"] == []
    assert {item["id"] for item in before["items"]} == {item["id"] for item in after["items"]}


def test_served_operations_center_exposes_remote_banner_payload(tmp_path):
    seed(tmp_path); state = present_attention(tmp_path, presenter=Recorder())
    server = serve_command_center(host="127.0.0.1", port=0, root=tmp_path)
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        page = urllib.request.urlopen(base + "/", timeout=5).read().decode()
        payload = json.loads(urllib.request.urlopen(base + "/api/office/payload", timeout=5).read().decode())
        assert "steward-annunciator-banner" in page
        assert "annunciator_html" in payload and "steward-annunciator-banner" in payload["annunciator_html"]
        request = urllib.request.Request(base + "/api/office/actions/execute", data=json.dumps({"action_id": "attention.acknowledge", "item_id": state["active_item_ids"][0], "actor": "Steward", "note": "UI acceptance"}).encode(), headers={"Content-Type": "application/json"}, method="POST")
        result = json.loads(urllib.request.urlopen(request, timeout=5).read().decode())
        assert result["outcome"] == "completed"
        assert json.loads((tmp_path / "runtime/office/steward_annunciator.json").read_text())["active"] is False
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=5)
