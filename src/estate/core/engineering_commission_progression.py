"""Engineering-owned CME adapter. It revalidates before using existing Dispatch."""
from __future__ import annotations
from typing import Any
from estate.core.grace_momentum_directive import load as load_directive
from estate.core.grace_helen_engineering_composition import GraceHelenEngineeringComposition, _load, COMMISSIONS

class EngineeringCommissionProgressionHandler:
 def __init__(self,root): self.root=root;self.composition=GraceHelenEngineeringComposition(root)
 def progress(self,directive_id:str,commission_id:str,*,provider_id:str="fixture-provider",provider_type:str="fixture") -> dict[str,Any]:
  d=load_directive(directive_id,self.root)
  if d["status"]!="active" or "engineering_progression" not in d["allowed_automatic_transition_classes"]: raise PermissionError("Grace momentum continuation is not active")
  c=_load(self.composition._path(COMMISSIONS,commission_id))
  if c["grace_objective_id"]!=d["grace_objective_id"]: raise ValueError("directive and commission objective mismatch")
  if c["status"] not in {"accepted","authorized_for_dispatch"}: raise PermissionError("Engineering commission is not accepted")
  if c["status"]=="authorized_for_dispatch": return {"status":"duplicate_effect_suppressed","commission_id":commission_id}
  # Record a fail-closed governance verdict before Dispatch. Fixture providers
  # are the only permitted default; live providers require a separately supplied
  # admitted/healthy/capable evidence envelope.
  det=_load(self.composition._path(__import__('estate.core.grace_helen_engineering_composition',fromlist=['DETERMINATIONS']).DETERMINATIONS,c["helen_determination_id"]))
  checks={"admitted":provider_id=="fixture-provider","capability_match":bool(c.get("required_capability")),"health":"available" if provider_id=="fixture-provider" else "unknown","capacity":"available" if provider_id=="fixture-provider" else "unknown","qualification":det.get("disposition")=="qualified_and_available","locality":d.get("locality")=="local_only","privacy_egress":d.get("privacy_egress")=="no_external_egress","no_spend":d.get("spend")=="no_spend","authority":bool(d.get("grace_authority_reference")),"live_provider_called":False}
  if not all([checks["admitted"],checks["capability_match"],checks["qualification"],checks["locality"],checks["privacy_egress"],checks["no_spend"],checks["authority"]]) or checks["health"]!="available" or checks["capacity"]!="available": raise PermissionError("provider governance revalidation failed")
  auth,item=self.composition.authorize_dispatch(commission_id,provider_id=provider_id,provider_type=provider_type,adapter_reference="engineering_commission_progression")
  return {"status":"authorized_for_dispatch","authorization":auth,"dispatch":item,"provider_governance_checks":checks,"evidence_reference":auth["dispatch_record_path"]}
