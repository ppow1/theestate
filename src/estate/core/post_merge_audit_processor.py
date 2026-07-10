"""Pending post-merge audit request consumer with claim protection."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from estate.core.operational_targets_runtime import OperationalTargetRuntime
from estate.core.operational_target_resolution import OperationalTargetResolver
from estate.core.operational_target_validation_binding import OperationalTargetValidationBinder
from estate.core.paths import ESTATE_ROOT
from estate.core.post_merge_validation_pipeline import PipelineConfig, PostMergeValidationPipeline, utc_now_iso
from estate.core.post_merge_audit_lifecycle import FINAL_VERDICTS

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
        self.resolver = OperationalTargetResolver(self.root)
        self.binder = OperationalTargetValidationBinder(self.root)
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
        pending = self.list_requests("pending")
        pending.sort(key=lambda r: (0 if ((r.get("metadata") or {}).get("canonical_status") == "admitted" or (r.get("metadata") or {}).get("canonical_discovery_id")) else 1, r.get("created_at", "")))
        for req in pending:
            p = Path(req["request_path"])
            current = _read_json(p)
            if current.get("state", current.get("status", "pending")) != "pending":
                continue
            if self._has_final_verdict(current):
                current["state"] = "already_audited"; current.setdefault("history", []).append({"at": utc_now_iso(), "action": "skipped_final_verdict_duplicate"})
                _write_json(p, current); continue
            if current.get("state") in {"superseded", "quarantined", "manual_hold"}:
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
        reason = None if results else self._zero_throughput_reason()
        payload = {"processed_count": len(results), "results": results, "zero_throughput_reason": reason, "provider_execution_performed": False, "dispatch_execution_performed": False}
        self._write_status(payload); return payload

    def demonstrate(self, work_package: str, pr: str | int | None = None) -> dict[str, Any]:
        resolution = self.resolver.resolve("estate")
        target_id = resolution.canonical_target_id or "estate-main"
        req = {"audit_id": f"demo-{work_package.lower()}", "target_id": target_id, "requested_target_identifier": "estate", "canonical_target_id": target_id, "target_resolution_method": resolution.resolution_method, "work_package_id": work_package, "source_kind": "demonstration", "source_reference": "HEAD", "expected_files": [], "metadata": {"pr": pr, "target_resolution": resolution.to_dict()}, "state": "pending"}
        self.request_dir.mkdir(parents=True, exist_ok=True); _write_json(self.request_dir / f"{req['audit_id']}.json", req)
        return self.process_next()

    def _process_claimed(self, req: dict[str, Any]) -> dict[str, Any]:
        p = Path(req["request_path"])
        try:
            requested = req.get("requested_target_identifier") or req.get("target_id")
            resolution = self.resolver.resolve(requested)
            req["requested_target_identifier"] = requested
            req["target_resolution_method"] = resolution.resolution_method
            req["latest_target_resolution"] = resolution.to_dict()
            if not resolution.resolved or not resolution.canonical_target_id:
                raise ValueError("unknown target " + str(requested))
            req["canonical_target_id"] = resolution.canonical_target_id
            req["target_id"] = resolution.canonical_target_id
            binding = self.binder.bind(resolution.canonical_target_id)
            req["target_binding_status"] = binding.to_dict()
            if not binding.ready:
                raise ValueError("target binding incomplete: " + ", ".join(binding.missing_requirements))
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

    def _has_final_verdict(self, req: dict[str, Any]) -> bool:
        for base in [self.root / BASE / "verdicts", self.root / BASE / "evidence"]:
            if not base.exists(): continue
            paths = list(base.glob("*.json")) + list(base.glob("*/verdict.json"))
            for vp in paths:
                try: d = _read_json(vp)
                except Exception: continue
                if d.get("target_id") == req.get("target_id") and d.get("work_package_id") == req.get("work_package_id") and d.get("verdict") in FINAL_VERDICTS:
                    return True
        return False

    def _zero_throughput_reason(self) -> str:
        reqs = self.list_requests()
        if not reqs or not any(r.get("state") == "pending" for r in reqs): return "no_pending_requests"
        if all(r.get("state") in {"superseded", "quarantined", "manual_hold"} for r in reqs): return "all_requests_held"
        if all(self._has_final_verdict(r) or r.get("state") in {"completed", "ring2_required", "blocked", "validation_failed", "workspace_failed", "already_audited"} for r in reqs): return "all_requests_terminal"
        return "processor_fault"

    def summary(self) -> dict[str, Any]:
        reqs = self.list_requests()
        latest = next((r for r in reversed(reqs) if r.get("state") in {"completed","blocked","ring2_required","failed"}), None)
        running = next((r for r in reqs if r.get("state") in {"claimed","running_validation","running_ring2"}), None)
        latest_resolution = (latest or {}).get("latest_target_resolution") or ((latest or {}).get("metadata") or {}).get("target_resolution")
        latest_binding = (latest or {}).get("target_binding_status") or {}
        return {"automatic_validation_available": True, "pending_audit_requests": sum(1 for r in reqs if r.get("state") == "pending"), "running_audit_request": running, "latest_completed_audit": latest, "latest_validation_status": (latest or {}).get("validation_result"), "latest_production_ready": (latest or {}).get("production_ready"), "latest_ring2_status": ((latest or {}).get("ring2_paths") or {}).get("prompt"), "latest_verdict": (latest or {}).get("verdict"), "latest_verdict_artifact": (latest or {}).get("verdict_path"), "validation_workspace_health": "configured", "validation_evidence_root": str(self.pipeline.config.resolved_evidence_root()), "provider_execution_performed": False, "dispatch_execution_performed": False, "latest_target_resolution": latest_resolution, "latest_target_resolution_status": (latest_resolution or {}).get("resolution_method"), "latest_target_resolution_method": (latest_resolution or {}).get("resolution_method"), "latest_target_binding_ready": latest_binding.get("ready"), "latest_target_binding_gaps": latest_binding.get("missing_requirements", []), "unresolved_target_requests": sum(1 for r in reqs if ((r.get("latest_target_resolution") or {}).get("resolution_method") == "not_found")), "ambiguous_target_requests": sum(1 for r in reqs if ((r.get("latest_target_resolution") or {}).get("resolution_method") == "ambiguous"))}

    def _write_status(self, payload: dict[str, Any]) -> None:
        status = {"generated_at": utc_now_iso(), "latest_result": payload, "summary": self.summary()}
        _write_json(self.root / STATUS / "latest.json", status); _write_json(self.root / STATUS / "summary.json", status["summary"])

def load_post_merge_audit_processor_status(root: Path | None = None) -> dict[str, Any]:
    processor = PostMergeAuditProcessor(root)
    latest = processor.root / STATUS / "latest.json"
    if latest.exists():
        return _read_json(latest)
    return {"generated_at": utc_now_iso(), "latest_result": None, "summary": processor.summary()}
