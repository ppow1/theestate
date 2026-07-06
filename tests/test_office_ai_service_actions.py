"""Installed staged test plan for WP-0210; copy into active tests only during install handoff."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_all_actions_are_local_only_and_classified():
    actions = json.loads((ROOT / "collaboration/workstreams/WP-0210/proposed/action_metadata.json").read_text())
    assert actions
    assert all(a["local_only_no_upload_guarantee"] for a in actions)
    assert all(a["authority_class"] for a in actions)

def test_installed_module_claims_installed_runtime_status():
    module_path = ROOT / "src/estate/core/office_ai_service_actions.py"
    assert "STAGED_WORK_IS_INSTALLED = True" in module_path.read_text()
