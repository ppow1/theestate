import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from estate.core.provider_routing_office_panel import (
    ADVISORY_MESSAGE,
    build_office_panel_payload,
    load_latest_office_panel_payload,
)


def recommendation_payload(**overrides):
    payload = {
        "recommendation_id": "prr-office-1",
        "recommended_provider": "codex_cloud_web",
        "alternate_providers": ["deterministic_local_tooling", "human_review"],
        "provider_rationale": "Codex Cloud/Web fits bounded repository implementation without local runtime.",
        "capacity_note": "Prefer Cloud/Web; no Codex CLI capacity burn and no live provider call occurred.",
        "local_runtime_required": False,
        "human_review_required": False,
        "boundary_review_required": False,
        "validation_rings_required": ["ring_0_static_structural", "ring_1_deterministic_tests"],
        "not_recommended": {"codex_cli": "Avoid premium CLI capacity unless local runtime is required."},
        "source_artifact": "collaboration/work_packages/pending/WP-0615_Office_Provider_Routing_Recommendations_Panel.md",
        "work_package_id": "WP-0615",
        "classification": "Estate Internal",
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "metadata": {"recommendation_only": True, "dispatch_mutated": False, "orchestrator_mutated": False},
    }
    payload.update(overrides)
    return payload


def write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_latest_recommendation_appears_in_office_panel_payload(tmp_path):
    latest = tmp_path / "runtime/provider_routing/status/latest.json"
    write_json(latest, recommendation_payload())

    panel = load_latest_office_panel_payload(latest)

    assert panel["available"] is True
    assert panel["latest_recommendation_id"] == "prr-office-1"
    assert panel["recommended_provider"] == "codex_cloud_web"
    assert panel["alternate_providers"] == ["deterministic_local_tooling", "human_review"]
    assert panel["advisory_only"] is True
    assert "not a movement decision" in panel["warnings"][0]


def test_missing_artifacts_produce_unavailable_panel_state(tmp_path):
    panel = load_latest_office_panel_payload(tmp_path / "missing.json")

    assert panel["available"] is False
    assert panel["advisory_only"] is True
    assert panel["errors"]
    assert "missing" in panel["safe_summary"]


def test_malformed_artifacts_produce_safe_error_state(tmp_path):
    latest = tmp_path / "latest.json"
    latest.write_text("{not-json", encoding="utf-8")

    panel = load_latest_office_panel_payload(latest)

    assert panel["available"] is False
    assert panel["advisory_only"] is True
    assert panel["errors"]
    assert panel["provider_rationale"] == ""


def test_empty_artifact_produces_unavailable_panel_state(tmp_path):
    latest = tmp_path / "latest.json"
    write_json(latest, {})

    panel = load_latest_office_panel_payload(latest)

    assert panel["available"] is False
    assert "empty" in panel["errors"][0]


def test_stale_artifacts_are_marked_stale():
    old = (datetime.now(timezone.utc) - timedelta(days=3)).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    panel = build_office_panel_payload(recommendation_payload(created_at=old))

    assert panel["stale"] is True
    assert any("stale" in warning for warning in panel["warnings"])


def test_classification_sensitive_fields_are_summarized_safely():
    secret = "Private resident detail: do not expose full rationale in Office-safe summary."

    panel = build_office_panel_payload(recommendation_payload(classification="Private", provider_rationale=secret))

    assert panel["classification"] == "Private"
    assert "rationale redacted" in panel["safe_summary"]
    assert secret not in panel["safe_summary"]
    assert panel["provider_rationale"] == secret


def test_capacity_local_runtime_human_and_boundary_fields_appear():
    panel = build_office_panel_payload(
        recommendation_payload(
            capacity_note="Use local runtime; avoid cloud-only handling.",
            local_runtime_required=True,
            human_review_required=True,
            boundary_review_required=True,
            validation_rings_required=["ring_2_local_gpu_reasoning_review", "ring_4_institutional_acceptance"],
        )
    )

    assert panel["capacity_note"] == "Use local runtime; avoid cloud-only handling."
    assert panel["local_runtime_required"] is True
    assert panel["human_review_required"] is True
    assert panel["boundary_review_required"] is True
    assert "ring_2_local_gpu_reasoning_review" in panel["validation_rings_required"]
    assert any("Local runtime" in warning for warning in panel["warnings"])


def test_no_scheduling_dispatch_assignment_provider_execution_or_live_calls_are_exposed():
    panel = build_office_panel_payload(recommendation_payload())
    serialized = json.dumps(panel).lower()

    assert panel["advisory_only"] is True
    assert ADVISORY_MESSAGE in panel["warnings"]
    assert "schedule" not in panel
    assert "dispatch" not in panel
    assert "assignment" not in panel
    assert "execute" not in panel
    assert "live_provider_called" not in serialized


def test_no_duplicate_routing_engine_is_introduced():
    panel = build_office_panel_payload(recommendation_payload())

    assert "routing_engine" not in panel
    assert panel["recommended_provider"] == "codex_cloud_web"
