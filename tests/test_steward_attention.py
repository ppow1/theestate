import json
from pathlib import Path

from estate.core.steward_attention import aggregate_attention, create_briefing, record_action


def write(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def seed(tmp_path: Path):
    write(tmp_path/"data/registry/residents.json", [{"id":"RES-1","name":"Alfred","role":"Chief of Staff","office":"Administration"}])
    write(tmp_path/"data/registry/personnel.json", [{"resident_id":"RES-1","display_name":"Alfred","mailbox_id":"alfred","current_office":"Administration"}])
    write(tmp_path/"runtime/residents/presence.json", {"residents":[{"resident_id":"RES-1","presence_state":"working","last_heartbeat":"2026-07-10T00:00:00+00:00"}]})
    write(tmp_path/"runtime/residents/task_status.json", {"residents":[{"resident_id":"RES-1","current_task":"waiting for launch approval","waiting_on":"steward","next_checkpoint":"2026-07-11T00:00:00+00:00","source_last_updated":"2026-07-10T00:00:00+00:00"}]})
    (tmp_path/"collaboration/work_packages/pending").mkdir(parents=True)
    (tmp_path/"collaboration/work_packages/pending/WP-9999_Test.md").write_text("# Test", encoding="utf-8")
    write(tmp_path/"collaboration/messages/msg1.json", {"id":"msg1","created_at":"2026-07-10T00:00:00+00:00","destination":"mailbox.alfred","priority":"normal","payload":{"title":"FYI","summary":"routine update"}})


def test_prioritization_batching_and_decision_split(tmp_path):
    seed(tmp_path)
    briefing = create_briefing("morning", tmp_path)
    assert briefing["steward_must_decide"]
    assert briefing["summary"]["must_decide"] >= 2
    assert briefing["routine_batch"]
    classes = [i["classification"] for i in briefing["steward_must_decide"] + briefing["steward_should_know"]]
    assert classes[0] == "decision_required"


def test_deduplication_collapses_repeated_mail_signal(tmp_path):
    seed(tmp_path)
    write(tmp_path/"collaboration/messages/msg1-copy.json", {"id":"msg1","created_at":"2026-07-10T00:01:00+00:00","destination":"mailbox.alfred","priority":"urgent","payload":{"title":"FYI","summary":"repeat"}})
    agg = aggregate_attention(tmp_path)
    mail = [i for i in agg["items"] if i["dedupe_key"] == "mail:msg1"]
    assert len(mail) == 1
    assert len(mail[0]["source_links"]) == 2


def test_stale_items_and_action_persistence(tmp_path):
    seed(tmp_path)
    agg = aggregate_attention(tmp_path)
    item = next(i for i in agg["items"] if i["must_decide"])
    action = record_action(item["id"], "acknowledge", actor="steward", root=tmp_path, note="seen")
    refreshed = aggregate_attention(tmp_path)
    updated = next(i for i in refreshed["items"] if i["id"] == item["id"])
    assert action["transport"] == "Office action transport"
    assert updated["status"] == "acknowledged"
