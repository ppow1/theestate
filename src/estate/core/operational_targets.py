"""Operational target registry models for Background Operations."""
from __future__ import annotations
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

WATCH_STATES={"enabled","paused","disabled","retired","import_candidate","blocked"}
CAPABILITIES={"git","validation","audit","build","deploy","service-health"}
TARGET_TYPES={"git_repository","codex_environment","local_workspace","service","infrastructure_node","ai_service","model_library","engineering_project","department_system"}

def utc_now_iso(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')

def default_validation_root()->str: return "A:/EstateRuntime/validation"
def default_workspace_root(target_id:str)->str: return f"A:/EstateRuntime/workspaces/audit/{target_id}"

@dataclass
class OperationalTarget:
    target_id:str
    display_name:str
    target_type:str
    owner_department:str
    repository_full_name:str|None=None
    local_path:str|None=None
    aliases:list[str]=field(default_factory=list)
    environment_names:list[str]=field(default_factory=list)
    base_branch:str="main"
    validation_root:str|None=None
    workspace_root:str|None=None
    watch_enabled:bool=False
    watch_state:str="disabled"
    capabilities:list[str]=field(default_factory=list)
    acceptance_authority:str="Chief Architect / Steward"
    office_surface:bool=True
    classification:str="Estate Internal"
    metadata:dict[str,Any]=field(default_factory=dict)

    def validate(self):
        if not self.target_id or not self.display_name: raise ValueError('target_id and display_name are required')
        if self.target_type not in TARGET_TYPES: raise ValueError(f"unknown target_type '{self.target_type}'")
        if self.watch_state not in WATCH_STATES: raise ValueError(f"unknown watch_state '{self.watch_state}'")
        if self.aliases is None: self.aliases=[]
        if self.environment_names is None: self.environment_names=[]
        unknown=[c for c in self.capabilities if c not in CAPABILITIES]
        if unknown: raise ValueError(f"unknown capabilities {unknown}")
        if self.watch_state in {"enabled"}: self.watch_enabled=True
        if self.watch_state in {"paused","disabled","retired","blocked","import_candidate"}: self.watch_enabled=False
        if self.validation_root is None: self.validation_root=default_validation_root()
        if self.workspace_root is None: self.workspace_root=default_workspace_root(self.target_id)
    def to_dict(self): self.validate(); return asdict(self)
    @classmethod
    def from_dict(cls,d):
        obj=cls(**{k:d.get(k) for k in cls.__dataclass_fields__})  # type: ignore
        obj.validate(); return obj

@dataclass
class OperationalTargetStatus:
    generated_at:str
    available_targets:list[dict[str,Any]]
    watched_targets:list[str]
    paused_targets:list[str]
    blocked_targets:list[str]
    import_candidates:list[str]
    last_watch_cycle:str|None=None
    latest_audit_verdict_by_target:dict[str,Any]=field(default_factory=dict)
    latest_git_hygiene_issue_by_target:dict[str,Any]=field(default_factory=dict)
    validation_evidence_root:str=field(default_factory=default_validation_root)
    warnings:list[str]=field(default_factory=list)
    def to_dict(self): return asdict(self)

def default_targets(root_path:str|None=None)->list[OperationalTarget]:
    return [
        OperationalTarget('estate-main','Estate Main','git_repository','Estate', 'ppow1/theestate', root_path, aliases=['estate','theestate','ppow1/theestate'], environment_names=['production','estate-main'], base_branch='main', capabilities=['git','validation','audit','service-health'], watch_state='enabled', watch_enabled=True, metadata={'environment':'production','production_target':True,'managed_checkout_path':root_path,'live_target_path':root_path,'upstream':'origin','publication_required':True,'publication_authorized':True,'publication':{'required':True,'authorized':True,'handler':'publish_controller_mutation'},'allowed_remediations':['create_declared_runtime_directories','update_activation_ledger','publish_controller_mutation'],'activation_requirements':{'ledger':True},'validation_recipe':[['python','-m','pytest','tests/test_operational_readiness_closure.py','-q'],['python','-m','py_compile','src/estate/core/operational_readiness_closure.py','src/estate/core/operational_targets.py','src/estate/cli/main.py']],'observation_policy':{'checks_required':2,'min_elapsed_seconds':60,'health_checks':[['python','-c','from pathlib import Path; assert Path("src/estate/core/operational_readiness_closure.py").is_file()']],'restart_events_required':0,'restart_not_applicable_rationale':'Repository/controller target has no managed long-running service restart event.'},'readiness_policy':{'production':True,'environment':'production','min_runtime_cycles':2,'compile_only_sufficient':False,'restart_required':False,'required_publication_sync':'0 0','policy_version':'WP-0654-estate-main-production-readiness-v1'},'acceptance_authority':'Chief Architect / Steward','evidence_location':'runtime/operational_readiness/evidence'}),
        OperationalTarget('cue-mastery','CueMastery','engineering_project','Engineering', aliases=['cue-mastery','CueMastery'], capabilities=['git','validation','audit'], watch_state='import_candidate'),
        OperationalTarget('ionoge-vps','Ionoge VPS','infrastructure_node','Infrastructure', capabilities=['service-health','deploy'], watch_state='import_candidate'),
        OperationalTarget('ionoge-site','Ionoge Site','service','Infrastructure', capabilities=['service-health','deploy'], watch_state='import_candidate'),
    ]
