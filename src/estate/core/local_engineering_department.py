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

from estate.core.execution_dispatch import complete_dispatch_item, update_dispatch_state
from estate.core.grace_operations_runtime import GraceObjective, GraceOperationsRuntime
from estate.core.helen_workforce import HelenWorkforceStore, WorkforceAssessment, WorkforceRequest
from estate.core.paths import ESTATE_ROOT
from estate.core.production_readiness_validation import generate_production_readiness_report

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
    if os.name == "nt":
        return Path(value)
    root = estate_root or (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())
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
        package = {"package_id": "WP-0552", "dispatch_id": dispatch_id, "allowed_write_paths": ["runtime/local_engineering_department"], "worktree": _canonical_child(self.worktree_root_ref, run_id), "evidence": _canonical_child(self.run_root_ref, run_id), "authority_boundary": "Helen staffs; Grace assigns; Dispatch hands off; external runtime executes only the bounded package."}
        package_path = self.root / BOUNDED_PACKAGE_DIR / f"{run_id}.json"; _write_json(package_path, package)
        invocation = self.adapter.invoke(package_path=package_path, worktree_path=worktree, evidence_path=evidence_dir)
        validation = generate_production_readiness_report(root=self.root)
        validation_path = evidence_dir / "independent_validation.json"; _write_json(validation_path, validation)
        raw_files = [evidence_dir / "worker_result.json", validation_path]
        hashes = {p.name: _sha256(p) for p in raw_files}; hashes[package_path.name] = _sha256(package_path)
        evidence = {"run_id": run_id, "external_runtime_root": self.runtime_root_ref, "external_worktree": package["worktree"], "external_evidence": package["evidence"], "runtime_manifest_sha256": _sha256(self.adapter.manifest_path), "entrypoint_sha256": _sha256(self.runtime_root / manifest["entrypoint"]), "sha256": hashes, "validation_summary": validation.get("summary", {}), "provenance": {"runtime_id": manifest["runtime_id"], "runtime_version": manifest["version"], "entrypoint": str(Path(self.runtime_root_ref) / manifest["entrypoint"]), "invocation": invocation["command"]}}
        if dispatch_id:
            update_dispatch_state(dispatch_id, "Validation", root=self.root)
            complete_dispatch_item(dispatch_id, result_reference=package["evidence"] + r"\worker_result.json", root=self.root)
        grace.close_objective(objective.objective_id, reviewed_by="Grace", result="completed with external evidence references for Chief Architect and Steward acceptance", accepted=False)
        result = LocalEngineeringResult("CAMPAIGN_0550", ["WP-0548", "WP-0549", "WP-0550", "WP-0551", "WP-0552"], utc_now(), self.runtime_root_ref, self.worktree_root_ref, self.run_root_ref, "", dispatch_id or "", objective.objective_id, assessment.assessment_id, "completed", evidence, [])
        record = self.governance_root / "acceptance_records" / f"{run_id}.json"; result.governance_record = str(record.relative_to(self.root))
        _write_json(record, result.to_dict()); _write_json(self.governance_root / "latest.json", result.to_dict())
        return result


def format_closed_loop_result(result: LocalEngineeringResult) -> str:
    return "\n".join(["Local engineering closed loop complete", f"Work packages: {', '.join(result.work_packages)}", f"Runtime: {result.runtime_root}", f"Worktree: {result.evidence.get('external_worktree')}", f"Evidence: {result.evidence.get('external_evidence')}", f"Governance record: {result.governance_record}", f"Dispatch: {result.dispatch_id}", f"Result: {result.result}"])
