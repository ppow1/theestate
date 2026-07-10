"""Pending post-merge audit request consumer with claim protection."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from estate.core.operational_targets_runtime import OperationalTargetRuntime
from estate.core.paths import ESTATE_ROOT
from estate.core.post_merge_validation_pipeline import PipelineConfig, PostMergeValidationPipeline, utc_now_iso

BASE = Path("runtime/post_merge_audit")
REQUESTS = BASE / "requests"
STATUS = BASE / "status"


def _root(root: Path | None = None) -> Path:
    return root or (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


class PostMergeAuditProcessor:
    def __init__(self, root: Path | None = None, *, workspace_root: Path | None = None, evidence_root: Path | None = None, validator=None, ollama_enabled: bool = False) -> None:
        self.root = _root(root)
        self.targets = OperationalTargetRuntime(self.root)
        self.pipeline = PostMergeValidationPipeline(PipelineConfig(self.root, workspace_root, evidence_root, ollama_enabled), validator=validator)

    @property
    def request_dir(self) -> Path:
        return self.root / REQUESTS

    def list_requests(self, state: str | None = None) -> list[dict[str, Any]]:
        if not self.request_dir.exists(): return []
        out = []
        for p in sorted(self.request_dir.glob("*.json")):
            d = _read_json(p); d.setdefault("state", d.get("status", "pending")); d["request_path"] = str(p)
            if state is None or d.get("state") == state: out.append(d)
        return out

    def claim_next(self) -> dict[str, Any] | None:
        for req in self.list_requests("pending"):
            p = Path(req["request_path"])
            current = _read_json(p)
            if current.get("state", current.get("status", "pending")) != "pending":
                continue
            current["state"] = "claimed"; current["claimed_at"] = utc_now_iso()
            _write_json(p, current)
            return {**current, "request_path": str(p)}
        return None

    def process_next(self) -> dict[str, Any]:
        req = self.claim_next()
        if not req:
            payload = {"processed": False, "reason": "no_pending_requests", "provider_execution_performed": False, "dispatch_execution_performed": False}
            self._write_status(payload); return payload
        return self._process_claimed(req)

    def process_all(self, max_count: int = 10) -> dict[str, Any]:
        results = []
        for _ in range(max_count):
            r = self.process_next();
            if not r.get("processed"): break
            results.append(r)
        payload = {"processed_count": len(results), "results": results, "provider_execution_performed": False, "dispatch_execution_performed": False}
        self._write_status(payload); return payload

    def demonstrate(self, work_package: str, pr: str | int | None = None) -> dict[str, Any]:
        req = {"audit_id": f"demo-{work_package.lower()}", "target_id": "estate", "work_package_id": work_package, "source_kind": "demonstration", "source_reference": "HEAD", "expected_files": [], "metadata": {"pr": pr}, "state": "pending"}
        self.request_dir.mkdir(parents=True, exist_ok=True); _write_json(self.request_dir / f"{req['audit_id']}.json", req)
        return self.process_next()

    def _process_claimed(self, req: dict[str, Any]) -> dict[str, Any]:
        p = Path(req["request_path"])
        try:
            req["state"] = "running_validation"; _write_json(p, {k:v for k,v in req.items() if k != "request_path"})
            target = self.targets.get(req["target_id"])
            verdict = self.pipeline.run(req, target)
            req.update({"state": verdict["state"], "validation_result": verdict.get("validation_status"), "production_ready": verdict.get("production_ready"), "receipt_status": verdict.get("receipt_status"), "workspace": verdict.get("workspace"), "ring2_paths": {"prompt": verdict.get("artifacts", {}).get("ring2_prompt")}, "verdict": verdict.get("verdict"), "verdict_path": verdict.get("verdict_path"), "warnings": verdict.get("warnings", []), "errors": verdict.get("errors", [])})
            _write_json(p, {k:v for k,v in req.items() if k != "request_path"})
            result = {"processed": True, "request": req, "verdict": verdict, "provider_execution_performed": False, "dispatch_execution_performed": False}
        except Exception as exc:
            req["state"] = "failed"; req.setdefault("errors", []).append(str(exc)); _write_json(p, {k:v for k,v in req.items() if k != "request_path"})
            result = {"processed": True, "request": req, "error": str(exc), "provider_execution_performed": False, "dispatch_execution_performed": False}
        self._write_status(result); return result

    def summary(self) -> dict[str, Any]:
        reqs = self.list_requests()
        latest = next((r for r in reversed(reqs) if r.get("state") in {"completed","blocked","ring2_required","failed"}), None)
        running = next((r for r in reqs if r.get("state") in {"claimed","running_validation","running_ring2"}), None)
        return {"automatic_validation_available": True, "pending_audit_requests": sum(1 for r in reqs if r.get("state") == "pending"), "running_audit_request": running, "latest_completed_audit": latest, "latest_validation_status": (latest or {}).get("validation_result"), "latest_production_ready": (latest or {}).get("production_ready"), "latest_ring2_status": ((latest or {}).get("ring2_paths") or {}).get("prompt"), "latest_verdict": (latest or {}).get("verdict"), "latest_verdict_artifact": (latest or {}).get("verdict_path"), "validation_workspace_health": "configured", "validation_evidence_root": str(self.pipeline.config.resolved_evidence_root()), "provider_execution_performed": False, "dispatch_execution_performed": False}

    def _write_status(self, payload: dict[str, Any]) -> None:
        status = {"generated_at": utc_now_iso(), "latest_result": payload, "summary": self.summary()}
        _write_json(self.root / STATUS / "latest.json", status); _write_json(self.root / STATUS / "summary.json", status["summary"])

def load_post_merge_audit_processor_status(root: Path | None = None) -> dict[str, Any]:
    processor = PostMergeAuditProcessor(root)
    latest = processor.root / STATUS / "latest.json"
    if latest.exists():
        return _read_json(latest)
    return {"generated_at": utc_now_iso(), "latest_result": None, "summary": processor.summary()}
