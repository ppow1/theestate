import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from estate.core.resident_conversation_sessions import create_session, list_sessions, load_session
from estate.core.resident_conversations import build_resident_conversations_workspace


def write_json(root, rel, payload):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def seed_residents(root):
    write_json(root, "data/registry/residents.json", [
        {"id": "RES-000001", "name": "Alfred", "role": "Administration", "status": "Active"},
        {"id": "RES-000003", "name": "Helen", "role": "Human Resources", "status": "Active"},
    ])
    write_json(root, "data/registry/personnel.json", [])
    write_json(root, "data/registry/mailboxes.json", [])


def test_create_sessions_for_alfred_and_helen_with_audit_fields(tmp_path):
    alfred = create_session(tmp_path, resident="Alfred", source_artifacts=["operations/alfred/operational_briefing.md"], prompt="What changed?", response="Informational only.", outcome="work_package_candidate", canonical_links=["collaboration/work_packages/pending/WP-0109_SERIES_resident_conversation_session_and_audit_trail.md"])
    helen = create_session(tmp_path, resident="Helen", operator_note="Review onboarding source.", outcome="needs_steward")

    assert alfred["resident"] == "Alfred"
    assert alfred["created_at"] and alfred["updated_at"]
    assert alfred["participants"][0]["role"] == "operator"
    assert alfred["source_artifacts"] == ["operations/alfred/operational_briefing.md"]
    assert alfred["outcome"]["label"] == "work_package_candidate"
    assert alfred["outcome"]["authoritative"] is False
    assert "No Steward approval" in " ".join(alfred["authority_boundary"]["limitations"])
    assert load_session(alfred["session_id"], tmp_path)["session_id"] == alfred["session_id"]
    assert helen["resident"] == "Helen"


def test_list_sessions_degrades_gracefully_and_summarizes(tmp_path):
    missing = list_sessions(tmp_path)
    assert missing["sessions"] == []
    assert missing["warnings"][0]["type"] == "missing_session_store"

    session = create_session(tmp_path, resident="Alfred", outcome="no_action")
    listed = list_sessions(tmp_path, resident="Alfred")
    assert listed["sessions"][0]["session_id"] == session["session_id"]
    assert listed["sessions"][0]["authority_label"] == "non-authoritative conversation session"
    assert listed["sessions"][0]["authoritative"] is False


def test_workspace_consumes_session_summaries(tmp_path):
    seed_residents(tmp_path)
    session = create_session(tmp_path, resident="Alfred", source_artifacts=["source.md"], outcome="validation_follow_up")
    workspace = build_resident_conversations_workspace(tmp_path, names=("Alfred", "Helen"))
    alfred = workspace["data"]["conversations"][0]
    helen = workspace["data"]["conversations"][1]
    assert alfred["recent_sessions"][0]["session_id"] == session["session_id"]
    assert alfred["recent_sessions"][0]["outcome_label"] == "validation_follow_up"
    assert "source.md" in alfred["source_artifacts"]
    assert helen["recent_sessions"] == []
    assert "Conversation is an interface surface only" in workspace["data"]["record_policy"]


def test_cli_json_output_valid(tmp_path):
    env = {"PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")}
    result = subprocess.run([
        sys.executable, "-m", "estate.cli.main", "resident-conversation", "start", "--resident", "Alfred", "--source-artifact", "source.md", "--outcome", "informational", "--json"
    ], cwd=tmp_path, env=env, text=True, capture_output=True, check=True)
    payload = json.loads(result.stdout)
    assert payload["resident"] == "Alfred"
    listed = subprocess.run([sys.executable, "-m", "estate.cli.main", "resident-conversation", "list", "--json"], cwd=tmp_path, env=env, text=True, capture_output=True, check=True)
    assert json.loads(listed.stdout)["sessions"][0]["session_id"] == payload["session_id"]
