import json
import subprocess
import sys

from estate.core.helen_duty import run_helen_duty


def write_json(root, rel, payload):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def seed_identity(root):
    write_json(root, "data/registry/residents.json", [{"id": "RES-000002", "name": "Helen", "role": "Onboarding coordinator"}])
    write_json(root, "data/registry/personnel.json", [{"resident_id": "RES-000002", "display_name": "Helen", "mailbox_id": 8}])
    write_json(root, "data/registry/mailboxes.json", [{"mailbox_id": 8, "display_name": "Helen Personal Mailbox"}])


def test_helen_duty_updates_presence_and_records_sources(tmp_path):
    seed_identity(tmp_path)
    write_json(tmp_path, "runtime/onboarding/status.json", {"status": "active", "items": [{"id": "ONB-1"}]})

    payload = run_helen_duty(tmp_path)

    assert payload["resident"] == "Helen"
    assert payload["duty_state"] == "working"
    assert payload["duty_summary"]["needs_steward"] is False
    assert payload["presence"]["presence_state"] == "working"
    assert payload["presence"]["autonomous_execution"] is False
    assert any(src["path"] == "runtime/onboarding/status.json" for src in payload["source_artifact_references"])
    assert (tmp_path / "runtime/helen/duty_state.json").is_file()
    assert (tmp_path / "runtime/helen/duty_runs.jsonl").is_file()


def test_helen_duty_degrades_when_identity_artifacts_missing(tmp_path):
    payload = run_helen_duty(tmp_path)

    assert payload["duty_state"] == "degraded"
    assert payload["duty_summary"]["needs_steward"] is False
    assert any(src["required"] and src["status"] == "missing" for src in payload["source_artifact_references"])


def test_helen_duty_sets_steward_attention_from_local_onboarding_evidence(tmp_path):
    seed_identity(tmp_path)
    write_json(tmp_path, "runtime/onboarding/status.json", {"status": "blocked", "blockers": [{"id": "missing_packet"}]})

    payload = run_helen_duty(tmp_path)

    assert payload["duty_state"] == "waiting_for_steward"
    assert payload["duty_summary"]["needs_steward"] is True
    assert payload["duty_summary"]["steward_attention_items"][0]["type"] == "onboarding_blocker"


def test_helen_duty_preserves_authority_boundaries(tmp_path):
    seed_identity(tmp_path)
    payload = run_helen_duty(tmp_path)

    joined = " ".join(payload["authority_limitations"])
    assert "may not authorize personnel changes" in joined
    assert "may not execute" in joined


def test_helen_duty_cli_json(tmp_path, monkeypatch):
    seed_identity(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = subprocess.run(
        [sys.executable, "-m", "estate.cli.main", "helen-duty", "--json"],
        check=True,
        capture_output=True,
        text=True,
        env={"PYTHONPATH": str(__import__('pathlib').Path(__file__).resolve().parents[1] / "src")},
    )
    payload = json.loads(result.stdout)
    assert payload["resident"] == "Helen"
    assert payload["runtime_artifacts"]["duty_state"] == "runtime/helen/duty_state.json"
