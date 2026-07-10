import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from estate.core.execution_dispatch import QUEUE_OUTPUT
from estate.core.operational_campaign_runtime import EVENTS_FILE, OperationalCampaignRuntime, STATUS_FILE
from estate.core.operational_campaigns import CampaignAuthority, CampaignPhase, OperationalCampaign


def sample_campaign():
    return OperationalCampaign.create(
        campaign_id="camp-runtime",
        title="Runtime campaign",
        goals=["Advance approved work"],
        authority=CampaignAuthority(
            approved_by="Steward",
            approved_at="2026-07-10T00:00:00Z",
            allowed_directors=["Operations Manager"],
            allowed_phase_ids=["routine", "review"],
            max_routine_advances_per_cycle=1,
        ),
        phases=[
            CampaignPhase("routine", "Routine provider work", ["Ship"], work_package_id="WP-1", evidence_requirements=["receipt"], validation_commands=["pytest -q tests/test_operational_campaign_runtime.py"]),
            CampaignPhase("review", "Governance review", ["Review"], dependencies=["routine"], routine=False, escalation_conditions=["acceptance decision"]),
        ],
    )


def test_runtime_advances_eligible_routine_phase_through_dispatch(tmp_path):
    runtime = OperationalCampaignRuntime(tmp_path)
    runtime.register(sample_campaign())
    runtime.start("camp-runtime")

    result = runtime.advance("camp-runtime")

    assert result["advanced"][0]["phase_id"] == "routine"
    queue = json.loads((tmp_path / QUEUE_OUTPUT).read_text(encoding="utf-8"))
    assert queue["items"][0]["dispatch_id"] == "camp-runtime-routine"
    assert queue["items"][0]["provider_metadata"]["campaign_id"] == "camp-runtime"
    assert (tmp_path / EVENTS_FILE).is_file()


def test_runtime_enforces_delegated_authority_and_escalates_non_routine(tmp_path):
    runtime = OperationalCampaignRuntime(tmp_path)
    runtime.register(sample_campaign())
    runtime.start("camp-runtime")

    with pytest.raises(PermissionError):
        runtime.advance("camp-runtime", director="Unapproved Director")

    runtime.advance("camp-runtime")
    runtime.complete_phase("camp-runtime", "routine", ["runtime/receipt.json"])
    result = runtime.advance("camp-runtime")

    assert result["exceptions"][0]["action_type"] == "escalate"
    assert result["advanced"] == []


def test_completion_is_not_institutional_acceptance_and_status_surfaces_blockers(tmp_path):
    runtime = OperationalCampaignRuntime(tmp_path)
    campaign = sample_campaign()
    campaign.phases[0].state = "Completed"
    campaign.phases[0].evidence = ["receipt"]
    campaign.phases[1].state = "Completed"
    runtime.register(campaign)
    completed = runtime.complete("camp-runtime")

    assert completed.state == "Completed"
    assert completed.institutional_acceptance is False
    status = json.loads((tmp_path / STATUS_FILE).read_text(encoding="utf-8"))
    assert status["campaigns"][0]["state"] == "Completed"
