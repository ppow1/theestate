"""Runtime for governed operational campaigns."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from estate.core.execution_dispatch import DispatchRequest, enqueue_dispatch_request
from estate.core.operational_campaigns import OperationalCampaign, campaign_event, utc_now_iso
from estate.core.paths import ESTATE_ROOT
from estate.core.provider_routing_recommendations import ProviderRoutingRecommendationRequest, evaluate_provider_routing_recommendation
from estate.core.traffic_controller import RecommendedAction

CAMPAIGN_DIR = Path("runtime/operational_campaigns")
STATE_FILE = CAMPAIGN_DIR / "campaigns.json"
EVENTS_FILE = CAMPAIGN_DIR / "events.jsonl"
STATUS_FILE = CAMPAIGN_DIR / "status.json"


def _root(root: str | Path | None = None) -> Path:
    return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists(): return default
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


class OperationalCampaignRuntime:
    def __init__(self, root: str | Path | None = None) -> None:
        self.root = _root(root)

    @property
    def state_path(self) -> Path: return self.root / STATE_FILE
    @property
    def events_path(self) -> Path: return self.root / EVENTS_FILE
    @property
    def status_path(self) -> Path: return self.root / STATUS_FILE

    def load_campaigns(self) -> dict[str, OperationalCampaign]:
        payload = _read_json(self.state_path, {"campaigns": []})
        return {c.campaign_id: c for c in [OperationalCampaign.from_dict(x) for x in payload.get("campaigns", [])]}

    def save_campaigns(self, campaigns: dict[str, OperationalCampaign]) -> None:
        _write_json(self.state_path, {"version": 1, "updated_at": utc_now_iso(), "campaigns": [c.to_dict() for c in campaigns.values()]})
        self.write_status(campaigns)

    def register(self, campaign: OperationalCampaign) -> OperationalCampaign:
        campaign.validate()
        campaigns = self.load_campaigns(); campaigns[campaign.campaign_id] = campaign; self.save_campaigns(campaigns)
        return campaign

    def _record(self, campaign: OperationalCampaign, event_type: str, summary: str, **metadata: Any) -> dict[str, Any]:
        event = campaign_event(campaign, event_type, summary, **metadata)
        self.events_path.parent.mkdir(parents=True, exist_ok=True)
        with self.events_path.open("a", encoding="utf-8") as handle: handle.write(json.dumps(event, sort_keys=True) + "\n")
        return event

    def _get(self, campaign_id: str) -> tuple[dict[str, OperationalCampaign], OperationalCampaign]:
        campaigns = self.load_campaigns()
        if campaign_id not in campaigns: raise KeyError(f"unknown campaign {campaign_id}")
        return campaigns, campaigns[campaign_id]

    def _authorize(self, campaign: OperationalCampaign, action: str, director: str, phase_id: str | None = None) -> None:
        if director not in campaign.authority.allowed_directors: raise PermissionError("director is outside pre-approved campaign authority")
        if action not in campaign.authority.allowed_actions: raise PermissionError(f"action {action} is outside pre-approved campaign authority")
        if phase_id and campaign.authority.allowed_phase_ids and phase_id not in campaign.authority.allowed_phase_ids: raise PermissionError(f"phase {phase_id} is outside delegated campaign authority")

    def start(self, campaign_id: str, *, director: str = "Operations Manager") -> OperationalCampaign:
        campaigns, campaign = self._get(campaign_id); self._authorize(campaign, "start", director)
        if campaign.state not in {"Ready", "Paused"}: raise ValueError("campaign is not startable")
        campaign.state = "Running"; campaign.updated_at = utc_now_iso(); self._record(campaign, "campaign_started", "Campaign started under delegated authority."); self.save_campaigns(campaigns); return campaign

    def pause(self, campaign_id: str, reason: str, *, director: str = "Operations Manager") -> OperationalCampaign:
        campaigns, campaign = self._get(campaign_id); self._authorize(campaign, "pause", director)
        campaign.state = "Paused"; campaign.holds.append(reason); campaign.updated_at = utc_now_iso(); self._record(campaign, "campaign_paused", reason); self.save_campaigns(campaigns); return campaign

    def resume(self, campaign_id: str, *, director: str = "Operations Manager") -> OperationalCampaign:
        campaigns, campaign = self._get(campaign_id); self._authorize(campaign, "resume", director)
        campaign.state = "Running"; campaign.holds.clear(); campaign.updated_at = utc_now_iso(); self._record(campaign, "campaign_resumed", "Campaign resumed."); self.save_campaigns(campaigns); return campaign

    def block(self, campaign_id: str, reason: str, *, director: str = "Operations Manager") -> OperationalCampaign:
        campaigns, campaign = self._get(campaign_id); self._authorize(campaign, "block", director)
        campaign.state = "Blocked"; campaign.blockers.append(reason); campaign.updated_at = utc_now_iso(); self._record(campaign, "campaign_blocked", reason); self.save_campaigns(campaigns); return campaign

    def cancel(self, campaign_id: str, reason: str, *, director: str = "Operations Manager") -> OperationalCampaign:
        campaigns, campaign = self._get(campaign_id); self._authorize(campaign, "cancel", director)
        campaign.state = "Cancelled"; campaign.updated_at = utc_now_iso(); self._record(campaign, "campaign_cancelled", reason); self.save_campaigns(campaigns); return campaign

    def complete(self, campaign_id: str, *, director: str = "Operations Manager") -> OperationalCampaign:
        campaigns, campaign = self._get(campaign_id); self._authorize(campaign, "complete", director)
        if any(p.state != "Completed" for p in campaign.phases): raise ValueError("all phases must complete before campaign completion")
        campaign.state = "Completed"; campaign.completed_at = utc_now_iso(); campaign.institutional_acceptance = False; campaign.updated_at = campaign.completed_at
        self._record(campaign, "campaign_completed", "Campaign completed; institutional acceptance is still separate."); self.save_campaigns(campaigns); return campaign

    def complete_phase(self, campaign_id: str, phase_id: str, evidence: list[str], *, director: str = "Operations Manager") -> OperationalCampaign:
        campaigns, campaign = self._get(campaign_id); self._authorize(campaign, "advance", director, phase_id)
        phase = campaign.phase(phase_id); phase.evidence.extend(evidence)
        missing = [req for req in phase.evidence_requirements if not any(req in ev for ev in phase.evidence)]
        if missing: raise ValueError(f"missing evidence requirements: {missing}")
        phase.state = "Completed"; campaign.updated_at = utc_now_iso(); self._record(campaign, "phase_completed", f"Phase {phase_id} completed.", evidence=evidence); self.save_campaigns(campaigns); return campaign

    def next_eligible_actions(self, campaign_id: str) -> dict[str, Any]:
        _, campaign = self._get(campaign_id)
        completed = {p.phase_id for p in campaign.phases if p.state == "Completed"}
        actions = []
        blockers = list(campaign.blockers) + list(campaign.holds)
        if campaign.state != "Running":
            return {"campaign_id": campaign_id, "state": campaign.state, "tempo": campaign.tempo, "next_actions": [], "blockers": blockers or [f"campaign is {campaign.state}"], "exceptions": []}
        for phase in campaign.phases:
            if phase.state in {"Pending", "Ready"}:
                unmet = [dep for dep in phase.dependencies if dep not in completed]
                if unmet or phase.blockers:
                    blockers.extend([f"{phase.phase_id} waiting on {dep}" for dep in unmet] + phase.blockers)
                    continue
                actions.append({"action": "advance", "phase_id": phase.phase_id, "title": phase.title, "routine": phase.routine})
        return {"campaign_id": campaign_id, "state": campaign.state, "tempo": campaign.tempo, "next_actions": actions, "blockers": blockers, "exceptions": []}

    def advance(self, campaign_id: str, *, director: str = "Operations Manager", dry_run: bool = False) -> dict[str, Any]:
        campaigns, campaign = self._get(campaign_id); self._authorize(campaign, "advance", director)
        surfaced = self.next_eligible_actions(campaign_id)
        advanced = []
        for action in surfaced["next_actions"][: campaign.authority.max_routine_advances_per_cycle]:
            phase = campaign.phase(action["phase_id"]); self._authorize(campaign, "advance", director, phase.phase_id)
            if not phase.routine or phase.escalation_conditions:
                rec = RecommendedAction.create(action_type="escalate", target_type="work_package", target_id=phase.work_package_id, priority="high", reason="Phase requires governance review or non-routine authority.", safe_summary=f"Campaign phase {phase.phase_id} escalated.")
                self._record(campaign, "campaign_escalated", rec.safe_summary, recommended_action=rec.to_dict()); surfaced["exceptions"].append(rec.to_dict()); continue
            recommendation = evaluate_provider_routing_recommendation(ProviderRoutingRecommendationRequest(routing_request_id=f"{campaign.campaign_id}:{phase.phase_id}", work_package_id=phase.work_package_id or "", mission_summary=phase.title, work_type="implementation", requires_repo_write=bool(phase.work_package_id), expected_artifacts=phase.evidence_requirements, validation_required=bool(phase.validation_commands)))
            provider = phase.provider or recommendation.recommended_provider
            dispatch_id = f"{campaign.campaign_id}-{phase.phase_id}"
            if not dry_run:
                item = enqueue_dispatch_request(DispatchRequest(dispatch_id=dispatch_id, work_package_id=phase.work_package_id, title=phase.title, requested_by=director, provider=provider, classification="Estate Internal", priority="High", state="Queued", allowed_providers=[provider], validation_commands=phase.validation_commands, provider_metadata={"campaign_id": campaign.campaign_id, "phase_id": phase.phase_id, "provider_recommendation": recommendation.to_dict()}), self.root)
                phase.dispatch_id = item.dispatch_id; phase.state = "Running"; self._record(campaign, "phase_dispatched", f"Phase {phase.phase_id} dispatched through execution dispatch.", dispatch_id=item.dispatch_id, provider=provider)
            advanced.append({"phase_id": phase.phase_id, "dispatch_id": dispatch_id, "provider": provider, "validation_commands": phase.validation_commands})
        campaign.updated_at = utc_now_iso(); self._record(campaign, "campaign_advanced", "Campaign advancement cycle evaluated.", advanced=advanced); self.save_campaigns(campaigns)
        return {**surfaced, "advanced": advanced}

    def write_status(self, campaigns: dict[str, OperationalCampaign] | None = None) -> dict[str, Any]:
        campaigns = campaigns or self.load_campaigns()
        payload = {"updated_at": utc_now_iso(), "campaigns": [{"campaign_id": c.campaign_id, "title": c.title, "state": c.state, "tempo": c.tempo, "next_actions": self.next_eligible_actions(c.campaign_id)["next_actions"] if c.campaign_id in campaigns else [], "blockers": c.blockers + c.holds, "exceptions": [p.phase_id for p in c.phases if p.blockers or p.escalation_conditions]} for c in campaigns.values()]}
        _write_json(self.status_path, payload); return payload
