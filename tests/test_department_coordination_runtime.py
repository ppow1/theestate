import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from estate.core.department_coordination import DepartmentAuthority, DepartmentCoordination, DepartmentDependency, DepartmentHandoff, DepartmentRequest
from estate.core.department_coordination_runtime import EVENTS_FILE, STATUS_FILE, DepartmentCoordinationRuntime


def sample_coordination():
    return DepartmentCoordination.create(
        coordination_id="coord-runtime",
        campaign_id="camp-runtime",
        title="Campaign department coordination",
        authority=DepartmentAuthority(
            approved_by="Steward",
            approved_at="2026-07-10T00:00:00Z",
            operations_manager="Operations Manager",
            allowed_departments=["Engineering", "Character Architecture", "Workforce"],
        ),
        requests=[
            DepartmentRequest.create(request_id="eng", department="Engineering", title="Build", requested_by="Operations Manager", commitment="Implementation receipt", execution_provider="dispatch"),
            DepartmentRequest.create(request_id="char", department="Character Architecture", title="Review", requested_by="Operations Manager", commitment="Boundary review", dependencies=[DepartmentDependency("dep-eng", "eng", "Engineering first")]),
            DepartmentRequest.create(request_id="workforce", department="Workforce", title="Staffing readiness", requested_by="Operations Manager", commitment="Readiness acknowledgement"),
        ],
    )


def test_campaign_requests_multiple_departments_and_tracks_acknowledgements(tmp_path):
    runtime = DepartmentCoordinationRuntime(tmp_path)
    runtime.register(sample_coordination())

    runtime.acknowledge("coord-runtime", "eng", acknowledged_by="Engineering Lead")
    runtime.acknowledge("coord-runtime", "workforce", acknowledged_by="Helen")

    engineering = runtime.department_view("Engineering")
    workforce = runtime.department_view("Workforce")

    assert engineering["inbox"][0]["request"]["acknowledgement_state"] == "Acknowledged"
    assert workforce["inbox"][0]["request"]["acknowledged_by"] == "Helen"
    assert (tmp_path / EVENTS_FILE).is_file()
    assert (tmp_path / "runtime" / "collaboration" / "events" / "events.jsonl").is_file()


def test_dependencies_block_and_release_correctly(tmp_path):
    runtime = DepartmentCoordinationRuntime(tmp_path)
    runtime.register(sample_coordination())
    runtime.acknowledge("coord-runtime", "char", acknowledged_by="Character Architect")

    before = runtime.sequence_ready_work("coord-runtime")
    assert {item["request_id"] for item in before["blocked"]} == {"char"}

    runtime.acknowledge("coord-runtime", "eng", acknowledged_by="Engineering Lead")
    runtime.complete_request("coord-runtime", "eng", ["runtime/dispatch/eng-receipt.json"])
    runtime.release_dependency("coord-runtime", "char", "dep-eng")
    after = runtime.sequence_ready_work("coord-runtime", ["char"])

    assert after["sequenced"][0]["request_id"] == "char"
    status = json.loads((tmp_path / STATUS_FILE).read_text(encoding="utf-8"))
    assert status["coordinations"][0]["requests"][1]["state"] == "In Progress"


def test_operations_can_sequence_routine_work_but_boundaries_and_escalations_remain(tmp_path):
    runtime = DepartmentCoordinationRuntime(tmp_path)
    runtime.register(sample_coordination())
    runtime.acknowledge("coord-runtime", "eng", acknowledged_by="Engineering Lead")

    with pytest.raises(PermissionError):
        runtime.sequence_ready_work("coord-runtime", actor="Steward Relay")

    result = runtime.sequence_ready_work("coord-runtime", ["eng"])
    assert result["sequenced"][0]["execution_provider"] == "dispatch"

    runtime.deliver_handoff("coord-runtime", "eng", DepartmentHandoff("h-eng-char", "Engineering", "Character Architecture", "Implementation context", evidence=["runtime/dispatch/eng-receipt.json"]))
    view = runtime.department_view("Engineering")
    assert view["outbox"][0]["handoff"]["state"] == "Delivered"

    escalation = runtime.escalate_unresolved("coord-runtime", "Authority conflict between departments")
    assert escalation["action_type"] == "escalate"
    assert "Steward/Traffic Controller" in escalation["safe_summary"]
