"""Deterministic Helen operational readiness and Grace hiring gate."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from estate.core.background_operations import utc_now_iso
from estate.core.helen_workforce import HelenWorkforceStore, WorkforceAssessment, WorkforceRequest
from estate.core.paths import ESTATE_ROOT
from estate.core.personnel_identity import resolve_personnel_identity
from estate.core.resident_authority import check_authority
from estate.core.resident_interaction import local_llm_status, resident_surface

READINESS_PATH = Path("runtime/residents/helen/readiness.json")
REPORT_PATH = Path("operations/residents/helen/Helen_Operational_Readiness_Report.md")
SURFACE_PATH = Path("operations/residents/surfaces/helen.json")


def _root(root: Path | None = None) -> Path:
    return Path(root) if root else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _exists(root: Path, rel: str) -> bool:
    return (root / rel).exists()


def _evidence(root: Path, rel: str) -> dict[str, Any]:
    return {"path": rel, "exists": _exists(root, rel)}


def _gate(gate_id: str, name: str, passed: bool, evidence: list[dict[str, Any]], missing: list[str] | None = None, next_action: str | None = None) -> dict[str, Any]:
    return {"gate_id": gate_id, "name": name, "status": "passed" if passed else "failed", "passed": passed, "evidence": evidence, "missing_evidence": missing or [], "next_action": next_action if not passed else None}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_readiness(root: Path | None = None, *, write: bool = True) -> dict[str, Any]:
    rootp = _root(root)
    residents = _read_json(rootp / "data/registry/residents.json", [])
    helen = next((r for r in residents if str(r.get("name", "")).lower() == "helen"), None)
    prompt_files = ["docs/residents/helen/platform-exports/textgen-4_9-helen-v0_2.yaml", "docs/residents/helen/Helen_Resident_Profile_v0_2.md"]
    prompt_text = "\n".join((rootp / p).read_text(encoding="utf-8") for p in prompt_files if (rootp / p).exists())
    llm = local_llm_status(resident="helen", root=rootp)
    store = HelenWorkforceStore(rootp)
    workforce_status = store.write_status()
    helen_identity = resolve_personnel_identity("Helen", root=rootp)
    authority = check_authority("Helen", "hiring_recommendation", target="Grace", source_refs=["docs/residents/helen/Helen_Hiring_Onboarding_Workflow_v0_1.md"])
    grace_office_evidence = [_evidence(rootp, "docs/residents/grace/Grace_Resident_Profile_v0_1.md"), _evidence(rootp, "docs/residents/helen/Helen_Hiring_Onboarding_Workflow_v0_1.md")]
    grace_package_evidence = [_evidence(rootp, "docs/residents/grace/Grace_Resident_Profile_v0_1.md"), _evidence(rootp, "docs/residents/grace/Grace_Resident_Validation_v0_1.md"), _evidence(rootp, "docs/residents/grace/platform-exports/textgen-4_9-grace-v0_1.yaml")]
    grace_registered = any(str(r.get("name", "")).lower() == "grace" and str(r.get("status","")).lower() in {"active","onboarding"} for r in residents)
    grace_activation_authorized = _exists(rootp, "runtime/onboarding/grace/steward_activation_decision.json")

    gates = [
        _gate("G1", "Helen resident identity resolves", bool(helen), [_evidence(rootp,"data/registry/residents.json")], ["Helen resident registry row"] if not helen else [], "Register Helen in data/registry/residents.json."),
        _gate("G2", "Helen chat uses Helen-specific prompt", "You are Helen" in prompt_text and "Human Resources" in prompt_text, [_evidence(rootp,p) for p in prompt_files], ["Helen-specific prompt/profile text"] if not prompt_text else [], "Restore Helen v0.2 prompt artifacts."),
        _gate("G3", "Local provider or truthful fallback state is visible", bool(llm.get("provider_reachable") or llm.get("fallback_active") is not None), [{"path":"runtime/model_control/registry.json","exists":_exists(rootp,"runtime/model_control/registry.json"),"llm_state":llm.get("provider_reachable"),"fallback_active":llm.get("fallback_active")}], [], "Expose resident LLM diagnostic/fallback state."),
        _gate("G4", "Workforce request and assessment commands operate", bool(workforce_status.get("available")), [{"path":"runtime/workforce_development/status/latest.json","exists":True}], [], "Repair HelenWorkforceStore status generation."),
        _gate("G5", "Privacy and classification boundaries remain intact", workforce_status.get("constitutional_authority_granted") is False and workforce_status.get("provider_execution_performed") is False, [{"path":"src/estate/core/helen_workforce.py","exists":True}], [], "Restore false authority/execution flags."),
        _gate("G6", "Employee identity, mailbox, office, reporting line, and security rating resolve", bool(helen_identity.get("resolved") and helen_identity.get("mailbox_id")), [_evidence(rootp,"data/registry/personnel.json"), _evidence(rootp,"data/registry/mailboxes.json")], [], "Repair Helen personnel and mailbox registry rows."),
        _gate("G7", "Helen can produce governed hiring recommendation without granting authority", authority.get("allowed") is False, [{"path":"src/estate/core/resident_authority.py","exists":True}, _evidence(rootp,"docs/residents/helen/Helen_Hiring_Onboarding_Workflow_v0_1.md")], [], "Keep hiring recommendation advisory unless governed authority is implemented."),
        _gate("G8", "Grace office and role authorization evidence exists", all(e["exists"] for e in grace_office_evidence), grace_office_evidence, [e["path"] for e in grace_office_evidence if not e["exists"]], "Create/approve Grace Office of Operations authorization evidence."),
        _gate("G9", "Grace resident package and validation artifacts exist", all(e["exists"] for e in grace_package_evidence), grace_package_evidence, [e["path"] for e in grace_package_evidence if not e["exists"]], "Complete Grace resident profile, export, and deterministic validation artifacts."),
        _gate("G10", "Steward-reserved appointment or activation is authorized before Grace registry exposure", (not grace_registered) or grace_activation_authorized, [_evidence(rootp,"data/registry/residents.json"), _evidence(rootp,"runtime/onboarding/grace/steward_activation_decision.json")], ["Grace registry exposure requires Steward appointment/activation evidence"] if grace_registered and not grace_activation_authorized else [], "Remove unauthorized Grace exposure or record Steward activation authority."),
    ]
    failed = [g for g in gates if not g["passed"]]
    grace_blockers = [g for g in gates[7:] if not g["passed"]]
    status = "ready" if not failed else ("ready_with_limitations" if not grace_blockers and all(g["gate_id"] not in {"G1","G2","G4","G5","G6","G7"} for g in failed) else "not_ready")
    payload = {"schema_version":"helen_operational_readiness.v1","generated_at":utc_now_iso(),"resident":"Helen","overall_status":status,"grace_hiring_gate":"blocked" if grace_blockers or status=="not_ready" else "eligible_for_steward_review","authority_flags":{"constitutional_authority_granted":False,"provider_execution_performed":False,"operational_queue_control_performed":False,"grace_appointed_or_activated":grace_activation_authorized},"gates":gates,"missing_evidence":[m for g in failed for m in g["missing_evidence"]],"next_actions":[g["next_action"] for g in failed if g.get("next_action")],"helen_identity":helen,"helen_personnel_resolution":helen_identity,"llm_status":{"provider_reachable":llm.get("provider_reachable"),"fallback_active":llm.get("fallback_active"),"selection_source":llm.get("selection_source")},"workforce_status_summary":workforce_status.get("summary"),"grace_registered_or_active":grace_registered,"grace_activation_authorized":grace_activation_authorized}
    if write:
        _write_json(rootp / READINESS_PATH, payload)
        render_report(payload, rootp / REPORT_PATH)
        _write_json(rootp / SURFACE_PATH, {"resident":"Helen","readiness_path":str(READINESS_PATH),"overall_status":status,"grace_hiring_gate":payload["grace_hiring_gate"],"authority_flags":payload["authority_flags"],"generated_at":payload["generated_at"]})
    return payload


def render_report(payload: dict[str, Any], path: Path) -> None:
    lines = ["# Helen Operational Readiness Report", "", f"Generated: {payload['generated_at']}", f"Overall status: `{payload['overall_status']}`", f"Grace hiring gate: `{payload['grace_hiring_gate']}`", "", "## Gate Results", ""]
    for g in payload["gates"]:
        lines.append(f"- {'PASS' if g['passed'] else 'FAIL'} — {g['gate_id']}: {g['name']}")
        if not g["passed"]:
            lines.append(f"  - Missing evidence: {', '.join(g['missing_evidence']) or 'unspecified'}")
            lines.append(f"  - Next action: {g['next_action']}")
    lines += ["", "## Authority Flags", "", "Helen authority flags remain false for constitutional authority, provider execution, and operational queue control; Grace appointment/activation may be true only when separately Steward-authorized."]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
