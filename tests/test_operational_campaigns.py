import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from estate.core.operational_campaigns import CampaignAuthority, CampaignPhase, OperationalCampaign, campaign_event


def test_campaign_model_requires_unique_phases_and_known_dependencies():
    campaign = OperationalCampaign.create(
        campaign_id="camp-001",
        title="Ops campaign",
        goals=["Finish governed initiative"],
        authority=CampaignAuthority(approved_by="Steward", approved_at="2026-07-10T00:00:00Z", allowed_phase_ids=["plan", "build"]),
        phases=[
            CampaignPhase("plan", "Plan", ["Create plan"], evidence_requirements=["plan.md"]),
            CampaignPhase("build", "Build", ["Implement"], dependencies=["plan"], delegated_authority=["Operations Manager"]),
        ],
    )

    payload = campaign.to_dict()
    restored = OperationalCampaign.from_dict(payload)

    assert restored.campaign_id == "camp-001"
    assert restored.phase("build").dependencies == ["plan"]


def test_campaign_model_rejects_bad_dependency():
    campaign = OperationalCampaign.create(
        title="Bad campaign",
        goals=["x"],
        authority=CampaignAuthority(approved_by="Steward", approved_at="2026-07-10T00:00:00Z"),
        phases=[CampaignPhase("phase-1", "Phase", ["x"], dependencies=["missing"])],
    )

    with pytest.raises(ValueError, match="unknown dependencies"):
        campaign.to_dict()


def test_campaign_event_is_governed_and_typed():
    campaign = OperationalCampaign.create(
        campaign_id="camp-002",
        title="Event campaign",
        goals=["x"],
        authority=CampaignAuthority(approved_by="Steward", approved_at="2026-07-10T00:00:00Z"),
        phases=[CampaignPhase("phase-1", "Phase", ["x"])],
    )

    event = campaign_event(campaign, "campaign_started", "Started.")

    assert event["campaign_id"] == "camp-002"
    assert event["event_type"] == "campaign_started"
    with pytest.raises(ValueError, match="unsupported"):
        campaign_event(campaign, "improvise", "Nope.")
