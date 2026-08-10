import json
import threading
import urllib.request

from estate.core.office_command_surface import execute_office_action
from estate.core.steward_annunciator import present_attention, watch_attention
from estate.core.steward_command_center import generate_command_center, render_command_center_html, serve_command_center


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
    assert result["cycles"][0]["presented_count"] == 1
    assert result["cycles"][1]["new_item_count"] == 0
    assert len(recorder.items) == 1


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
