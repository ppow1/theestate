"""Runtime wrapper for merge discovery."""
from __future__ import annotations
from pathlib import Path
from typing import Any
from estate.core.merge_discovery import MergeDiscovery
from estate.core.merge_discovery_consolidation import MergeDiscoveryConsolidator
from estate.core.merge_discovery_admission import MergeDiscoveryAdmission

class MergeDiscoveryRuntime:
    def __init__(self, root:Path|None=None): self.discovery=MergeDiscovery(root)
    def scan(self, target:str="estate-main", max_commits:int=100, **kw)->dict[str,Any]: return self.discovery.scan(target, max_commits=max_commits, **kw)
    def replay(self, target:str="estate-main", max_commits:int=50, **kw)->dict[str,Any]: return self.discovery.scan(target, max_commits=max_commits, replay=True, **kw)
    def status(self, target:str="estate-main")->dict[str,Any]: return self.discovery.status(target)
    def candidates(self, target:str="estate-main")->dict[str,Any]: return self.discovery.candidates(target)
    def consolidate(self, target:str="estate-main", **kw)->dict[str,Any]: return MergeDiscoveryConsolidator(self.discovery.root).consolidate(target, **kw)
    def quarantine_status(self, target:str="estate-main")->dict[str,Any]: return MergeDiscoveryConsolidator(self.discovery.root).quarantine_status(target)
    def admit(self, target:str="estate-main", work_package:str="")->dict[str,Any]: return MergeDiscoveryConsolidator(self.discovery.root).admit(target, work_package)
    def admission_status(self, target:str="estate-main")->dict[str,Any]: return MergeDiscoveryAdmission(self.discovery.root).status(target)
    def auto_admit(self, target:str="estate-main", max_requests:int=5)->dict[str,Any]: return MergeDiscoveryAdmission(self.discovery.root).auto_admit(target, max_requests=max_requests)
    def hold(self, target:str="estate-main", work_package:str="")->dict[str,Any]: return MergeDiscoveryAdmission(self.discovery.root).hold(target, work_package)
    def release(self, target:str="estate-main", work_package:str="")->dict[str,Any]: return MergeDiscoveryAdmission(self.discovery.root).release(target, work_package)
    def reconcile_requests(self, target:str="estate-main")->dict[str,Any]: return MergeDiscoveryConsolidator(self.discovery.root).reconcile_requests(target)
