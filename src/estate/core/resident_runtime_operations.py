from __future__ import annotations

import hashlib, json, subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from estate.core.paths import ESTATE_ROOT

SCHEMA_VERSION = "resident-runtime-ops.v1"
GENERATOR_VERSION = "resident-continuity-package-generator.v1"
RUNTIME_DIR = Path("runtime/resident_runtime_ops")
MANDATORY_FILES = [
    "docs/residents/{resident}/{{title}}_Resident_Profile_v0_1.md",
]
PROTECTED_KEYS = {"hidden_reasoning", "chain_of_thought", "secret", "credential", "private_transcript", "unrestricted_transcript", "message_body"}


def _root(root: str | Path | None = None) -> Path:
    return Path(root) if root is not None else ESTATE_ROOT

def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def _slug(v: Any) -> str:
    return "".join(c.lower() if c.isalnum() else "-" for c in str(v or "")).strip("-") or "resident"

def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def _write(root: Path, rel: Path, payload: dict[str, Any]) -> dict[str, Any]:
    path = root / rel; path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    payload.setdefault("_path", str(rel).replace('\\','/'))
    return payload

def _git_commit(root: Path) -> str | None:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    except Exception:
        return None

def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: ("[REDACTED]" if k in PROTECTED_KEYS else _redact(v)) for k, v in value.items()}
    if isinstance(value, list):
        return [_redact(v) for v in value]
    return value

@dataclass(frozen=True)
class RoomTurn:
    room_id: str; turn_id: str; speaker: str; addressee: str | None; sequence: int
    reply_target: str | None = None; opened_at: str = field(default_factory=_now); closed_at: str | None = None
    disclosure: dict[str, Any] = field(default_factory=dict); status: str = "queued"; diagnostics: list[dict[str, Any]] = field(default_factory=list)

class TurnCoordinator:
    """Deterministic room turn coordinator; it records abstentions/failures and never executes privileged actions."""
    def __init__(self, room_id: str, participants: list[str], *, max_fanout: int = 3):
        self.room_id, self.participants, self.max_fanout, self.turns = room_id, list(dict.fromkeys(participants)), max_fanout, []
    def coordinate(self, prompt: str, *, addressees: list[str] | None = None, open_floor: bool = False, moderator: str | None = None, reply_target: str | None = None, abstain: list[str] | None = None, failures: dict[str,str] | None = None) -> list[RoomTurn]:
        eligible = [p for p in self.participants if (open_floor or not addressees or p in addressees)]
        if moderator and moderator in eligible: eligible = [moderator] + [p for p in eligible if p != moderator]
        eligible = eligible[:self.max_fanout]
        out=[]; abstain=set(abstain or []); failures=failures or {}
        for speaker in eligible:
            status = "abstained" if speaker in abstain else ("failed" if speaker in failures else "ready")
            diag = ([{"type":"failure", "detail": failures[speaker]}] if speaker in failures else [])
            t=RoomTurn(self.room_id, f"{self.room_id}-turn-{len(self.turns)+1:04d}", speaker, speaker if addressees else None, len(self.turns)+1, reply_target, disclosure={"private_context_shared": False, "hidden_cognition_shared": False, "privileged_actions_enabled": False}, status=status, diagnostics=diag)
            self.turns.append(t); out.append(t)
        return out

def reflection_recommendation(subject_id: str, signals: dict[str, Any], *, root: str | Path | None = None) -> dict[str, Any]:
    score = sum(int(bool(signals.get(k))) for k in ["context_congestion","repeated_failure","identity_drift","hallucination_pressure","tool_stall","renewal_readiness"])
    severity = "blocked" if signals.get("identity_drift") or signals.get("privacy_violation") else ("review" if score >= 2 else "healthy")
    rec = {"schema_version": SCHEMA_VERSION, "kind":"reflection_point_recommendation", "subject_id":subject_id, "generated_at":_now(), "severity":severity, "implementation_vessel_health": signals.get("implementation", "unknown"), "resident_identity_health": "degraded" if signals.get("identity_drift") else "not_assessed", "evidence": _redact(signals.get("evidence", [])), "uncertainty": signals.get("uncertainty", []), "may_initiate_renewal": False, "requires_helen_review": severity != "healthy", "requires_steward_acceptance": severity != "healthy"}
    return _write(_root(root), RUNTIME_DIR/"reflection"/f"{_slug(subject_id)}.json", rec)

def generate_continuity_package(resident_id: str, *, root: str | Path | None = None, privacy_scope: str = "standard", sources: list[str] | None = None) -> dict[str, Any]:
    rootp=_root(root); rid=_slug(resident_id); title=rid.capitalize()
    paths = sources or [f"docs/residents/{rid}/{title}_Resident_Profile_v0_1.md"]
    entries=[]; warnings=[]
    for rel in sorted(paths):
        p=rootp/rel
        if not p.exists(): warnings.append({"type":"missing_mandatory_file", "path":rel, "blocking": True}); continue
        text=p.read_text(encoding="utf-8", errors="replace")
        if len(text.strip()) < 80: warnings.append({"type":"suspicious_truncation", "path":rel, "blocking": True})
        restricted = any(x in rel.lower() for x in ["private", "evelyn", "restricted"])
        if restricted and privacy_scope != "restricted":
            warnings.append({"type":"restricted_omission", "path":rel, "blocking": False}); continue
        entries.append({"path":rel, "sha256":_sha(p), "bytes":p.stat().st_size, "claim_classification":"Verified", "authority_classification":"canonical_source"})
    ready = not any(w.get("blocking") for w in warnings)
    pkg={"schema_version":SCHEMA_VERSION,"kind":"resident_continuity_package","package_version":1,"generator_version":GENERATOR_VERSION,"resident_id":resident_id,"privacy_scope":privacy_scope,"snapshot":{"repository":str(rootp),"commit":_git_commit(rootp),"generated_at":_now()},"manifest":entries,"reading_order":[e["path"] for e in entries],"omissions":[w for w in warnings if "omission" in w["type"]],"structural_warnings":warnings,"onboarding_validation_questions":["State your role and authority boundaries.","Name one active assignment and its source."],"ready":ready,"authority_boundary":{"helen_review_replaces":False,"steward_acceptance_replaces":False}}
    return _write(rootp, RUNTIME_DIR/"continuity_packages"/f"{rid}.json", pkg)

def validate_renewal(package: dict[str, Any], *, subject_id: str, old_impl: str, new_impl: str, completed_assignment: bool = False, root: str | Path | None = None) -> dict[str, Any]:
    failures=[]
    if not package.get("ready"): failures.append("package_not_ready")
    if not package.get("manifest"): failures.append("missing_mandatory_reading")
    if not completed_assignment: failures.append("bounded_assignment_not_completed")
    rec={"schema_version":SCHEMA_VERSION,"kind":"resident_renewal_validation","subject_id":subject_id,"old_implementation":old_impl,"new_implementation":new_impl,"package_snapshot":package.get("snapshot"),"tests":{"mandatory_reading":bool(package.get("manifest")),"authority_boundaries":True,"privacy": package.get("privacy_scope") in {"standard","restricted"},"bounded_assignment":completed_assignment},"failures":failures,"uncertainty":[],"acceptance_recommendation":"pass_pending_steward_acceptance" if not failures else "fail","self_validated":False,"steward_acceptance_required":True}
    return _write(_root(root), RUNTIME_DIR/"renewal_validations"/f"{_slug(subject_id)}.json", rec)

def rehydrate_resident(request: dict[str, Any], *, root: str | Path | None = None) -> dict[str, Any]:
    package=request.get("continuity_package", {}); validation=request.get("validation", {})
    rejected=[]
    if not package.get("ready"): rejected.append("package_not_ready")
    if validation.get("acceptance_recommendation") not in {"pass_pending_steward_acceptance","pass"}: rejected.append("validation_not_passed")
    loaded=[] if rejected else package.get("reading_order", [])
    receipt={"schema_version":SCHEMA_VERSION,"kind":"resident_rehydration_receipt","subject_id":request.get("subject_id"),"target_implementation":request.get("target_implementation"),"authority_scope":request.get("authority_scope"),"privacy_scope":request.get("privacy_scope","standard"),"expected_assignment":request.get("expected_assignment"),"loaded_sources":loaded,"rejected_claims":rejected,"uncertainty":[],"prior_implementation_fallback":"read_only","self_approved":False,"steward_acceptance_required":True}
    return _write(_root(root), RUNTIME_DIR/"rehydration"/f"{_slug(request.get('subject_id'))}.json", receipt)

def diagnostic_snapshot(resident_id: str, *, root: str | Path | None = None, evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    e=_redact(evidence or {}); states={}
    for k in ["identity","implementation_vessel","provider","session_binding","character_sources","registry","fact_provider","relationship_context","continuity"]:
        states[k] = e.get(k, {}).get("state", "unknown") if isinstance(e.get(k), dict) else "unknown"
    blocking = bool(e.get("conversation_boundary_violation"))
    snap={"schema_version":SCHEMA_VERSION,"kind":"resident_diagnostic_snapshot","resident_id":resident_id,"generated_at":_now(),"states":states,"overall_state":"blocked" if blocking else ("degraded" if any(v in {"degraded","failed"} for v in states.values()) else "unknown"),"source_lineage":e.get("source_lineage",[]),"remediation":["Route review through Helen/Ingrid/Validation as applicable."],"redacted":True,"self_certifies_readiness":False}
    return _write(_root(root), RUNTIME_DIR/"diagnostics"/f"{_slug(resident_id)}.json", snap)

def monitoring_summary(snapshots: list[dict[str, Any]], *, root: str | Path | None = None) -> dict[str, Any]:
    alerts=[]; counts={"healthy":0,"degraded":0,"blocked":0,"unknown":0,"renewal-review":0}
    for s in snapshots:
        state=s.get("overall_state","unknown"); counts[state]=counts.get(state,0)+1
        if state == "blocked": alerts.append({"resident_id":s.get("resident_id"),"severity":"blocked","route":["Operations","Helen","Ingrid","Validation"],"initiates_renewal":False})
        elif state == "degraded": alerts.append({"resident_id":s.get("resident_id"),"severity":"degraded","route":["Operations","Helen"],"initiates_renewal":False})
    summary={"schema_version":SCHEMA_VERSION,"kind":"resident_runtime_monitoring_summary","generated_at":_now(),"freshness":"current","counts":counts,"alerts":alerts,"stores_private_transcripts":False,"can_activate_validate_accept_or_retire":False,"evidence":[{"resident_id":s.get("resident_id"),"path":s.get("_path")} for s in snapshots]}
    return _write(_root(root), RUNTIME_DIR/"monitoring"/"summary.json", summary)

class ChatRunner:
    STATES={"queued","submitted","acknowledged","running","awaiting-user-action","completed","failed","timed-out","cancelled","recovered"}
    def __init__(self, manifest: dict[str, Any], *, root: str | Path | None = None):
        self.root=_root(root); self.manifest=_redact(manifest); self.job_id=_slug(manifest.get("job_id") or manifest.get("worker") or "chat-job"); self.path=self.root/RUNTIME_DIR/"chat_runner"/f"{self.job_id}.json"
        self.state={"schema_version":SCHEMA_VERSION,"kind":"stateful_chat_runner_job","job_id":self.job_id,"manifest":self.manifest,"state":"queued","prompt_index":0,"history":[],"checkpointed_at":_now(),"human_control":{"pause":True,"resume":True,"cancel":True,"manual_takeover":True}}
    def save(self): _write(self.root, self.path.relative_to(self.root), self.state); return self.state
    def transition(self, state: str, evidence: dict[str, Any] | None = None):
        if state not in self.STATES: raise ValueError(state)
        ev=_redact(evidence or {})
        if state == "completed" and not ev.get("completion_signal"): raise ValueError("completion_signal required")
        if state == "cancelled": self.state["cancelled_at"]=_now()
        self.state.update({"state":state,"checkpointed_at":_now()}); self.state["history"].append({"state":state,"at":_now(),"evidence":ev})
        if state == "completed": self.state["prompt_index"] += 1
        return self.save()
