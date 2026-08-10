import json

from estate.core.steward_annunciator import present_attention, run_live_test, watch_attention
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


def test_live_test_boundary_is_mockable_without_audio(monkeypatch):
    class FakePresenter:
        def ding(self): return {"api": "mock-ding"}
        def speak(self, text): return {"api": "mock-tts", "text": text}
    monkeypatch.setattr("estate.core.steward_annunciator.WindowsPresenter", FakePresenter)
    result = run_live_test()
    assert result["success"] is True
    assert result["ding"]["api"] == "mock-ding"
    assert result["tts"]["api"] == "mock-tts"


def attention_item(item_id, classification="decision_required", status="open"):
    return {"id": item_id, "title": item_id, "summary": item_id, "classification": classification, "status": status, "requested_steward_action": "review"}


def attention_payload(items):
    return {"items": items}


def test_watcher_startup_baseline_suppresses_historical_backlog(tmp_path, monkeypatch):
    monkeypatch.setattr("estate.core.steward_annunciator.aggregate_attention", lambda *args, **kwargs: attention_payload([attention_item(f"old-{i}") for i in range(100)]))
    recorder = Recorder()

    result = watch_attention(tmp_path, interval_seconds=1, max_cycles=1, presenter=recorder)

    assert recorder.items == []
    assert result["cycles"][0]["presented_count"] == 0
    assert result["cycles"][0]["new_item_count"] == 0
    assert json.loads((tmp_path / "runtime/office/steward_annunciator.json").read_text())["baseline_established"] is True


def test_new_actionable_item_after_baseline_presents_once(tmp_path, monkeypatch):
    payloads = [attention_payload([attention_item("old")]), attention_payload([attention_item("old"), attention_item("new")]), attention_payload([attention_item("old"), attention_item("new")])]
    monkeypatch.setattr("estate.core.steward_annunciator.aggregate_attention", lambda *args, **kwargs: payloads.pop(0))
    recorder = Recorder()

    result = watch_attention(tmp_path, interval_seconds=1, max_cycles=2, presenter=recorder)

    assert recorder.items == ["new"]
    assert [cycle["presented_count"] for cycle in result["cycles"]] == [1, 0]


def test_same_item_on_repeated_polls_does_not_reannounce(tmp_path, monkeypatch):
    item = attention_item("same")
    monkeypatch.setattr("estate.core.steward_annunciator.aggregate_attention", lambda *args, **kwargs: attention_payload([item]))
    recorder = Recorder()

    result = watch_attention(tmp_path, interval_seconds=1, max_cycles=3, presenter=recorder)

    assert recorder.items == []
    assert all(cycle["presented_count"] == 0 for cycle in result["cycles"])


def test_timestamp_churn_does_not_reannounce(tmp_path, monkeypatch):
    first = {**attention_item("timestamped"), "timestamp": "2026-08-09T20:00:00+00:00"}
    second = {**attention_item("timestamped"), "timestamp": "2026-08-09T20:01:00+00:00"}
    payloads = [attention_payload([first]), attention_payload([second]), attention_payload([second])]
    monkeypatch.setattr("estate.core.steward_annunciator.aggregate_attention", lambda *args, **kwargs: payloads.pop(0))
    recorder = Recorder()

    result = watch_attention(tmp_path, interval_seconds=1, max_cycles=2, presenter=recorder)

    assert recorder.items == []
    assert all(cycle["presented_count"] == 0 for cycle in result["cycles"])


def test_watcher_restart_with_same_outstanding_item_does_not_replay(tmp_path, monkeypatch):
    monkeypatch.setattr("estate.core.steward_annunciator.aggregate_attention", lambda *args, **kwargs: attention_payload([attention_item("outstanding")]))
    first = Recorder(); second = Recorder()

    watch_attention(tmp_path, interval_seconds=1, max_cycles=1, presenter=first)
    watch_attention(tmp_path, interval_seconds=1, max_cycles=1, presenter=second)

    assert first.items == [] and second.items == []


def test_routine_item_never_uses_audio(tmp_path, monkeypatch):
    monkeypatch.setattr("estate.core.steward_annunciator.aggregate_attention", lambda *args, **kwargs: attention_payload([attention_item("routine", "routine")]))
    recorder = Recorder()

    watch_attention(tmp_path, interval_seconds=1, max_cycles=2, presenter=recorder)

    assert recorder.items == []


def test_meaningful_transition_into_decision_required_presents_once(tmp_path, monkeypatch):
    payloads = [attention_payload([attention_item("escalating", "attention_soon")]), attention_payload([attention_item("escalating", "decision_required")]), attention_payload([attention_item("escalating", "decision_required")])]
    monkeypatch.setattr("estate.core.steward_annunciator.aggregate_attention", lambda *args, **kwargs: payloads.pop(0))
    recorder = Recorder()

    result = watch_attention(tmp_path, interval_seconds=1, max_cycles=2, presenter=recorder)

    assert recorder.items == ["escalating"]
    assert result["cycles"][0]["presented_count"] == 1


def test_meaningful_transition_into_urgent_presents_once(tmp_path, monkeypatch):
    payloads = [attention_payload([attention_item("urgent-escalation", "attention_soon")]), attention_payload([attention_item("urgent-escalation", "urgent")]), attention_payload([attention_item("urgent-escalation", "urgent")])]
    monkeypatch.setattr("estate.core.steward_annunciator.aggregate_attention", lambda *args, **kwargs: payloads.pop(0))
    recorder = Recorder()

    result = watch_attention(tmp_path, interval_seconds=1, max_cycles=2, presenter=recorder)

    assert recorder.items == ["urgent-escalation"]
    assert result["cycles"][0]["presented_count"] == 1


def test_acknowledged_item_remains_quiet(tmp_path, monkeypatch):
    payloads = [attention_payload([attention_item("ack", "urgent")]), attention_payload([attention_item("ack", "urgent", "acknowledged")]), attention_payload([attention_item("ack", "urgent", "acknowledged")])]
    monkeypatch.setattr("estate.core.steward_annunciator.aggregate_attention", lambda *args, **kwargs: payloads.pop(0))
    recorder = Recorder()

    result = watch_attention(tmp_path, interval_seconds=1, max_cycles=2, presenter=recorder)

    assert recorder.items == []
    assert all(cycle["presented_count"] == 0 for cycle in result["cycles"])


def test_reopened_actionable_item_presents_once(tmp_path, monkeypatch):
    payloads = [attention_payload([attention_item("reopen", "urgent")]), attention_payload([]), attention_payload([attention_item("reopen", "urgent")])]
    monkeypatch.setattr("estate.core.steward_annunciator.aggregate_attention", lambda *args, **kwargs: payloads.pop(0))
    recorder = Recorder()

    result = watch_attention(tmp_path, interval_seconds=1, max_cycles=2, presenter=recorder)

    assert recorder.items == ["reopen"]
    assert result["cycles"][1]["presented_count"] == 1
