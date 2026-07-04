import json
from pathlib import Path

from estate.core.alfred_duty import run_alfred_duty


def write_json(root: Path, rel: str, data):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def seed_identity(root: Path):
    write_json(root, "data/registry/residents.json", [{"id": "RES-000001", "name": "Alfred", "role": "Chief of staff"}])
    write_json(root, "data/registry/personnel.json", [{"resident_id": "RES-000001", "display_name": "Alfred", "mailbox_id": 7}])


def test_alfred_duty_updates_presence_and_records_sources(tmp_path):
    seed_identity(tmp_path)
    write_json(tmp_path, "runtime/steward/decision_queue.json", {"decisions": []})

    payload = run_alfred_duty(tmp_path)

    assert payload["resident"] == "Alfred"
    assert payload["duty_state"] == "working"
    assert payload["duty_summary"]["needs_steward"] is False
    assert any(src["path"] == "runtime/steward/decision_queue.json" for src in payload["source_artifact_references"])
    presence = json.loads((tmp_path / "runtime/residents/presence.json").read_text())
    assert presence["residents"][0]["presence_state"] == "working"
    assert (tmp_path / "runtime/alfred/duty_state.json").is_file()
    assert (tmp_path / "runtime/alfred/duty_runs.jsonl").is_file()


def test_alfred_duty_degrades_when_identity_artifacts_missing(tmp_path):
    payload = run_alfred_duty(tmp_path)

    assert payload["duty_state"] == "degraded"
    assert payload["duty_summary"]["needs_steward"] is False
    missing_required = [s for s in payload["source_artifact_references"] if s["required"] and s["status"] == "missing"]
    assert missing_required


def test_alfred_duty_sets_steward_attention_from_local_evidence(tmp_path):
    seed_identity(tmp_path)
    write_json(tmp_path, "runtime/steward/decision_queue.json", {"decisions": [{"id": "D-1", "title": "Needs Steward"}]})

    payload = run_alfred_duty(tmp_path)

    assert payload["duty_state"] == "waiting_for_steward"
    assert payload["duty_summary"]["needs_steward"] is True
    assert payload["duty_summary"]["steward_attention_items"][0]["type"] == "steward_decisions_present"


def test_alfred_duty_preserves_authority_boundaries(tmp_path):
    seed_identity(tmp_path)

    payload = run_alfred_duty(tmp_path)

    text = " ".join(payload["authority_limitations"])
    assert "may not authorize" in text
    assert "may not execute" in text
    assert payload["presence"]["autonomous_execution"] is False
