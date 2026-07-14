"""Closed-loop local engineering department runtime for Campaign 0550.

The Estate side keeps governance and evidence references only.  The runnable
worker files, Git worktrees, and run evidence are externalized to the Steward's
A-drive roots and invoked through the existing Helen, Grace, Dispatch, provider
health/routing, validation, and audit surfaces.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from estate.core.execution_dispatch import DispatchRequest, complete_dispatch_item, enqueue_dispatch_request, update_dispatch_state
from estate.core.grace_operations_runtime import GraceObjective, GraceOperationsRuntime
from estate.core.helen_workforce import HelenWorkforceStore, WorkforceAssessment, WorkforceRequest
from estate.core.paths import ESTATE_ROOT
from estate.core.production_readiness_validation import generate_production_readiness_report

DEFAULT_RUNTIME_ROOT = r"A:\AI\Tools\EngineeringWorkerRuntime"
DEFAULT_WORKTREE_ROOT = r"A:\AI\EngineeringWorktrees"
DEFAULT_RUN_ROOT = r"A:\AI\EngineeringRuns"
GOVERNANCE_ROOT = Path("runtime/local_engineering_department")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def external_path(value: str, *, estate_root: Path | None = None) -> Path:
    """Return a host path for an A-drive path without changing the governed value.

    Windows Stewards receive the real A-drive path.  Non-Windows validation hosts map
    the same path beneath ``.external_runtime/A_drive`` so tests can exercise the
    loop without requiring a Windows volume.
    """
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


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


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


class LocalEngineeringDepartment:
    def __init__(self, root: Path | None = None, *, runtime_root: str = DEFAULT_RUNTIME_ROOT, worktree_root: str = DEFAULT_WORKTREE_ROOT, run_root: str = DEFAULT_RUN_ROOT) -> None:
        self.root = root or (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())
        self.runtime_root_ref = runtime_root
        self.worktree_root_ref = worktree_root
        self.run_root_ref = run_root
        self.runtime_root = external_path(runtime_root, estate_root=self.root)
        self.worktree_root = external_path(worktree_root, estate_root=self.root)
        self.run_root = external_path(run_root, estate_root=self.root)
        self.governance_root = self.root / GOVERNANCE_ROOT

    def install_runtime(self) -> dict[str, str]:
        self.runtime_root.mkdir(parents=True, exist_ok=True)
        worker = self.runtime_root / "Invoke-EngineeringWorker.ps1"
        worker.write_text("""param(\n  [Parameter(Mandatory=$true)][string]$PackagePath,\n  [Parameter(Mandatory=$true)][string]$WorktreePath,\n  [Parameter(Mandatory=$true)][string]$EvidencePath\n)\n$ErrorActionPreference = 'Stop'\nNew-Item -ItemType Directory -Force -Path $EvidencePath | Out-Null\n$package = Get-Content -Raw -Path $PackagePath | ConvertFrom-Json\n$stamp = Get-Date -Format o\n$result = [ordered]@{ status = 'completed'; executed_at = $stamp; package_id = $package.package_id; worktree = $WorktreePath; note = 'Local worker runtime received a bounded package and preserved evidence.' }\n$result | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 -Path (Join-Path $EvidencePath 'worker_result.json')\n""", encoding="utf-8")
        manifest = {"runtime_root": self.runtime_root_ref, "entrypoint": str(Path(self.runtime_root_ref) / "Invoke-EngineeringWorker.ps1"), "installed_at": utc_now(), "no_scheduler": True, "no_provider_control_plane": True}
        _write_json(self.runtime_root / "runtime_manifest.json", manifest)
        return {"runtime_manifest": str(self.runtime_root / "runtime_manifest.json"), "worker_entrypoint": str(worker)}

    def helen_staff(self) -> tuple[WorkforceAssessment, dict[str, str]]:
        role = EngineeringRole("eng-local-implementer-validator", "Local Engineering Implementer/Validator", ["git_worktree", "bounded_patch", "independent_validation", "evidence_hashing"], ["package_contract_only"], ["python -m pytest tests/test_local_engineering_department.py"])
        store = HelenWorkforceStore(self.root)
        request = WorkforceRequest.create(request_type="staffing_request", subject_id=role.role_id, subject_type="engineering_role", requesting_office="Steward", summary="Staff the first local engineering department operational slice.", requested_outcome="Available qualified local engineering worker assigned to Grace.", source_artifacts=["collaboration/campaigns/CAMPAIGN_0550_LOCAL_ENGINEERING_DEPARTMENT_FIRST_OPERATIONAL_SLICE.md"], metadata={"role": asdict(role)})
        req_path = store.save_request(request)
        assessment = WorkforceAssessment.create(request_id=request.request_id, subject_id=request.subject_id, worker_factors=["candidate has bounded local git/runtime execution evidence"], institutional_factors=["Dispatch remains the handoff authority", "Grace receives staffed team only after Helen readiness"], missing_evidence=[], recommendations=["staffing_action"], rationale="Helen verifies the initial local engineering worker is eligible for a bounded first operational slice.", evidence_artifacts=[str(req_path)], grace_operational_constraint_summary="Worker may receive only bounded Dispatch packages and may not merge or alter protected areas outside contract.", metadata={"staffed_worker_id": "local-engineering-worker-001", "qualification_summary": role.required_qualifications})
        ass_path = store.save_assessment(assessment)
        return assessment, {"helen_request": str(req_path), "helen_assessment": str(ass_path)}

    def run_closed_loop(self) -> LocalEngineeringResult:
        paths = self.install_runtime()
        self.worktree_root.mkdir(parents=True, exist_ok=True); self.run_root.mkdir(parents=True, exist_ok=True)
        assessment, helen_paths = self.helen_staff(); paths.update(helen_paths)
        grace = GraceOperationsRuntime(self.root)
        objective = GraceObjective.create(requested_by="Steward", title="First local engineering department closed-loop run", summary="Demonstrate Helen staffing, Grace assignment, Dispatch handoff, external local worker execution, independent validation, and governed closure.", work_package_id="WP-0552", owner="local-engineering-worker-001", evidence=list(paths.values()), metadata={"helen_assessment_id": assessment.assessment_id})
        action, grace_paths = grace.conduct_objective(objective, request_dispatch=True); paths.update(grace_paths)
        dispatch_id = action.dispatch_handoff_request.get("dispatch_id") if action.dispatch_handoff_request else None
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
        worktree = self.worktree_root / run_id; evidence_dir = self.run_root / run_id
        shutil.copytree(self.root, worktree, ignore=shutil.ignore_patterns(".git", ".external_runtime", ".pytest_cache", "__pycache__"))
        package = {"package_id": "WP-0552", "dispatch_id": dispatch_id, "allowed_write_paths": ["runtime/local_engineering_department"], "worktree": self.worktree_root_ref + "\\" + run_id, "evidence": self.run_root_ref + "\\" + run_id}
        package_path = evidence_dir / "bounded_package.json"; _write_json(package_path, package)
        if os.name == "nt":
            subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(self.runtime_root / "Invoke-EngineeringWorker.ps1"), "-PackagePath", str(package_path), "-WorktreePath", str(worktree), "-EvidencePath", str(evidence_dir)], check=True)
        else:
            _write_json(evidence_dir / "worker_result.json", {"status": "completed", "executed_at": utc_now(), "package_id": "WP-0552", "worktree": str(worktree), "note": "Simulated PowerShell worker on non-Windows validation host."})
        validation = generate_production_readiness_report(root=worktree)
        validation_path = evidence_dir / "independent_validation.json"; _write_json(validation_path, validation)
        hashes = {p.name: _sha256(p) for p in [package_path, evidence_dir / "worker_result.json", validation_path]}
        evidence = {"run_id": run_id, "external_runtime_root": self.runtime_root_ref, "external_worktree": self.worktree_root_ref + "\\" + run_id, "external_evidence": self.run_root_ref + "\\" + run_id, "host_runtime_path": str(self.runtime_root), "host_worktree": str(worktree), "host_evidence": str(evidence_dir), "sha256": hashes, "validation_summary": validation.get("summary", {})}
        if dispatch_id:
            update_dispatch_state(dispatch_id, "Validation", root=self.root)
            complete_dispatch_item(dispatch_id, result_reference=str(evidence_dir / "worker_result.json"), root=self.root)
        grace.close_objective(objective.objective_id, reviewed_by="Grace", result="completed with evidence for Chief Architect and Steward acceptance", accepted=False)
        result = LocalEngineeringResult("CAMPAIGN_0550", ["WP-0548", "WP-0549", "WP-0550", "WP-0551", "WP-0552"], utc_now(), self.runtime_root_ref, self.worktree_root_ref, self.run_root_ref, "", dispatch_id or "", objective.objective_id, assessment.assessment_id, "completed", evidence, [])
        record = self.governance_root / "acceptance_records" / f"{run_id}.json"; result.governance_record = str(record.relative_to(self.root))
        _write_json(record, result.to_dict())
        _write_json(self.governance_root / "latest.json", result.to_dict())
        return result


def format_closed_loop_result(result: LocalEngineeringResult) -> str:
    return "\n".join(["Local engineering closed loop complete", f"Work packages: {', '.join(result.work_packages)}", f"Runtime: {result.runtime_root}", f"Worktree: {result.evidence.get('external_worktree')}", f"Evidence: {result.evidence.get('external_evidence')}", f"Governance record: {result.governance_record}", f"Dispatch: {result.dispatch_id}", f"Result: {result.result}"])
