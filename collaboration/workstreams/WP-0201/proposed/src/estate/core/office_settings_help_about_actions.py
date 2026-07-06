"""Staged Settings/Help/About action definitions for WP-0201. Proposed only."""
from pathlib import Path
import json


def load_action_metadata(path: str | Path):
    return json.loads(Path(path).read_text())


def assert_local_only(actions):
    return all(action.get("local_only_no_upload_guarantee") is True for action in actions)
