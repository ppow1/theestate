import json

from estate.core.steward_annunciator import present_attention
from estate.core.steward_attention import record_action


class Recorder:
    def __init__(self): self.items = []
    def announce(self, item): self.items.append(item["id"])


class Failing:
    def announce(self, item): raise RuntimeError("speaker unavailable")


def seed(root):
    registry = root / "data/registry/residents.json"
    registry.parent.mkdir(parents=True)
    registry.write_text(json.dumps([{"id": "RES-5", "name": "Project 5", "role": "Project"}]))
    p = root / "runtime/residents/task_status.json"
    p.parent.mkdir(parents=True)
    p.write_text(json.dumps({"residents": [{"resident_id": "RES-5", "resident_name": "Project 5", "current_task": "waiting", "waiting_on": "steward"}]}))


def test_new_item_dedupes_across_poll_and_restart(tmp_path):
    seed(tmp_path); first = Recorder()
    one = present_attention(tmp_path, presenter=first, now="2026-08-09T20:00:00+00:00")
    assert first.items and one["last_run"]["presented_count"] == 1
    second = Recorder(); two = present_attention(tmp_path, presenter=second, now="2026-08-09T20:01:00+00:00")
    assert second.items == [] and two["active"]
    restarted = Recorder(); three = present_attention(tmp_path, presenter=restarted, now="2026-08-09T20:02:00+00:00")
    assert restarted.items == [] and three["active_item_ids"] == one["active_item_ids"]


def test_severity_and_acknowledgement_clear_annunciator(tmp_path):
    seed(tmp_path); rec = Recorder(); state = present_attention(tmp_path, presenter=rec)
    assert state["severity"] == "decision_required"
    record_action(state["active_item_ids"][0], "acknowledge", root=tmp_path)
    cleared = present_attention(tmp_path, presenter=Recorder())
    assert not cleared["active"] and cleared["active_item_ids"] == []


def test_presenter_failure_keeps_visual_alarm_and_retries(tmp_path):
    seed(tmp_path); failed = present_attention(tmp_path, presenter=Failing())
    assert failed["active"] and failed["last_run"]["failure_count"] == 1 and not failed["presented"]
    recovered = Recorder(); state = present_attention(tmp_path, presenter=recovered)
    assert recovered.items and state["last_run"]["presented_count"] == 1


def test_urgent_has_precedence_for_visual_severity(tmp_path, monkeypatch):
    payload = {"items": [
        {"id": "soon", "title": "Soon", "summary": "soon", "classification": "attention_soon", "status": "open", "requested_steward_action": "review"},
        {"id": "urgent", "title": "Urgent", "summary": "urgent", "classification": "urgent", "status": "open", "requested_steward_action": "review"},
    ]}
    monkeypatch.setattr("estate.core.steward_annunciator.aggregate_attention", lambda *args, **kwargs: payload)
    state = present_attention(tmp_path, presenter=Recorder())
    assert state["severity"] == "urgent" and state["severity_rank"] == 0
