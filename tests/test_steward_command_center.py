import json
import sys
from pathlib import Path
from urllib.request import urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from estate.core.steward_command_center import generate_command_center, render_command_center_html, serve_command_center


def write_json(root, rel, payload):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def seed_inputs(root):
    write_json(root, "data/registry/residents.json", [
        {"id": "RES-000001", "name": "Alfred", "department": "Administration", "office": "Manager of Administration", "status": "Active", "role": "Coordinates the Estate."},
        {"id": "RES-000003", "name": "Helen", "department": "Human Resources", "office": "Manager of Human Resources", "status": "Active", "role": "Manages resident and worker assignment fit."},
    ])
    write_json(root, "data/registry/personnel.json", [{"employee_id": 6, "display_name": "Helen", "mailbox_id": 6, "resident_id": "RES-000003"}])
    write_json(root, "data/registry/mailboxes.json", [{"mailbox_id": 10100, "display_name": "Alfred Routing Intake", "owning_office": "Chief of Staff"}])
    write_json(root, "data/objects/RES-000001.json", {"id": "RES-000001", "name": "Alfred"})
    write_json(root, "data/objects/RES-000003.json", {"id": "RES-000003", "name": "Helen"})
    write_json(root, "collaboration/mailboxes/index.json", {"summary": {"message_count": 3}})
    (root / "operations/briefings").mkdir(parents=True, exist_ok=True)
    (root / "operations/briefings/morning_briefing.md").write_text("# Morning Briefing\n", encoding="utf-8")
    (root / "operations/work_packages").mkdir(parents=True, exist_ok=True)
    (root / "operations/work_packages/assignment_queue.md").write_text("# Assignment Queue\n", encoding="utf-8")
    write_json(root, "runtime/audit/latest.json", {"summary": {"failed": 0}})


def test_command_center_renders_all_initial_panels(tmp_path):
    seed_inputs(tmp_path)
    payload = generate_command_center(tmp_path)
    html = render_command_center_html(payload)

    for title in ["Alfred Resident Card", "Helen Resident Card", "Morning Briefing", "Steward Decision Queue", "Mailbox Summary", "Work Package Pipeline", "Validation Status"]:
        assert title in html
    assert (tmp_path / "runtime/steward/command_center.html").exists()


def test_command_center_degrades_gracefully_when_artifacts_are_missing(tmp_path):
    payload = generate_command_center(tmp_path, write=False)
    html = render_command_center_html(payload)

    assert payload["panels"]["alfred_resident_card"]["available"] is False
    assert "Supporting artifact is not available yet." in html
    assert "No pending Steward decisions were found" in html


def test_command_center_starts_local_http_server(tmp_path):
    seed_inputs(tmp_path)
    server = serve_command_center(host="127.0.0.1", port=0, root=tmp_path)
    try:
        host, port = server.server_address
        import threading
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        response = urlopen(f"http://{host}:{port}/", timeout=5)
        body = response.read().decode("utf-8")
        assert response.status == 200
        assert "Office of the Steward" in body
        assert "Mailbox Summary" in body
    finally:
        server.shutdown()
        server.server_close()


def test_command_center_cli_generates_json(tmp_path):
    import subprocess

    seed_inputs(tmp_path)
    result = subprocess.run(
        [sys.executable, "-m", "estate.cli.main", "steward-command-center", "--json"],
        cwd=tmp_path,
        env={"PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")},
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(result.stdout)
    assert payload["panels"]["alfred_resident_card"]["available"] is True
    assert (tmp_path / "runtime/steward/command_center.html").exists()
