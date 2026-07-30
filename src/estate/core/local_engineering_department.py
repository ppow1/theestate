"""Estate adapter for the external engineering worker runtime.

The Estate remains the governance/control plane.  Executable worker ownership lives
in the Steward-controlled runtime at ``A:\\AI\\Tools\\EngineeringWorkerRuntime``.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from estate.core.execution_dispatch import complete_dispatch_item, inspect_dispatch_item, update_dispatch_state
from estate.core.execution_adapter_handoff_runtime import prepare_handoff
from estate.core.grace_operations_runtime import GraceObjective, GraceOperationsRuntime
from estate.core.helen_workforce import HelenWorkforceStore, WorkforceAssessment, WorkforceRequest
from estate.core.paths import ESTATE_ROOT

DEFAULT_RUNTIME_ROOT = r"A:\AI\Tools\EngineeringWorkerRuntime"
DEFAULT_WORKTREE_ROOT = r"A:\AI\EngineeringWorktrees"
DEFAULT_RUN_ROOT = r"A:\AI\EngineeringRuns"
REQUIRED_RUNTIME_ID = "engineering-worker-runtime"
REQUIRED_RUNTIME_VERSION = "1.0.0"
GOVERNANCE_ROOT = Path("runtime/local_engineering_department")
BOUNDED_PACKAGE_DIR = GOVERNANCE_ROOT / "bounded_packages"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def external_path(value: str, *, estate_root: Path | None = None) -> Path:
    """Map canonical A-drive references for non-Windows test hosts only."""
    root = estate_root or (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())
    # Production uses the Steward's canonical external roots. Isolated test
    # roots must not reuse machine worktrees, runs, or installed runtimes.
    if os.name == "nt" and root.resolve() == (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd()).resolve():
        return Path(value)
    text = value.replace("\\", "/")
    if len(text) >= 2 and text[1] == ":":
        text = f"{text[0]}_drive" + text[2:]
    return root / ".external_runtime" / text.lstrip("/")


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    h = hashlib.sha256(); h.update(path.read_bytes()); return h.hexdigest()


def _canonical_child(parent_ref: str, child: str) -> str:
    return parent_ref.rstrip("\\/") + "\\" + child


def _generic_engineering_handoff(item: Any, root: Path) -> dict[str, Any]:
    """Persist a provider-neutral Engineering commission handoff.

    Grace/Dispatch may intentionally leave ``provider`` empty. Engineering
    owns capability interpretation and provider selection after this record is
    accepted by Dispatch.
    """
    metadata = dict(item.provider_metadata or {})
    commission = metadata.get("commission") if isinstance(metadata.get("commission"), dict) else {}
    payload = {
        "schema_version": "estate.engineering.dispatch-handoff.v1",
        "dispatch_id": item.dispatch_id,
        "commission": commission,
        "provider_id": None,
        "provider_selection_owner": "Engineering",
        "dispatch_authority": "Dispatch",
        "grace_objective_id": commission.get("grace_objective_id") or metadata.get("grace_objective_id"),
        "allowed_read_paths": list(item.allowed_read_paths),
        "allowed_write_paths": list(item.allowed_write_paths),
        "created_at": utc_now(),
    }
    path = root / "runtime/execution_dispatch/handoffs" / f"{item.dispatch_id}_engineering_commission.json"
    _write_json(path, payload)
    return {"status": "handoff_validated", "dispatch_id": item.dispatch_id, "errors": [], "artifacts": {"request_path": str(path.relative_to(root)).replace("\\", "/")}, "dispatch": item.to_dict(), "adapter_request": None}


@dataclass
class EngineeringRole:
    role_id: str
    title: str
    required_qualifications: list[str]
    permitted_paths: list[str]
    validation_commands: list[str]
    authority_boundary: str = "Helen staffs; Grace assigns; Dispatch hands off; Chief Architect and Steward accept."


@dataclass
class LocalEngineeringResult:
    campaign: str
    work_packages: list[str]
    created_at: str
    runtime_root: str
    worktree_root: str
    run_root: str
    governance_record: str
    dispatch_id: str
    grace_objective_id: str
    helen_assessment_id: str
    result: str
    evidence: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ExternalEngineeringRuntimeAdapter:
    """Thin fail-closed adapter to the external engineering worker runtime."""

    def __init__(self, *, root: Path, runtime_root_ref: str, worktree_root_ref: str, run_root_ref: str) -> None:
        self.root = root
        self.runtime_root_ref = runtime_root_ref
        self.worktree_root_ref = worktree_root_ref
        self.run_root_ref = run_root_ref
        self.runtime_root = external_path(runtime_root_ref, estate_root=root)
        self.worktree_root = external_path(worktree_root_ref, estate_root=root)
        self.run_root = external_path(run_root_ref, estate_root=root)

    @property
    def manifest_path(self) -> Path:
        return self.runtime_root / "runtime_manifest.json"

    def validate_manifest(self) -> dict[str, Any]:
        if not self.manifest_path.is_file():
            raise RuntimeError(f"External engineering worker runtime manifest is missing: {self.runtime_root_ref}\\runtime_manifest.json")
        manifest = _read_json(self.manifest_path)
        if manifest.get("runtime_id") != REQUIRED_RUNTIME_ID:
            raise RuntimeError("External engineering worker runtime id is incompatible")
        if manifest.get("version") != REQUIRED_RUNTIME_VERSION:
            raise RuntimeError(f"External engineering worker runtime version mismatch: expected {REQUIRED_RUNTIME_VERSION}, got {manifest.get('version')}")
        if manifest.get("canonical_runtime_root") != self.runtime_root_ref:
            raise RuntimeError("External engineering worker runtime canonical root mismatch")
        if manifest.get("no_scheduler") is not True or manifest.get("no_provider_control_plane") is not True:
            raise RuntimeError("External engineering worker runtime manifest violates Estate authority boundaries")
        entrypoint = manifest.get("entrypoint")
        if not isinstance(entrypoint, str) or not (self.runtime_root / entrypoint).is_file():
            raise RuntimeError("External engineering worker runtime entrypoint is missing")
        return manifest

    def invoke(self, *, package_path: Path, worktree_path: Path, evidence_path: Path) -> dict[str, Any]:
        manifest = self.validate_manifest()
        self._enforce_bounded_paths(package_path=package_path, worktree_path=worktree_path, evidence_path=evidence_path)
        entrypoint = self.runtime_root / manifest["entrypoint"]
        cmd = [sys.executable, str(entrypoint), "--package", str(package_path), "--worktree", str(worktree_path), "--evidence", str(evidence_path)]
        completed = subprocess.run(cmd, check=False, text=True, capture_output=True)
        if completed.returncode != 0:
            raise RuntimeError(f"External engineering worker runtime failed closed ({completed.returncode}): {completed.stderr.strip()}")
        result_path = evidence_path / "worker_result.json"
        if not result_path.is_file():
            raise RuntimeError("External engineering worker runtime did not produce documented worker_result.json")
        return {"manifest": manifest, "command": [sys.executable, str(Path(self.runtime_root_ref) / manifest["entrypoint"]), "--package", "<bounded_package>", "--worktree", "<external_worktree>", "--evidence", "<external_evidence>"], "stdout": completed.stdout.strip()}

    def load_worker_result(self, evidence_path: Path) -> dict[str, Any]:
        result_path = evidence_path / "worker_result.json"
        if not result_path.is_file():
            raise RuntimeError("Engineering worker did not produce worker_result.json")
        result = _read_json(result_path)
        if not isinstance(result, dict):
            raise RuntimeError("Engineering worker result must be a JSON object")
        if result.get("status") not in {"completed", "blocked", "failed"}:
            raise RuntimeError("Engineering worker result has no truthful terminal status")
        required = {"commission", "plan", "provider_selection", "provider_result", "validation", "retry_history", "final_disposition"}
        missing = sorted(required - set(result))
        if missing:
            raise RuntimeError("Engineering worker result is missing required evidence: " + ", ".join(missing))
        if result["status"] == "completed":
            if result.get("final_disposition") != "completed" or not result.get("authority", {}).get("institutional_acceptance_granted") is False:
                raise RuntimeError("Engineering completion result violates the acceptance authority boundary")
            if result.get("provider_result", {}).get("status") != "succeeded":
                raise RuntimeError("Engineering completion requires a successful provider receipt")
            if not result.get("provider_result", {}).get("receipt_path") or not result.get("provider_result", {}).get("artifacts"):
                raise RuntimeError("Engineering completion requires provider receipt and artifact references")
            if result.get("validation", {}).get("passed") is not True:
                raise RuntimeError("Engineering completion requires passed commission-specific validation")
        return result

    def _enforce_bounded_paths(self, *, package_path: Path, worktree_path: Path, evidence_path: Path) -> None:
        package_path.resolve().relative_to((self.root / BOUNDED_PACKAGE_DIR).resolve())
        worktree_path.resolve().relative_to(self.worktree_root.resolve())
        evidence_path.resolve().relative_to(self.run_root.resolve())


class LocalEngineeringDepartment:
    def __init__(self, root: Path | None = None, *, runtime_root: str = DEFAULT_RUNTIME_ROOT, worktree_root: str = DEFAULT_WORKTREE_ROOT, run_root: str = DEFAULT_RUN_ROOT) -> None:
        self.root = root or (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())
        self.runtime_root_ref = runtime_root; self.worktree_root_ref = worktree_root; self.run_root_ref = run_root
        self.runtime_root = external_path(runtime_root, estate_root=self.root)
        self.worktree_root = external_path(worktree_root, estate_root=self.root)
        self.run_root = external_path(run_root, estate_root=self.root)
        self.governance_root = self.root / GOVERNANCE_ROOT
        self.adapter = ExternalEngineeringRuntimeAdapter(root=self.root, runtime_root_ref=runtime_root, worktree_root_ref=worktree_root, run_root_ref=run_root)

    def install_runtime(self) -> dict[str, str]:
        raise RuntimeError("Embedded runtime installation has been removed. Run scripts/Sync-EngineeringWorkerRuntime.ps1 to materialize A:\\AI\\Tools\\EngineeringWorkerRuntime from governed source artifacts.")

    def helen_staff(self) -> tuple[WorkforceAssessment, dict[str, str]]:
        role = EngineeringRole("eng-local-implementer-validator", "Local Engineering Implementer/Validator", ["git_worktree", "bounded_patch", "independent_validation", "evidence_hashing"], ["package_contract_only"], ["python -m pytest tests/test_local_engineering_department.py"])
        store = HelenWorkforceStore(self.root)
        request = WorkforceRequest.create(request_type="staffing_request", subject_id=role.role_id, subject_type="engineering_role", requesting_office="Steward", summary="Staff the first local engineering department operational slice.", requested_outcome="Available qualified local engineering worker assigned to Grace.", source_artifacts=["collaboration/campaigns/CAMPAIGN_0550_LOCAL_ENGINEERING_DEPARTMENT_FIRST_OPERATIONAL_SLICE.md"], metadata={"role": asdict(role)})
        req_path = store.save_request(request)
        assessment = WorkforceAssessment.create(request_id=request.request_id, subject_id=request.subject_id, worker_factors=["candidate has bounded local git/runtime execution evidence"], institutional_factors=["Dispatch remains the handoff authority", "Grace receives staffed team only after Helen readiness"], missing_evidence=[], recommendations=["staffing_action"], rationale="Helen verifies the initial local engineering worker is eligible for a bounded first operational slice.", evidence_artifacts=[str(req_path)], grace_operational_constraint_summary="Worker may receive only bounded Dispatch packages and may not merge or alter protected areas outside contract.", metadata={"staffed_worker_id": "local-engineering-worker-001", "qualification_summary": role.required_qualifications})
        ass_path = store.save_assessment(assessment)
        return assessment, {"helen_request": str(req_path), "helen_assessment": str(ass_path)}

    def run_closed_loop(self) -> LocalEngineeringResult:
        paths: dict[str, str] = {"runtime_manifest": str(Path(self.runtime_root_ref) / "runtime_manifest.json")}
        manifest = self.adapter.validate_manifest()
        self.worktree_root.mkdir(parents=True, exist_ok=True); self.run_root.mkdir(parents=True, exist_ok=True)
        assessment, helen_paths = self.helen_staff(); paths.update(helen_paths)
        grace = GraceOperationsRuntime(self.root)
        objective = GraceObjective.create(requested_by="Steward", title="First local engineering department closed-loop run", summary="Demonstrate Helen staffing, Grace assignment, Dispatch handoff, external local worker execution, independent validation, and governed closure.", work_package_id="WP-0552", owner="local-engineering-worker-001", evidence=list(paths.values()), metadata={"helen_assessment_id": assessment.assessment_id})
        action, grace_paths = grace.conduct_objective(objective, request_dispatch=True); paths.update(grace_paths)
        dispatch_id = action.dispatch_handoff_request.get("dispatch_id") if action.dispatch_handoff_request else None
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
        worktree = self.worktree_root / run_id; evidence_dir = self.run_root / run_id; worktree.mkdir(parents=True); evidence_dir.mkdir(parents=True)
        package = {"package_id": "WP-0552", "dispatch_id": dispatch_id, "allowed_write_paths": ["runtime/local_engineering_department"], "commission": {"commission_id": f"engcom-{run_id}", "grace_objective_id": objective.objective_id, "requested_outcome": objective.summary, "artifact_type": "structured_work_product", "required_capabilities": ["documentation_draft"], "acceptance_criteria": [{"kind": "artifact_exists"}, {"kind": "provider_receipt"}], "constraints": [], "allowed_providers": ["fixture-local-engineering"]}, "provider_catalog": [{"provider_id": "fixture-local-engineering", "provider_type": "fixture", "implementation_kind": "deterministic_local_artifact", "adapter_kind": "deterministic_local_artifact", "capabilities": ["documentation_draft"], "status": "implemented"}], "worktree": _canonical_child(self.worktree_root_ref, run_id), "evidence": _canonical_child(self.run_root_ref, run_id), "authority_boundary": "Helen staffs; Grace assigns; Dispatch hands off; Engineering interprets and validates only the bounded generic commission."}
        package_path = self.root / BOUNDED_PACKAGE_DIR / f"{run_id}.json"; _write_json(package_path, package)
        invocation = self.adapter.invoke(package_path=package_path, worktree_path=worktree, evidence_path=evidence_dir)
        worker_result = self.adapter.load_worker_result(evidence_dir)
        raw_files = [evidence_dir / "worker_result.json"]
        hashes = {p.name: _sha256(p) for p in raw_files}; hashes[package_path.name] = _sha256(package_path)
        evidence = {"run_id": run_id, "external_runtime_root": self.runtime_root_ref, "external_worktree": package["worktree"], "external_evidence": package["evidence"], "worker_result": package["evidence"] + r"\worker_result.json", "runtime_manifest_sha256": _sha256(self.adapter.manifest_path), "entrypoint_sha256": _sha256(self.runtime_root / manifest["entrypoint"]), "sha256": hashes, "engineering_result": worker_result, "provenance": {"runtime_id": manifest["runtime_id"], "runtime_version": manifest["version"], "entrypoint": str(Path(self.runtime_root_ref) / manifest["entrypoint"]), "invocation": invocation["command"]}}
        if dispatch_id and worker_result["status"] == "completed":
            update_dispatch_state(dispatch_id, "Validation", root=self.root)
            complete_dispatch_item(dispatch_id, result_reference=package["evidence"] + r"\worker_result.json", root=self.root)
        grace.close_objective(objective.objective_id, reviewed_by="Grace", result=f"Engineering worker disposition: {worker_result['status']}; acceptance remains external", accepted=False)
        result = LocalEngineeringResult("CAMPAIGN_0550", ["WP-0548", "WP-0549", "WP-0550", "WP-0551", "WP-0552"], utc_now(), self.runtime_root_ref, self.worktree_root_ref, self.run_root_ref, "", dispatch_id or "", objective.objective_id, assessment.assessment_id, worker_result["status"], evidence, [])
        record = self.governance_root / "acceptance_records" / f"{run_id}.json"; result.governance_record = str(record.relative_to(self.root))
        _write_json(record, result.to_dict()); _write_json(self.governance_root / "latest.json", result.to_dict())
        return result

    def run_dispatch_bridge(self, dispatch_id: str) -> LocalEngineeringResult:
        """Execute an existing governed Dispatch item through the external worker runtime.

        This bridge is intentionally narrow: Dispatch remains the source of execution
        authority, the external runtime receives only a bounded package, validation is
        recorded independently, Grace records closure evidence, and Chief Architect /
        Steward acceptance remains an evidence record rather than an automatic approval.
        """
        paths: dict[str, str] = {"runtime_manifest": str(Path(self.runtime_root_ref) / "runtime_manifest.json")}
        manifest = self.adapter.validate_manifest()
        item = inspect_dispatch_item(dispatch_id, self.root)
        handoff = _generic_engineering_handoff(item, self.root) if not item.provider else prepare_handoff(dispatch_id, self.root, write=True)
        if handoff.get("errors"):
            raise RuntimeError("Dispatch item is not eligible for engineering worker runtime bridge: " + "; ".join(handoff["errors"]))
        paths.update(handoff.get("artifacts") or {})
        self.worktree_root.mkdir(parents=True, exist_ok=True); self.run_root.mkdir(parents=True, exist_ok=True)
        grace = GraceOperationsRuntime(self.root)
        objective = GraceObjective.create(requested_by="Dispatch", title=f"Engineering worker runtime execution for {dispatch_id}", summary="Run an existing governed Dispatch item through the external Engineering Worker Runtime and record closure evidence.", work_package_id=item.work_package_id, owner=item.assigned_worker or "local-engineering-worker-001", evidence=list(paths.values()), metadata={"dispatch_id": dispatch_id, "handoff_status": handoff.get("status")})
        _, grace_paths = grace.conduct_objective(objective, request_dispatch=False); paths.update(grace_paths)
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
        worktree = self.worktree_root / run_id; evidence_dir = self.run_root / run_id; worktree.mkdir(parents=True); evidence_dir.mkdir(parents=True)
        metadata = dict(item.provider_metadata or {})
        commission = metadata.get("commission") if isinstance(metadata.get("commission"), dict) else {}
        commission = {
            "commission_id": commission.get("commission_id") or metadata.get("engineering_commission_id") or f"engcom-{dispatch_id}",
            "grace_objective_id": commission.get("grace_objective_id") or metadata.get("grace_objective_id") or item.work_package_id or dispatch_id,
            "requested_outcome": commission.get("requested_outcome") or item.title or "Complete the bounded Engineering commission.",
            "artifact_type": commission.get("artifact_type") or metadata.get("artifact_type") or "structured_work_product",
            "required_capabilities": commission.get("required_capabilities") or metadata.get("required_capabilities") or ["documentation_draft"],
            "acceptance_criteria": commission.get("acceptance_criteria") or metadata.get("acceptance_criteria") or [{"kind": "artifact_exists"}, {"kind": "provider_receipt"}],
            "constraints": commission.get("constraints") or metadata.get("constraints") or [],
            "allowed_providers": commission.get("allowed_providers") or item.allowed_providers or [],
        }
        catalog = metadata.get("provider_catalog")
        if not isinstance(catalog, list):
            # Test/fixture providers must declare their adapter explicitly. A
            # real provider is never silently converted into a fake adapter.
            if str(item.provider or "").startswith("fixture"):
                catalog = [{"provider_id": item.provider, "provider_type": "fixture", "implementation_kind": "deterministic_local_artifact", "adapter_kind": "deterministic_local_artifact", "capabilities": commission["required_capabilities"], "status": "implemented"}]
            else:
                catalog_path = self.root / "config/providers/catalog.json"
                try:
                    catalog_data = _read_json(catalog_path)
                    catalog = catalog_data.get("providers", []) if isinstance(catalog_data, dict) else []
                except (OSError, ValueError, json.JSONDecodeError):
                    catalog = []
        package = {"package_id": item.work_package_id or dispatch_id, "dispatch_id": dispatch_id, "handoff_reference": item.handoff_reference or handoff.get("artifacts", {}).get("request_path"), "prompt_source": item.prompt_source, "allowed_read_paths": item.allowed_read_paths, "allowed_write_paths": item.allowed_write_paths, "commission": commission, "provider_catalog": catalog, "retry_policy": metadata.get("retry_policy") or {"max_retries": 0}, "worktree": _canonical_child(self.worktree_root_ref, run_id), "evidence": _canonical_child(self.run_root_ref, run_id), "authority_boundary": "Dispatch authorizes; Engineering interprets, selects, executes, and validates only this bounded commission; Chief Architect/Steward acceptance is not automatic."}
        package_path = self.root / BOUNDED_PACKAGE_DIR / f"{run_id}_{dispatch_id}.json"; _write_json(package_path, package)
        update_dispatch_state(dispatch_id, "Running", root=self.root)
        invocation = self.adapter.invoke(package_path=package_path, worktree_path=worktree, evidence_path=evidence_dir)
        worker_result = self.adapter.load_worker_result(evidence_dir)
        worker_result_path = evidence_dir / "worker_result.json"
        raw_files = [worker_result_path]
        hashes = {p.name: _sha256(p) for p in raw_files}; hashes[package_path.name] = _sha256(package_path)
        evidence = {"run_id": run_id, "dispatch_id": dispatch_id, "handoff": handoff, "external_runtime_root": self.runtime_root_ref, "external_worktree": package["worktree"], "external_evidence": package["evidence"], "worker_result": package["evidence"] + r"\worker_result.json", "runtime_manifest_sha256": _sha256(self.adapter.manifest_path), "entrypoint_sha256": _sha256(self.runtime_root / manifest["entrypoint"]), "sha256": hashes, "engineering_result": worker_result, "acceptance": {"chief_architect_review_required": True, "steward_acceptance_required": True, "automatic_acceptance": False}, "provenance": {"runtime_id": manifest["runtime_id"], "runtime_version": manifest["version"], "entrypoint": str(Path(self.runtime_root_ref) / manifest["entrypoint"]), "invocation": invocation["command"]}}
        terminal = worker_result["status"]
        if terminal == "completed":
            update_dispatch_state(dispatch_id, "Validation", root=self.root)
            complete_dispatch_item(dispatch_id, result_reference=package["evidence"] + r"\worker_result.json", root=self.root)
        elif terminal == "blocked":
            from estate.core.execution_dispatch import block_dispatch_item
            block_dispatch_item(dispatch_id, worker_result.get("provider_result", {}).get("reason") or "Engineering commission blocked.", root=self.root)
        else:
            update_dispatch_state(dispatch_id, "Failed", root=self.root, summary="Engineering commission failed after provider execution or validation.")
        closure_paths = grace.close_objective(objective.objective_id, reviewed_by="Grace", result=f"Engineering worker disposition: {terminal}; acceptance remains external", accepted=False); paths.update(closure_paths)
        result = LocalEngineeringResult("WP-0656", [item.work_package_id or dispatch_id], utc_now(), self.runtime_root_ref, self.worktree_root_ref, self.run_root_ref, "", dispatch_id, objective.objective_id, "", terminal, evidence, [])
        record = self.governance_root / "acceptance_records" / f"{run_id}_{dispatch_id}.json"; result.governance_record = str(record.relative_to(self.root))
        _write_json(record, result.to_dict()); _write_json(self.governance_root / "latest_dispatch_bridge.json", result.to_dict())
        return result


def format_closed_loop_result(result: LocalEngineeringResult) -> str:
    return "\n".join(["Local engineering closed loop complete", f"Work packages: {', '.join(result.work_packages)}", f"Runtime: {result.runtime_root}", f"Worktree: {result.evidence.get('external_worktree')}", f"Evidence: {result.evidence.get('external_evidence')}", f"Governance record: {result.governance_record}", f"Dispatch: {result.dispatch_id}", f"Result: {result.result}"])
