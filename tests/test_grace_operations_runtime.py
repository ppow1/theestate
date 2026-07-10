import json

from estate.core.grace_operations_runtime import GraceObjective, GraceOperationsRuntime
from estate.core.office_operational_activity import load_office_operational_activity


def test_grace_sequences_ready_action_with_checkpoint_and_dispatch(tmp_path):
    runtime = GraceOperationsRuntime(tmp_path)
    objective = GraceObjective.create(
        requested_by="Steward",
        title="Complete approved work",
        summary="Convert approved work into governed next action.",
        work_package_id="WP-4006",
        owner="Operations",
        checkpoint="Chief Architect review before closure",
        dependencies=["WP-4005"],
    )

    action, paths = runtime.conduct_objective(objective, request_dispatch=True)

    assert action.state == "dispatch_requested"
    assert action.owner == "Operations"
    assert action.checkpoint == "Chief Architect review before closure"
    assert action.traffic_controller_request["action_type"] == "assign"
    assert action.dispatch_handoff_request["provider_execution_must_remain_behind_dispatch"] is True
    assert "dispatch_queue" in paths
    queue = json.loads((tmp_path / "runtime/execution_dispatch/queue.json").read_text())
    assert queue["items"][0]["provider_metadata"]["grace_action_id"] == action.action_id


def test_grace_escalates_blockers_without_dispatch_bypass(tmp_path):
    runtime = GraceOperationsRuntime(tmp_path)
    objective = GraceObjective.create(
        requested_by="Steward",
        title="Blocked movement",
        summary="Movement is blocked by missing approval.",
        work_package_id="WP-X",
        authority="requires_steward",
        blockers=["Traffic Controller authorization missing"],
    )

    action, paths = runtime.conduct_objective(objective, request_dispatch=True)

    assert action.state == "blocked"
    assert action.escalation["escalate_to"] == "Steward"
    assert action.traffic_controller_request["action_type"] == "hold"
    assert "escalation" in paths
    assert not (tmp_path / "runtime/execution_dispatch/queue.json").exists()


def test_grace_records_closure_as_reconciliation_not_acceptance(tmp_path):
    runtime = GraceOperationsRuntime(tmp_path)
    paths = runtime.close_objective("grace-obj-demo", reviewed_by="Chief Architect", result="Validated", accepted=True)
    closure = json.loads(open(paths["closure"], encoding="utf-8").read())
    assert closure["accepted"] is True
    assert "institutional acceptance remains" in closure["note"]


def test_office_activity_includes_grace_status(tmp_path):
    runtime = GraceOperationsRuntime(tmp_path)
    runtime.intake_objective(GraceObjective.create(requested_by="Steward", title="Surface Grace", summary="Show status."))

    surface = load_office_operational_activity(tmp_path)

    assert surface["grace_operations_status"]["available"] is True
    assert surface["grace_operations_status"]["role"] == "governed operational executive"
