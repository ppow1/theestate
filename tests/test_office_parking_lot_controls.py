import shutil
from pathlib import Path

from estate.core.office_command_surface import execute_office_action
from estate.core.office_parking_lot_controls import filter_items
from estate.core.steward_command_center import generate_command_center, render_command_center_html
from estate.core.work_package_validation import get_validation_recipe


def seed(tmp_path: Path):
    src = Path.cwd()
    for rel in ["operations/boards/parking_lot.md", "operations/boards/roadmap.md"]:
        dest = tmp_path / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src / rel, dest)


def ids(text):
    lines = [l for l in text.splitlines() if l.startswith("| PL-")]
    return [l.split("|")[1].strip() for l in lines]


def test_create_edit_priority_owner_accept_archive_restore_and_filter(tmp_path):
    seed(tmp_path)
    r = execute_office_action("parking_lot.control", root=tmp_path, planning_action="create", idea="Test idea", category="QA", priority="High", owner="Tester", notes="Promote when green")
    assert r["outcome"] == "completed"
    item_id = r["steward_message"].split()[-1]
    assert "Test idea" in (tmp_path / "operations/boards/parking_lot.md").read_text()

    r = execute_office_action("parking_lot.control", root=tmp_path, planning_action="edit", item_id=item_id, idea="Edited idea", owner="Owner 2")
    assert r["outcome"] == "completed"
    r = execute_office_action("parking_lot.control", root=tmp_path, planning_action="set_priority", item_id=item_id, priority="Strategic")
    assert r["outcome"] == "completed"
    for action, status in [("accept", "Promoted"), ("archive", "Archived"), ("restore", "Captured")]:
        r = execute_office_action("parking_lot.control", root=tmp_path, planning_action=action, item_id=item_id)
        assert r["outcome"] == "completed"
        assert status in (tmp_path / "operations/boards/parking_lot.md").read_text()

    visible = filter_items(root=tmp_path, surface="parking", query="Edited", priority="Strategic", owner="Owner 2")
    assert visible.outcome == "completed"
    assert [x["ID"] for x in visible.data["visible_items"]] == [item_id]


def test_move_up_down_reorder_reload_and_undo(tmp_path):
    seed(tmp_path)
    before = ids((tmp_path / "operations/boards/parking_lot.md").read_text())
    target = before[1]
    assert execute_office_action("parking_lot.control", root=tmp_path, planning_action="move_up", item_id=target)["outcome"] == "completed"
    moved = ids((tmp_path / "operations/boards/parking_lot.md").read_text())
    assert moved[0] == target
    html = render_command_center_html(generate_command_center(root=tmp_path, write=False))
    assert html.find(target) < html.find(before[0])

    assert execute_office_action("planning.undo_last_local_change", root=tmp_path)["outcome"] == "completed"
    assert ids((tmp_path / "operations/boards/parking_lot.md").read_text())[:2] == before[:2]

    order = before[2:3] + before[:2] + before[3:]
    assert execute_office_action("parking_lot.control", root=tmp_path, planning_action="reorder", order=order)["outcome"] == "completed"
    assert ids((tmp_path / "operations/boards/parking_lot.md").read_text())[:3] == order[:3]
    assert ids((tmp_path / "operations/boards/parking_lot.md").read_text())[:3] == order[:3]


def test_promote_canonical_once_and_invalid_blocked(tmp_path, monkeypatch):
    seed(tmp_path)
    calls = []
    from estate.core import office_parking_lot_controls as mod
    original = mod.OperationsControlRuntime.record_decision
    def wrapped(self, decision):
        calls.append(decision)
        return original(self, decision)
    monkeypatch.setattr(mod.OperationsControlRuntime, "record_decision", wrapped)
    assert execute_office_action("parking_lot.control", root=tmp_path, planning_action="promote", item_id="PL-0001", destination="operations_control")["outcome"] == "completed"
    assert len(calls) == 1
    assert execute_office_action("parking_lot.control", root=tmp_path, planning_action="promote", item_id="PL-0002", destination="new_queue")["outcome"] == "blocked"


def test_roadmap_controls_and_rendered_controls(tmp_path):
    seed(tmp_path)
    assert execute_office_action("roadmap.control", root=tmp_path, planning_action="create", capability="QA Capability", milestone="M1", status="Planned")["outcome"] == "completed"
    assert execute_office_action("roadmap.control", root=tmp_path, planning_action="move_up", item_id="QA Capability")["outcome"] == "completed"
    assert execute_office_action("roadmap.control", root=tmp_path, planning_action="set_priority", item_id="QA Capability", priority="Active")["outcome"] == "completed"
    html = render_command_center_html(generate_command_center(root=tmp_path, write=False))
    assert "parking_lot.control" in html
    assert "roadmap.control" in html
    assert "Move up" in html and "Archive" in html


def test_wp_0513_recipe_registered():
    assert get_validation_recipe("WP-0513") is not None
