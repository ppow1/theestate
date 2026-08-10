"""Safe, offline annunciator demonstration; no real audio is emitted."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from estate.core.steward_annunciator import present_attention
from estate.core.steward_attention import record_action


class DemoPresenter:
    def __init__(self): self.calls = []
    def announce(self, item): self.calls.append({"item_id": item["id"], "message": item["summary"]})


def main():
    with tempfile.TemporaryDirectory(prefix="estate-annunciator-demo-") as directory:
        root = Path(directory)
        registry = root / "data/registry/residents.json"
        registry.parent.mkdir(parents=True)
        registry.write_text(json.dumps([{"id": "RES-5", "name": "Project 5", "role": "Project"}]), encoding="utf-8")
        task = root / "runtime/residents/task_status.json"
        task.parent.mkdir(parents=True)
        task.write_text(json.dumps({"residents": [{"resident_id": "RES-5", "resident_name": "Project 5", "current_task": "waiting for Steward input", "waiting_on": "steward"}]}), encoding="utf-8")
        speaker = DemoPresenter()
        first = present_attention(root, presenter=speaker)
        second = present_attention(root, presenter=speaker)
        record_action(first["active_item_ids"][0], "acknowledge", root=root)
        cleared = present_attention(root, presenter=speaker)
        print(json.dumps({"demo_root": str(root), "presentations": speaker.calls, "first_active": first["active"], "second_new_item_count": second["last_run"]["new_item_count"], "cleared_active": cleared["active"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
