"""Post-merge audit request and verdict models."""
from __future__ import annotations
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4
VERDICTS={"accepted","accepted_with_notes","ring2_required","needs_repair","blocked","not_merged","workspace_failed","validation_failed"}
def utc_now_iso(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
@dataclass
class PostMergeAuditRequest:
    audit_id:str; target_id:str; work_package_id:str; source_kind:str; source_reference:str; expected_files:list[str]=field(default_factory=list); created_at:str=field(default_factory=utc_now_iso); metadata:dict[str,Any]=field(default_factory=dict)
    @classmethod
    def create(cls,target_id,work_package_id,source_kind='merge',source_reference='HEAD',expected_files=None,metadata=None): return cls('pma-'+uuid4().hex,target_id,work_package_id,source_kind,source_reference,expected_files or [],metadata=metadata or {})
    def to_dict(self): return asdict(self)
    @classmethod
    def from_dict(cls,d): return cls(**{k:d.get(k) for k in cls.__dataclass_fields__})  # type: ignore
@dataclass
class PostMergeAuditVerdict:
    audit_id:str; target_id:str; work_package_id:str; source_kind:str; source_reference:str; verdict:str; merge_or_promotion_verified:bool; validation_workspace_clean:bool; validation_workspace_on_expected_branch:bool; expected_files_present:bool; deterministic_validation_status:str; production_ready:bool; receipt_status:str; ring2_status:str; ring2_verdict:str|None; provider_execution_performed:bool; dispatch_execution_performed:bool; blocking_reasons:list[str]=field(default_factory=list); non_blocking_findings:list[str]=field(default_factory=list); artifacts:dict[str,str]=field(default_factory=dict); created_at:str=field(default_factory=utc_now_iso); metadata:dict[str,Any]=field(default_factory=dict)
    def to_dict(self):
        if self.verdict not in VERDICTS: raise ValueError(f'unknown verdict {self.verdict}')
        return asdict(self)
