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
        OperationalTarget('estate-main','Estate Main','git_repository','Estate', 'ppow1/theestate', root_path, 'main', capabilities=['git','validation','audit'], watch_state='enabled', watch_enabled=True),
        OperationalTarget('cue-mastery','CueMastery','engineering_project','Engineering', capabilities=['git','validation','audit'], watch_state='import_candidate'),
        OperationalTarget('ionoge-vps','Ionoge VPS','infrastructure_node','Infrastructure', capabilities=['service-health','deploy'], watch_state='import_candidate'),
        OperationalTarget('ionoge-site','Ionoge Site','service','Infrastructure', capabilities=['service-health','deploy'], watch_state='import_candidate'),
    ]
