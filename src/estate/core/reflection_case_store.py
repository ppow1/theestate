from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from estate.core.paths import ESTATE_ROOT
from estate.core.reflection_case_types import CASE_STATES, SCHEMA_VERSION


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class ReflectionCaseStore:
    def __init__(self, root: Path | None = None) -> None:
        self.root = (root or ESTATE_ROOT) / "operations" / "reflection_cases"

    def create(self, target: dict[str, Any], initiation: dict[str, Any]) -> dict[str, Any]:
        case_id = f"REF-{uuid.uuid4().hex[:12].upper()}"
        state = "reflection_authorized" if initiation["type"] == "direct" else "evaluation_requested"
        record = {
            "schema_version": SCHEMA_VERSION,
            "case_id": case_id,
            "state": state,
            "target": target,
            "initiation": initiation,
            "worker_artifacts": {},
            "history": [{"state": state, "at": _now(), "actor": initiation["source"]}],
        }
        self.save(record)
        return record

    def load(self, case_id: str) -> dict[str, Any]:
        return json.loads((self.root / f"{case_id}.json").read_text(encoding="utf-8"))

    def save(self, record: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        path = self.root / f"{record['case_id']}.json"
        path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def transition(self, case_id: str, state: str, actor: str, note: str = "") -> dict[str, Any]:
        if state not in CASE_STATES:
            raise ValueError(f"Unsupported reflection state: {state}")
        record = self.load(case_id)
        record["state"] = state
        record["history"].append({"state": state, "at": _now(), "actor": actor, "note": note})
        self.save(record)
        return record
