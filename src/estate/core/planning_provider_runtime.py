from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from estate.core.paths import ESTATE_ROOT
from estate.core.planning_provider import PlanningProviderRequest, PlanningProviderResponse

RUNTIME_RELATIVE_ROOT = Path("runtime/planning_provider")


def _parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class PlanningProviderRuntimeWriter:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or ESTATE_ROOT
        self.runtime_root = self.root / RUNTIME_RELATIVE_ROOT
        self.requests_dir = self.runtime_root / "requests"
        self.results_dir = self.runtime_root / "results"
        self.events_dir = self.runtime_root / "events"
        self.status_dir = self.runtime_root / "status"

    def ensure_dirs(self) -> None:
        for path in [self.requests_dir, self.results_dir, self.events_dir, self.status_dir]:
            path.mkdir(parents=True, exist_ok=True)

    def write_all(self, request: PlanningProviderRequest, response: PlanningProviderResponse) -> dict[str, str]:
        self.ensure_dirs()
        req_path = self.requests_dir / f"{request.request_id}.json"
        res_path = self.results_dir / f"{request.request_id}.json"
        events_path = self.events_dir / f"{request.request_id}.jsonl"
        latest_path = self.status_dir / "latest.json"
        req_path.write_text(json.dumps(request.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        res_path.write_text(json.dumps(response.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        events_path.write_text("".join(json.dumps(event, sort_keys=True) + "\n" for event in response.events), encoding="utf-8")
        latest = self.latest_status_payload(request, response)
        latest_path.write_text(json.dumps(latest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return {"request": str(req_path), "result": str(res_path), "events": str(events_path), "latest_status": str(latest_path)}

    def latest_status_payload(self, request: PlanningProviderRequest, response: PlanningProviderResponse) -> dict[str, Any]:
        elapsed = max(0.0, (_parse_ts(response.finished_at) - _parse_ts(response.started_at)).total_seconds())
        current_state = "Completed" if response.status == "completed" else "Blocked" if response.status == "blocked" else "Failed" if response.status == "failed" else "Planning"
        if response.events:
            current_state = response.events[-1].get("state", current_state)
        return {
            "request_id": request.request_id,
            "provider_id": response.provider_id,
            "worker_id": request.worker_id,
            "current_state": current_state,
            "status": response.status,
            "planning_intent": request.planning_intent,
            "started_at": response.started_at,
            "updated_at": response.finished_at,
            "elapsed_seconds": elapsed,
            "classification": response.classification,
            "validation_status": response.validation_status,
            "requires_review": response.requires_review,
            "summary": response.summary,
        }
