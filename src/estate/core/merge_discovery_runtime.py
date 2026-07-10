"""Runtime wrapper for merge discovery."""
from __future__ import annotations
from pathlib import Path
from typing import Any
from estate.core.merge_discovery import MergeDiscovery

class MergeDiscoveryRuntime:
    def __init__(self, root:Path|None=None): self.discovery=MergeDiscovery(root)
    def scan(self, target:str="estate-main", max_commits:int=100)->dict[str,Any]: return self.discovery.scan(target, max_commits=max_commits)
    def replay(self, target:str="estate-main", max_commits:int=50)->dict[str,Any]: return self.discovery.scan(target, max_commits=max_commits, replay=True)
    def status(self, target:str="estate-main")->dict[str,Any]: return self.discovery.status(target)
    def candidates(self, target:str="estate-main")->dict[str,Any]: return self.discovery.candidates(target)
