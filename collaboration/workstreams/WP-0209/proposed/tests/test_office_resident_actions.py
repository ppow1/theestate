"""Staged test plan for WP-0209; copy into active tests only during install handoff."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]

def test_all_actions_are_local_only_and_classified():
    actions = json.loads((ROOT / "collaboration/workstreams/WP-0209/proposed/action_metadata.json").read_text())
    assert actions
    assert all(a["local_only_no_upload_guarantee"] for a in actions)
    assert all(a["authority_class"] for a in actions)

def test_no_staged_action_claims_installed_runtime_status():
    manifest = json.loads((ROOT / "collaboration/workstreams/WP-0209/install_manifest.json").read_text())
    assert manifest["staged_work_is_installed"] is False
