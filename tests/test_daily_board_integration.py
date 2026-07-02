import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from estate.core.daily_board_integration import (
    generate_daily_board_integration,
    parse_parking_lot,
    promotion_condition_status,
    format_daily_board_integration_markdown,
)


def write(root, rel, text):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def fixture(root):
    write(root, "operations/boards/parking_lot.md", """# Parking Lot

## Parking Lot Items

| ID | Idea | Category | Priority | Originator | Date Captured | Status | Target Milestone | Promotion Condition |
|---|---|---|---|---|---|---|---|---|
| PL-1 | Stable thing | Ops | High | A | 2026-07-01 | Captured | Stable board | Board is stable |
| PL-2 | Later thing | Ops | Normal | A | 2026-07-01 | Captured | Future | After workflow matures |
""")
    write(root, "operations/boards/active_work.md", """# Active Work Board

## Active Work

| ID | Effort | Owner | Status | Current Milestone | Dependency | Next Action |
|---|---|---|---|---|---|---|
| AW-1 | Ops | Alfred | Active | v1 | None | Review |

## Waiting

| ID | Effort | Waiting On | Owner | Resume Condition |
|---|---|---|---|---|
| AW-2 | Blocked | Input | Alfred | Input arrives |
""")
    write(root, "operations/boards/daily_board.md", """# Daily Task Board

## Today

| ID | Task | Owner | Status | Blocker | Review Required | Next Action |
|---|---|---|---|---|---|---|
| DT-1 | Task | Alfred | Active | None | Yes | Do it |

## Blocked

| ID | Item | Blocker | Owner | Escalation Needed |
|---|---|---|---|---|
| - | - | - | - | - |
""")
    write(root, "collaboration/work_packages/pending/WP-9999_TEST.md", "# WP-9999 Test Package\n")
    write(root, "collaboration/work_packages/completions/WP-9998_codex_done.json", json.dumps({
        "work_package_id": "WP-9998", "codex_status": "done", "ready_for_ca_review": True
    }))


def test_parse_parking_lot_items(tmp_path):
    fixture(tmp_path)
    warnings = []
    items = parse_parking_lot(tmp_path / "operations/boards/parking_lot.md", tmp_path, warnings)
    assert len(items) == 2
    assert items[0]["ID"] == "PL-1"
    assert warnings == []


def test_identifies_promotion_conditions_without_promoting():
    item = {"Promotion Condition": "Board is stable", "Target Milestone": "Stable board"}
    status = promotion_condition_status(item)
    assert status["classification"] == "ready_for_review"
    assert "promote" not in status


def test_lists_active_pending_completed_work_packages(tmp_path):
    fixture(tmp_path)
    report = generate_daily_board_integration(tmp_path, write=False)
    assert report["active_work"][0]["ID"] == "AW-1"
    assert report["pending_codex_queue"][0]["id"] == "WP-9999"
    assert report["completed_awaiting_review"][0]["id"] == "WP-9998"


def test_missing_artifact_warnings(tmp_path):
    report = generate_daily_board_integration(tmp_path, write=False)
    assert report["warnings"]
    assert any(w["type"] == "missing_optional_artifact" for w in report["warnings"])


def test_markdown_and_json_report_generation(tmp_path):
    fixture(tmp_path)
    report = generate_daily_board_integration(tmp_path)
    markdown = format_daily_board_integration_markdown(report)
    assert (tmp_path / "runtime/operations/daily_board_integration.json").exists()
    assert (tmp_path / "operations/boards/daily_board_integration.md").exists()
    assert markdown.startswith("# Daily Board Integration")
    assert "## Parking Lot Items Ready for Review" in markdown


def test_daily_board_cli_registration(tmp_path):
    fixture(tmp_path)
    result = subprocess.run(
        [sys.executable, "-m", "estate.cli.main", "daily-board", "--json"],
        cwd=tmp_path,
        env={"PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")},
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(result.stdout)
    assert payload["summary"]["pending_work_packages"] == 1
