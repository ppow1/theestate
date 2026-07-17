import json

import pytest

from estate.core.codex_campaign_execution import (
    CodexCampaignExecution,
    CodexCampaignManifest,
    CodexCampaignPackage,
)


def manifest():
    return CodexCampaignManifest(
        campaign_id="CAMPAIGN-TEST",
        campaign_source="collaboration/campaigns/test.md",
        branch="campaign/test",
        approved_by="Chief Architect",
        packages=[
            CodexCampaignPackage("WP-1", "pending/WP-1.md"),
            CodexCampaignPackage("WP-2", "pending/WP-2.md", ["WP-1"], "wave-2"),
            CodexCampaignPackage("WP-3", "pending/WP-3.md", ["WP-1"], "wave-2"),
            CodexCampaignPackage("WP-4", "pending/WP-4.md", ["WP-2", "WP-3"]),
        ],
        review_gates={"integration": ["WP-2", "WP-3"]},
        allow_parallel_groups=["wave-2"],
    )


def test_dependency_parallel_gate_and_bounded_commits(tmp_path):
    runtime = CodexCampaignExecution(tmp_path)
    runtime.register(manifest())
    with pytest.raises(ValueError, match="campaign branch"):
        runtime.start("CAMPAIGN-TEST", current_branch="main")
    runtime.start("CAMPAIGN-TEST", current_branch="campaign/test")
    assert runtime.next_launches("CAMPAIGN-TEST") == ["WP-1"]
    runtime.mark_running("CAMPAIGN-TEST", "WP-1")
    runtime.record_commit("CAMPAIGN-TEST", "WP-1", "abc123")
    assert runtime.next_launches("CAMPAIGN-TEST") == ["WP-2", "WP-3"]
    for package, commit in (("WP-2", "def456"), ("WP-3", "fed654")):
        runtime.mark_running("CAMPAIGN-TEST", package)
        runtime.record_commit("CAMPAIGN-TEST", package, commit)
    assert runtime.load("CAMPAIGN-TEST").status == "awaiting_review"
    assert runtime.next_launches("CAMPAIGN-TEST") == []
    runtime.approve_gate("CAMPAIGN-TEST", "integration", reviewer="Chief Architect")
    assert runtime.load("CAMPAIGN-TEST").status == "running"
    assert runtime.next_launches("CAMPAIGN-TEST") == ["WP-4"]


def test_final_package_gate_precedes_acceptance_and_requires_approval(tmp_path):
    value = manifest()
    value.review_gates = {"final-review": ["WP-4"]}
    runtime = CodexCampaignExecution(tmp_path)
    runtime.register(value)
    runtime.start("CAMPAIGN-TEST", current_branch="campaign/test")

    for package, commit in (
        ("WP-1", "abc123"),
        ("WP-2", "def456"),
        ("WP-3", "fed654"),
        ("WP-4", "ghi789"),
    ):
        runtime.mark_running("CAMPAIGN-TEST", package)
        runtime.record_commit("CAMPAIGN-TEST", package, commit)

    campaign = runtime.load("CAMPAIGN-TEST")
    assert campaign.status == "awaiting_review"
    assert campaign.active_gate == "final-review"
    assert runtime.next_launches("CAMPAIGN-TEST") == []

    campaign = runtime.approve_gate("CAMPAIGN-TEST", "final-review", reviewer="Chief Architect")
    assert campaign.status == "awaiting_acceptance"
    assert campaign.active_gate is None
    state = json.loads(runtime._path("CAMPAIGN-TEST").read_text())
    assert [event["event"] for event in state["history"]][-3:] == [
        "review_gate_reached",
        "review_gate_approved",
        "campaign_awaiting_acceptance",
    ]


def test_failure_is_durable_and_requires_explicit_reconciliation(tmp_path):
    runtime = CodexCampaignExecution(tmp_path)
    runtime.register(manifest())
    runtime.start("CAMPAIGN-TEST", current_branch="campaign/test")
    runtime.mark_running("CAMPAIGN-TEST", "WP-1")
    runtime.fail("CAMPAIGN-TEST", "WP-1", "tests failed")
    assert runtime.load("CAMPAIGN-TEST").status == "reconciliation_required"
    assert runtime.next_launches("CAMPAIGN-TEST") == []
    runtime.reconcile("CAMPAIGN-TEST", "WP-1", action="retry")
    assert runtime.next_launches("CAMPAIGN-TEST") == ["WP-1"]
    state = json.loads(runtime._path("CAMPAIGN-TEST").read_text())
    assert [event["event"] for event in state["history"]][-2:] == ["package_failed", "campaign_reconciled"]


def test_manifest_rejects_unapproved_parallelism():
    value = manifest()
    value.allow_parallel_groups = []
    with pytest.raises(ValueError, match="not approved"):
        value.validate()
