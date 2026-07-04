import json
import subprocess
import sys
from pathlib import Path

from estate.core.resident_authority import check_authority, list_authority
from estate.core.alfred_duty import run_alfred_duty
from estate.core.helen_duty import run_helen_duty
from estate.core.resident_conversation_sessions import create_session


def test_alfred_allowed_and_denied_actions_are_explicit(tmp_path):
    allowed = check_authority("Alfred", "summarize", target="operations/alfred/duty_summary.md", root=tmp_path)
    denied = check_authority("Alfred", "execute-work-package", target="WP-0110", root=tmp_path)
    assert allowed["allowed"] is True
    assert allowed["authority_classification"] == "non_authoritative"
    assert denied["decision"] == "denied"
    assert denied["allowed"] is False
    assert "execute" in denied["reason"]
    assert (tmp_path / "runtime/residents/authority_decisions.jsonl").is_file()


def test_helen_personnel_boundary_and_unknown_action_safe_default(tmp_path):
    summarize = check_authority("Helen", "summarize", root=tmp_path)
    personnel = check_authority("Helen", "modify-personnel", target="data/registry/personnel.json", root=tmp_path)
    unknown = check_authority("Helen", "invent-new-power", root=tmp_path)
    assert summarize["allowed"] is True
    assert personnel["decision"] == "denied"
    assert personnel["authority_classification"] == "personnel_authority"
    assert unknown["decision"] == "denied"
    assert "Unknown action category" in unknown["reason"]


def test_list_authority_includes_explicit_boundaries():
    payload = list_authority("Alfred")
    alfred = payload["resident_boundaries"]["alfred"]
    assert "summarize" in alfred["allowed"]
    assert "approve-merge-work" in alfred["denied"]
    assert payload["default_unknown_action"] == "denied"


def test_cli_json_output_is_valid(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    env = {"PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")}
    result = subprocess.run([sys.executable, "-m", "estate.cli.main", "resident-authority", "check", "--resident", "Alfred", "--action", "summarize", "--json"], env=env, text=True, capture_output=True, check=True)
    payload = json.loads(result.stdout)
    assert payload["resident"] == "Alfred"
    assert payload["allowed"] is True


def test_duty_runners_and_conversations_consume_boundary(tmp_path):
    (tmp_path / "data/registry").mkdir(parents=True)
    (tmp_path / "data/registry/residents.json").write_text(json.dumps([{"id": "RES-1", "name": "Alfred"}, {"id": "RES-2", "name": "Helen"}]), encoding="utf-8")
    (tmp_path / "data/registry/personnel.json").write_text(json.dumps([{"resident_id": "RES-1", "display_name": "Alfred", "mailbox_id": 7}, {"resident_id": "RES-2", "display_name": "Helen", "mailbox_id": 8}]), encoding="utf-8")
    assert run_alfred_duty(tmp_path)["authority_boundary"]["execute_work_package"]["decision"] == "denied"
    assert run_helen_duty(tmp_path)["authority_boundary"]["summarize"]["allowed"] is True
    session = create_session(tmp_path, resident="Alfred", outcome="informational", action="execute-work-package")
    assert session["authority_boundary"]["decision"]["decision"] == "denied"
