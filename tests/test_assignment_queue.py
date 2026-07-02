import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from estate.core.assignment_queue import generate_assignment_queue, format_assignment_queue_markdown


def write_text(root, rel, text):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def write_json(root, rel, payload):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_queue_generation_writes_json_and_markdown(tmp_path):
    write_text(tmp_path, "collaboration/work_packages/pending/WP-0100_SERIES_example.md", "# WP-0100\n\n## Mode\nSERIES.\n\nOwner: codex\n")

    queue = generate_assignment_queue(tmp_path)

    assert queue["summary"]["work_package_count"] == 1
    assert (tmp_path / "runtime/work_packages/assignment_queue.json").exists()
    assert (tmp_path / "operations/work_packages/assignment_queue.md").exists()


def test_dependency_listing(tmp_path):
    write_text(tmp_path, "collaboration/work_packages/pending/WP-0101_SERIES_deps.md", "# WP-0101\n\nOwner: codex\n\n## Dependencies\n- WP-0100\n- CAP-1\n")

    queue = generate_assignment_queue(tmp_path, write=False)

    entry = queue["work_packages"][0]
    assert entry["dependencies"] == ["WP-0100", "CAP-1"]


def test_blocked_entries(tmp_path):
    write_text(tmp_path, "collaboration/work_packages/pending/WP-0102_SERIES_blocked.md", "# WP-0102\n\nOwner: codex\n\n## Blockers\n- Waiting for review\n")

    queue = generate_assignment_queue(tmp_path, write=False)

    assert queue["work_packages"][0]["state"] == "blocked"
    assert queue["summary"]["blocked_count"] == 1


def test_missing_owner_warning(tmp_path):
    write_text(tmp_path, "collaboration/work_packages/pending/WP-0103_SERIES_no_owner.md", "# WP-0103\n")

    queue = generate_assignment_queue(tmp_path, write=False)

    assert queue["work_packages"][0]["owner"] == "unassigned"
    assert queue["warnings"][0]["type"] == "missing_owner"


def test_completed_records_mark_state_completed(tmp_path):
    write_text(tmp_path, "collaboration/work_packages/pending/WP-0104_SERIES_done.md", "# WP-0104\n\nOwner: codex\n")
    write_json(tmp_path, "collaboration/work_packages/completions/WP-0104_codex_done.json", {"work_package_id": "WP-0104", "codex_status": "done"})

    queue = generate_assignment_queue(tmp_path, write=False)

    assert queue["work_packages"][0]["state"] == "completed"


def test_markdown_output_contains_queue_table(tmp_path):
    write_text(tmp_path, "collaboration/work_packages/pending/WP-0105_SERIES_md.md", "# WP-0105\n\nOwner: codex\n")
    queue = generate_assignment_queue(tmp_path, write=False)

    markdown = format_assignment_queue_markdown(queue)

    assert markdown.startswith("# Estate Assignment Queue")
    assert "| Work Package | Mode | Owner | State | Dependencies | Blockers | Next Action |" in markdown
    assert "[WP-0105]" in markdown


def test_assignment_queue_cli_json(tmp_path):
    write_text(tmp_path, "collaboration/work_packages/pending/WP-0106_SERIES_cli.md", "# WP-0106\n\nOwner: codex\n")

    result = subprocess.run(
        [sys.executable, "-m", "estate.cli.main", "assignment-queue", "--json"],
        cwd=tmp_path,
        env={"PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")},
        capture_output=True,
        text=True,
        check=True,
    )

    payload = json.loads(result.stdout)
    assert payload["work_packages"][0]["work_package_id"] == "WP-0106"
