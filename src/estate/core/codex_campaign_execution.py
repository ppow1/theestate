"""Durable, authority-bounded execution state for Codex engineering campaigns.

This module plans work; it deliberately does not merge branches, accept campaigns, or
invoke Codex.  A provider adapter may consume ``next_launches`` and report results.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from estate.core.operational_campaigns import utc_now_iso
from estate.core.paths import ESTATE_ROOT

STATE_DIR = Path("runtime/codex_campaigns")
TERMINAL_PACKAGE_STATES = {"completed", "failed", "skipped"}


@dataclass
class CodexCampaignPackage:
    work_package_id: str
    source: str
    dependencies: list[str] = field(default_factory=list)
    parallel_group: str | None = None
    state: str = "pending"
    commit: str | None = None
    attempts: int = 0
    failure: str | None = None


@dataclass
class CodexCampaignManifest:
    campaign_id: str
    campaign_source: str
    branch: str
    approved_by: str
    packages: list[CodexCampaignPackage]
    review_gates: dict[str, list[str]] = field(default_factory=dict)
    allow_parallel_groups: list[str] = field(default_factory=list)
    status: str = "ready"
    active_gate: str | None = None
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "CodexCampaignManifest":
        payload = dict(value)
        payload["packages"] = [CodexCampaignPackage(**item) for item in payload["packages"]]
        return cls(**payload)

    def validate(self) -> None:
        if not self.approved_by:
            raise ValueError("campaign requires recorded approval")
        if not self.branch or self.branch in {"main", "master"}:
            raise ValueError("campaign requires a non-protected campaign branch")
        ids = [item.work_package_id for item in self.packages]
        if len(ids) != len(set(ids)):
            raise ValueError("work package identifiers must be unique")
        known = set(ids)
        for item in self.packages:
            unknown = set(item.dependencies) - known
            if unknown:
                raise ValueError(f"{item.work_package_id} has unknown dependencies: {sorted(unknown)}")
            if item.parallel_group and item.parallel_group not in self.allow_parallel_groups:
                raise ValueError(f"parallel group {item.parallel_group} is not approved")
        for gate, feeders in self.review_gates.items():
            unknown = set(feeders) - known
            if unknown:
                raise ValueError(f"gate {gate} has unknown packages: {sorted(unknown)}")


class CodexCampaignExecution:
    """Persisted campaign controller with explicit provider/reviewer handoffs."""

    def __init__(self, root: str | Path | None = None) -> None:
        self.root = Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())

    def _path(self, campaign_id: str) -> Path:
        return self.root / STATE_DIR / f"{campaign_id}.json"

    def register(self, manifest: CodexCampaignManifest) -> CodexCampaignManifest:
        manifest.validate()
        if self._path(manifest.campaign_id).exists():
            raise FileExistsError(f"campaign {manifest.campaign_id} is already registered")
        self._save(manifest, "campaign_registered", "Approved campaign registered for execution.")
        return manifest

    def load(self, campaign_id: str) -> CodexCampaignManifest:
        payload = json.loads(self._path(campaign_id).read_text(encoding="utf-8"))
        return CodexCampaignManifest.from_dict(payload["campaign"])

    def start(self, campaign_id: str, *, current_branch: str) -> CodexCampaignManifest:
        campaign = self.load(campaign_id)
        if current_branch != campaign.branch:
            raise ValueError(f"execution must remain on campaign branch {campaign.branch}")
        if campaign.status not in {"ready", "paused"}:
            raise ValueError(f"campaign cannot start from {campaign.status}")
        campaign.status = "running"
        self._save(campaign, "campaign_started", "Campaign execution started.")
        return campaign

    def next_launches(self, campaign_id: str) -> list[str]:
        campaign = self.load(campaign_id)
        if campaign.status != "running":
            return []
        completed = {p.work_package_id for p in campaign.packages if p.state == "completed"}
        eligible = [p for p in campaign.packages if p.state == "pending" and set(p.dependencies) <= completed]
        if not eligible:
            return []
        first = eligible[0]
        if not first.parallel_group:
            return [first.work_package_id]
        # Parallel launch is permitted only inside an explicitly approved group.
        return [p.work_package_id for p in eligible if p.parallel_group == first.parallel_group]

    def mark_running(self, campaign_id: str, work_package_id: str) -> CodexCampaignManifest:
        campaign = self.load(campaign_id)
        if work_package_id not in self.next_launches(campaign_id):
            raise ValueError("work package is not dependency-eligible")
        package = self._package(campaign, work_package_id)
        package.state = "running"
        package.attempts += 1
        self._save(campaign, "package_started", f"{work_package_id} started.", work_package_id=work_package_id)
        return campaign

    def record_commit(self, campaign_id: str, work_package_id: str, commit: str) -> CodexCampaignManifest:
        campaign = self.load(campaign_id)
        package = self._package(campaign, work_package_id)
        if package.state != "running" or package.commit:
            raise ValueError("exactly one commit may be recorded for a running work package")
        if not commit.strip():
            raise ValueError("commit identifier is required")
        package.commit = commit
        package.state = "completed"
        event = "package_completed"
        summary = f"{work_package_id} completed as bounded commit {commit}."
        for gate, feeders in campaign.review_gates.items():
            if work_package_id in feeders and all(self._package(campaign, item).state == "completed" for item in feeders):
                campaign.status = "awaiting_review"
                campaign.active_gate = gate
                event = "review_gate_reached"
                summary = f"Review gate {gate} reached; continuation is paused."
                break
        if all(p.state == "completed" for p in campaign.packages):
            campaign.status = "awaiting_acceptance"
            campaign.active_gate = None
        self._save(campaign, event, summary, work_package_id=work_package_id, commit=commit)
        return campaign

    def fail(self, campaign_id: str, work_package_id: str, reason: str) -> CodexCampaignManifest:
        campaign = self.load(campaign_id)
        package = self._package(campaign, work_package_id)
        if package.state != "running":
            raise ValueError("only a running package may fail")
        package.state = "failed"
        package.failure = reason
        campaign.status = "reconciliation_required"
        self._save(campaign, "package_failed", reason, work_package_id=work_package_id)
        return campaign

    def reconcile(self, campaign_id: str, work_package_id: str, *, action: str) -> CodexCampaignManifest:
        campaign = self.load(campaign_id)
        if campaign.status != "reconciliation_required":
            raise ValueError("campaign does not require reconciliation")
        package = self._package(campaign, work_package_id)
        if package.state != "failed" or action not in {"retry", "skip"}:
            raise ValueError("reconciliation action must retry or skip a failed package")
        package.state = "pending" if action == "retry" else "skipped"
        package.failure = None if action == "retry" else package.failure
        campaign.status = "running" if action == "retry" else "paused"
        self._save(campaign, "campaign_reconciled", f"{work_package_id}: {action}.", work_package_id=work_package_id)
        return campaign

    def approve_gate(self, campaign_id: str, gate: str, *, reviewer: str) -> CodexCampaignManifest:
        campaign = self.load(campaign_id)
        if campaign.status != "awaiting_review" or campaign.active_gate != gate:
            raise ValueError("gate is not awaiting review")
        if not reviewer.strip():
            raise ValueError("reviewer identity is required")
        campaign.active_gate = None
        campaign.status = "running"
        self._save(campaign, "review_gate_approved", f"{gate} approved by {reviewer}.", reviewer=reviewer)
        return campaign

    def _package(self, campaign: CodexCampaignManifest, work_package_id: str) -> CodexCampaignPackage:
        try:
            return next(p for p in campaign.packages if p.work_package_id == work_package_id)
        except StopIteration as error:
            raise KeyError(work_package_id) from error

    def _save(self, campaign: CodexCampaignManifest, event: str, summary: str, **details: Any) -> None:
        campaign.updated_at = utc_now_iso()
        path = self._path(campaign.campaign_id)
        history: list[dict[str, Any]] = []
        if path.exists():
            history = json.loads(path.read_text(encoding="utf-8")).get("history", [])
        history.append({"event": event, "timestamp": campaign.updated_at, "summary": summary, **details})
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"version": 1, "campaign": asdict(campaign), "history": history}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
