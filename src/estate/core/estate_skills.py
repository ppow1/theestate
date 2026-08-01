"""Canonical, executor-neutral Estate Skill registry and governance helpers.

Skills are procedures, not authority, capabilities, providers, or residents.
This module intentionally performs only local validation and read-only discovery.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SKILL_ID = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
VERSION = re.compile(r"^\d+\.\d+\.\d+$")
ALLOWED_TOP = {"schema_version", "registry_id", "authority", "skills"}
ALLOWED_MANIFEST = {"skill_id","version","name","aliases","owner","maintainer","purpose","outcomes","trigger_classes","required_capabilities","allowed_providers_tools","bootstrap_dependencies","classification","authority","scope","stages","preconditions","stop_and_escalation","idempotency","contracts","rollback","maturity","availability","institutional_acceptance","examples"}

class SkillError(ValueError):
    pass

class SkillAmbiguity(SkillError):
    pass

def _walk(value: Any, path: str = ""):
    yield path, value
    if isinstance(value, dict):
        for k, v in value.items(): yield from _walk(v, f"{path}.{k}" if path else k)
    elif isinstance(value, list):
        for i, v in enumerate(value): yield from _walk(v, f"{path}[{i}]")

def _safe_ref(value: Any) -> bool:
    if not isinstance(value, str) or not value or "${" in value or "{{" in value:
        return False
    p = value.replace("\\", "/")
    return not (p.startswith("/") or re.match(r"^[A-Za-z]:/", p) or any(x == ".." for x in p.split("/")))

def validate_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(manifest, dict): raise SkillError("manifest must be an object")
    unknown = set(manifest) - ALLOWED_MANIFEST
    if unknown: raise SkillError(f"unknown manifest fields: {sorted(unknown)}")
    for key in ("skill_id", "version", "name", "purpose", "owner", "maintainer", "scope", "stages", "stop_and_escalation", "contracts", "maturity", "availability", "institutional_acceptance"):
        if key not in manifest: raise SkillError(f"missing required field: {key}")
    if not SKILL_ID.fullmatch(str(manifest["skill_id"])): raise SkillError("invalid skill_id")
    if not VERSION.fullmatch(str(manifest["version"])): raise SkillError("invalid semantic version")
    if not isinstance(manifest.get("aliases"), list) or not manifest["aliases"]: raise SkillError("aliases must be non-empty")
    if not isinstance(manifest["stages"], list) or not manifest["stages"]: raise SkillError("stages must be non-empty")
    stop = manifest["stop_and_escalation"]
    if not isinstance(stop, dict) or not all(stop.get(k) for k in ("stop_conditions", "escalation", "timeout", "partial_result")): raise SkillError("stop/escalation/timeout/partial-result contract required")
    for path, value in _walk(manifest):
        if isinstance(value, str) and ("${" in value or "{{" in value): raise SkillError(f"unresolved placeholder at {path}")
    for key in ("reads", "writes", "outputs", "external_sinks"):
        for ref in manifest.get("scope", {}).get(key, []):
            if not _safe_ref(ref): raise SkillError(f"unsafe or unresolved scope reference: {ref}")
    if manifest.get("authority", {}).get("implicit"): raise SkillError("implicit authority is prohibited")
    if manifest.get("scope", {}).get("wildcards") and not manifest["scope"].get("bounded_policy"): raise SkillError("wildcards require bounded_policy")
    return manifest

@dataclass(frozen=True)
class SkillRegistry:
    skills: tuple[dict[str, Any], ...]
    registry_id: str
    authority: str

    @classmethod
    def load(cls, path: str | Path) -> "SkillRegistry":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        unknown = set(payload) - ALLOWED_TOP
        if unknown: raise SkillError(f"unknown registry fields: {sorted(unknown)}")
        if payload.get("schema_version") != "estate.skill.registry.v1": raise SkillError("unsupported registry schema")
        skills = tuple(validate_manifest(x) for x in payload.get("skills", []))
        seen: dict[str, str] = {}
        for skill in skills:
            for alias in [skill["name"], skill["skill_id"], *skill["aliases"]]:
                key = str(alias).casefold()
                if key in seen: raise SkillAmbiguity(f"duplicate Skill name or alias: {alias}")
                seen[key] = skill["skill_id"]
        return cls(skills, str(payload.get("registry_id", "canonical")), str(payload.get("authority", "derived_read_only")))

    def discover(self, query: str | None = None, *, owner: str | None = None, outcome: str | None = None) -> list[dict[str, Any]]:
        q = query.casefold().strip() if query else None
        out = []
        for skill in self.skills:
            hay = [skill["skill_id"], skill["name"], *skill["aliases"], skill["owner"], skill["purpose"], *skill.get("outcomes", [])]
            if q and not any(q in str(x).casefold() for x in hay): continue
            if owner and owner.casefold() not in str(skill["owner"]).casefold(): continue
            if outcome and not any(outcome.casefold() in str(x).casefold() for x in skill.get("outcomes", [])): continue
            out.append({"skill_id":skill["skill_id"],"version":skill["version"],"name":skill["name"],"aliases":skill["aliases"],"purpose":skill["purpose"],"outcomes":skill.get("outcomes",[]),"maturity":skill["maturity"],"availability":skill["availability"],"institutional_acceptance":skill["institutional_acceptance"]})
        return out

    def proposal(self, steward_words: str, query: str) -> dict[str, Any]:
        matches = self.discover(query)
        return {"status":"proposal_only","executed":False,"steward_request":steward_words,"matches":matches,"next_step":"explicit execute-now request plus required authority"}

def assess_readiness(manifest: dict[str, Any], *, capabilities=None, providers=None, workers=None, authority=False) -> dict[str, Any]:
    capabilities, providers, workers = capabilities or {}, providers or {}, workers or {}
    gaps=[]
    for dep in manifest.get("required_capabilities", []):
        state=capabilities.get(dep.get("id"), {})
        if not state.get("available") or state.get("maturity", 0) < dep.get("minimum_maturity", 0): gaps.append({"kind":"capability","id":dep.get("id"),"reason":"missing_or_below_maturity"})
    for dep in manifest.get("bootstrap_dependencies", []):
        if not dep.get("available", False): gaps.append({"kind":"bootstrap","id":dep.get("id"),"reason":"unavailable"})
    if not workers.get(manifest["maintainer"], {}).get("qualified", True): gaps.append({"kind":"worker","id":manifest["maintainer"],"reason":"not_qualified"})
    if not authority and manifest.get("authority", {}).get("required"): gaps.append({"kind":"authority","reason":"missing_explicit_authority"})
    return {"skill_id":manifest["skill_id"],"historical_maturity":manifest["maturity"],"availability":manifest["availability"],"institutional_acceptance":manifest["institutional_acceptance"],"dispatchable":not gaps,"gaps":gaps}

def validate_receipt(receipt: dict[str, Any]) -> bool:
    required=("schema_version","receipt_id","invocation_id","skill_id","status","artifacts","validation","reconciliation","terminal_result")
    if any(k not in receipt for k in required): raise SkillError("receipt contract incomplete")
    if receipt["status"] not in {"completed","blocked","failed","partial"}: raise SkillError("invalid terminal status")
    return True

def reconcile(receipt: dict[str, Any], *, report_exists: bool) -> dict[str, Any]:
    validate_receipt(receipt)
    return {"status":"reconciled" if report_exists and receipt["status"] == "completed" else "attention_required","invocation_id":receipt["invocation_id"],"institutional_acceptance":"not_granted"}

def grace_discover(registry: SkillRegistry, steward_words: str) -> dict[str, Any]:
    return {"request_provenance":steward_words,"discovery":registry.proposal(steward_words, steward_words),"executed":False}
