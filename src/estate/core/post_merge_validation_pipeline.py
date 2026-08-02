"""Automatic post-merge validation pipeline.

Coordinates deterministic validation in a dedicated workspace and writes bounded
Ring 2/verdict evidence. This module does not run providers, dispatch work,
merge code, commit repairs, or create Steward acceptance.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from estate.core.paths import ESTATE_ROOT
from estate.core.audit_workspace_runtime import config_from_target
from estate.core.audit_workspace_service import AuditWorkspaceService
from estate.core.production_readiness_validation import calculate_production_readiness, validate_receipt
from estate.core.background_process import hidden_windows_process_kwargs

DEFAULT_STATES = {"pending","claimed","running_validation","ring2_required","running_ring2","completed","blocked","failed"}
DEFAULT_VERDICTS = {"ring2_required","accepted","accepted_with_notes","needs_repair","blocked","validation_failed","no_recipe"}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _root(root: Path | None = None) -> Path:
    return root or (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _git(path: Path, *args: str) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(["git", *args], cwd=path, text=True, capture_output=True, check=False)
    except OSError:
        return None


@dataclass
class PipelineConfig:
    root: Path = field(default_factory=_root)
    workspace_root: Path | None = None
    evidence_root: Path | None = None
    ollama_enabled: bool = False
    ollama_model: str = "llama3.1"

    def resolved_workspace_root(self) -> Path:
        return self.workspace_root or Path(os.environ.get("ESTATE_AUDIT_WORKSPACE_ROOT", str(self.root / "runtime/post_merge_audit/workspaces")))

    def resolved_evidence_root(self) -> Path:
        return self.evidence_root or Path(os.environ.get("ESTATE_VALIDATION_EVIDENCE_ROOT", str(self.root / "runtime/post_merge_audit/evidence")))


class PostMergeValidationPipeline:
    def __init__(self, config: PipelineConfig | None = None, *, validator: Callable[[str, Path], dict[str, Any]] | None = None) -> None:
        self.config = config or PipelineConfig()
        self.root = self.config.root
        self.validator = validator or self._standard_validator

    def run(self, request: dict[str, Any], target: Any) -> dict[str, Any]:
        audit_id = request["audit_id"]
        wp = request["work_package_id"]
        target_id = request["target_id"]
        evidence_root = self.config.evidence_root
        workspace_root = self.config.workspace_root
        warnings: list[str] = []
        errors: list[str] = []
        artifacts: dict[str, str] = {}
        retain_failed = bool((getattr(target, "metadata", {}) or {}).get("retain_failed_audit_workspaces", True))
        aw_config = config_from_target(target, self.root, workspace_root=workspace_root, evidence_root=evidence_root, retain_failed_workspaces=retain_failed)
        service = AuditWorkspaceService(aw_config)
        expected_revision = (request.get("metadata") or {}).get("expected_revision") or request.get("source_reference")
        workspace_record = service.prepare(audit_id, expected_revision)
        workspace = Path(workspace_record.workspace_path)
        artifacts["validation_workspace"] = _rel(workspace, self.root)
        evidence_root = aw_config.evidence_root
        workspace_root = aw_config.workspace_root
        evidence = evidence_root / audit_id
        reports = evidence / "reports"; ring2_dir = evidence / "ring2"
        reports.mkdir(parents=True, exist_ok=True); ring2_dir.mkdir(parents=True, exist_ok=True)
        artifacts["workspace_sync_report"] = _rel(evidence_root / "reports" / audit_id / "workspace_sync.json", self.root)
        warnings.extend(workspace_record.warnings)
        errors.extend(workspace_record.errors)
        blocking: list[str] = []
        if workspace_record.state not in {"synchronized"}:
            blocking.extend(workspace_record.errors or ["workspace_synchronization_failed"])
            if "requested_revision_unresolvable" in workspace_record.errors or "requested_revision_not_reachable_from_base" in workspace_record.errors:
                blocking.append("expected_revision_mismatch")
        if workspace_record.isolated_workspace_dirty:
            blocking.append("isolated_workspace_dirty")
        missing = [f for f in request.get("expected_files", []) if not (workspace / f).exists()]
        if missing:
            blocking.append("expected_files_missing: " + ", ".join(missing))

        validation: dict[str, Any] = {"validation_status": "not_run", "failures": [], "findings": [], "warnings": []}
        workspace_success = False
        try:
            if not blocking:
                workspace_record.state = "validating"
                validation = self.validator(wp, workspace)
                _write_json(reports / "validation.json", validation)
                artifacts["validation_report"] = _rel(reports / "validation.json", self.root)
                if validation.get("validation_status") == "no_recipe":
                    blocking.append("validation_recipe_missing")
                elif validation.get("validation_status") not in {"passed", "passed_with_findings"}:
                    blocking.append("validation_failed")
            receipt = validate_receipt(wp, root=workspace) if workspace.exists() else {"receipt_status": "missing"}
            readiness = calculate_production_readiness(validation.get("validation_status", "failed"), receipt)
            if not readiness.get("production_ready"):
                blocking.extend(readiness.get("blocking_reasons") or [])
            prompt = self._write_ring2_prompt(ring2_dir, request, validation, readiness, blocking)
            artifacts["ring2_prompt"] = _rel(prompt, self.root)
            ring2_status = "prompt_generated"
            ring2_verdict = None
            if self.config.ollama_enabled:
                ring2_status, ring2_verdict, out = self._run_ollama(prompt)
                if out:
                    artifacts["ring2_review"] = _rel(out, self.root)
            verdict = "ring2_required"
            if validation.get("validation_status") == "no_recipe" or "validation_recipe_missing" in blocking:
                verdict = "no_recipe"
            elif blocking:
                verdict = "validation_failed" if "validation_failed" in blocking else "blocked"
            elif ring2_verdict:
                verdict = ring2_verdict
            workspace_success = verdict in {"ring2_required", "accepted", "accepted_with_notes"}
        except Exception as exc:
            validation = {"validation_status": "failed", "failures": [str(exc)], "findings": [], "warnings": []}
            errors.append(str(exc)); blocking.append("validation_failed")
            receipt = {"receipt_status": "missing"}; readiness = {"production_ready": False, "non_blocking_findings": []}
            prompt = self._write_ring2_prompt(ring2_dir, request, validation, readiness, blocking)
            artifacts["ring2_prompt"] = _rel(prompt, self.root); ring2_status = "prompt_generated"; ring2_verdict = None; verdict = "validation_failed"
        finally:
            workspace_record = service.cleanup(workspace_record, success=workspace_success)
            _write_json(reports / "workspace_lifecycle.json", workspace_record.to_dict())
            artifacts["workspace_lifecycle"] = _rel(reports / "workspace_lifecycle.json", self.root)
        verdict_payload = {
            "audit_id": audit_id, "target_id": target_id, "work_package_id": wp,
            "state": "completed" if verdict not in {"ring2_required","blocked","validation_failed"} else ("ring2_required" if verdict == "ring2_required" else "blocked"),
            "verdict": verdict, "validation_status": validation.get("validation_status"),
            "production_ready": bool(readiness.get("production_ready")), "receipt_status": receipt.get("receipt_status", "unknown"),
            "ring2_status": ring2_status, "ring2_verdict": ring2_verdict,
            "workspace": str(workspace), "evidence_root": str(evidence), "external_evidence_root": str(evidence_root),
            "active_tree_dirty": workspace_record.active_checkout_dirty, "active_checkout_dirty": workspace_record.active_checkout_dirty,
            "isolated_workspace_dirty": workspace_record.isolated_workspace_dirty, "branch_sync_status": workspace_record.branch_sync_status,
            "revision_reachable": workspace_record.revision_reachable, "workspace_record": workspace_record.to_dict(),
            "base_branch_verified": workspace_record.revision_reachable, "expected_revision_verified": workspace_record.resolved_commit is not None, "expected_files_present": not missing,
            "failures": validation.get("failures", []), "findings": validation.get("findings", []) + readiness.get("non_blocking_findings", []),
            "warnings": warnings + validation.get("warnings", []), "errors": errors,
            "blocking_reasons": blocking, "blocking_reason": "validation_recipe_missing" if verdict == "no_recipe" else (blocking[0] if blocking else None), "retry_eligible": verdict == "no_recipe", "artifacts": artifacts,
            "provider_execution_performed": False, "dispatch_execution_performed": False, "created_at": utc_now_iso(),
        }
        verdict_path = evidence / "verdict.json"
        _write_json(verdict_path, verdict_payload)
        (evidence / "verdict.md").write_text(f"# Post-Merge Audit Verdict\n\n- Verdict: {verdict}\n- Work package: {wp}\n- Production ready: {verdict_payload['production_ready']}\n- Provider execution performed: false\n- Dispatch execution performed: false\n", encoding="utf-8")
        verdict_payload["verdict_path"] = _rel(verdict_path, self.root)
        return verdict_payload

    def _standard_validator(self, wp: str, workspace: Path) -> dict[str, Any]:
        cmd = ["python", "-m", "estate.cli.main", "validate-work-package", "--id", wp, "--json"]
        env = os.environ.copy(); env["PYTHONPATH"] = str(self.root / "src")
        r = subprocess.run(cmd, cwd=workspace, text=True, capture_output=True, check=False, env=env, **hidden_windows_process_kwargs())
        try:
            payload = json.loads(r.stdout)
        except json.JSONDecodeError:
            payload = {"validation_status": "failed", "failures": [r.stderr or r.stdout], "findings": [], "warnings": []}
        payload.setdefault("command", " ".join(cmd)); payload.setdefault("exit_code", r.returncode)
        if r.returncode and payload.get("validation_status") not in {"failed", "no_recipe"}:
            payload["validation_status"] = "failed"
        return payload

    def _write_ring2_prompt(self, ring2_dir: Path, request: dict[str, Any], validation: dict[str, Any], readiness: dict[str, Any], blocking: list[str]) -> Path:
        p = ring2_dir / "prompt.md"
        p.write_text("# Ring 2 Post-Merge Validation Review\n\n"
                     f"Audit: {request.get('audit_id')}\n\nWork package: {request.get('work_package_id')}\n\n"
                     f"Validation status: {validation.get('validation_status')}\n\nProduction ready: {readiness.get('production_ready')}\n\n"
                     f"Blocking reasons: {blocking}\n\nReview boundaries: do not execute providers, dispatch, merge, repair, or create Steward acceptance.\n", encoding="utf-8")
        return p

    def _run_ollama(self, prompt: Path) -> tuple[str, str | None, Path | None]:
        if shutil.which("ollama") is None:
            return "ollama_unavailable", None, None
        r = subprocess.run(["ollama", "run", self.config.ollama_model], input=prompt.read_text(encoding="utf-8"), text=True, capture_output=True, check=False)
        out = prompt.parent / "review.txt"; out.write_text(r.stdout + r.stderr, encoding="utf-8")
        verdict = "accepted_with_notes" if r.returncode == 0 else "blocked"
        return "review_captured", verdict, out
