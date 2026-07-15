from estate.core.openwebui_engineering_workflow import detect_engineering_assignment_command
from estate.core.resident_gateway import chat_completion


def test_detects_explicit_metadata_command():
    command = detect_engineering_assignment_command(
        {"metadata": {"estate_command": "initiate_engineering_assignment", "engineering_objective": "Repair the dashboard."}},
        "Please do it.",
    )
    assert command["objective"] == "Repair the dashboard."
    assert command["source"] == "metadata"


def test_openwebui_chat_initiates_existing_helen_grace_dispatch_workflow(tmp_path):
    code, body = chat_completion(
        {
            "model": "estate/grace",
            "messages": [{"role": "user", "content": "Initiate Engineering Department assignment: add a validation smoke test."}],
            "metadata": {"session_id": "owui-eng-1"},
        },
        root=tmp_path,
    )

    assert code == 200
    workflow = body["estate"]["engineering_assignment"]
    assert workflow["second_execution_system_created"] is False
    assert workflow["provider_execution_performed"] is False
    assert workflow["helen_request"]["request_type"] == "staffing_request"
    assert workflow["helen_assessment"]["assessor"] == "Helen"
    assert workflow["grace_action"]["state"] == "dispatch_requested"
    assert workflow["grace_action"]["dispatch_handoff_request"]["provider_execution_must_remain_behind_dispatch"] is True
    assert (tmp_path / "runtime/workforce_development/status/latest.json").exists()
    assert (tmp_path / "runtime/operations/grace/status/latest.json").exists()
    assert (tmp_path / "runtime/execution_dispatch/queue.json").exists()
    assert "No second execution system" in body["choices"][0]["message"]["content"]
