import json
from pathlib import Path


def actions():
    return json.loads(Path("collaboration/workstreams/WP-0202/proposed/action_metadata.json").read_text())


def test_all_work_package_controls_are_non_executing():
    for action in actions():
        assert action["target_tab"] == "work-packages"
        assert action["does_not_execute_pending_work_packages"]
        assert action["command_hook_or_handler_reference"] != "execute_pending_work_package"


def test_copy_commands_are_copy_only():
    for action in actions():
        if "copy" in action["action_id"]:
            assert action["command_hook_or_handler_reference"] == "copy-only"
            assert action["confirmation_requirement"] == "none"


def test_review_and_batch_are_authority_gated_not_approval_or_execution():
    gated = {a["action_id"]: a for a in actions() if a["authority_class"] == "authority_gated_institutional_action"}
    assert "work_packages.request_ca_review" in gated
    assert "work_packages.prepare_batch_manifest" in gated
    assert "does not mark review complete" in gated["work_packages.request_ca_review"]["description"]
    assert "does not submit or execute" in gated["work_packages.prepare_batch_manifest"]["description"]
