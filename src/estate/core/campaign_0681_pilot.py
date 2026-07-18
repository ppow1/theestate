"""Bounded real-work pilot harness using existing Estate operational seams."""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

from estate.core.alfred_runtime import route_operational_message
from estate.core.autonomous_operations_audit import append_operational_audit_event
from estate.core.continuous_momentum_engine import run_momentum_cycle
from estate.core.execution_dispatch import DispatchRequest, enqueue_dispatch_request
from estate.core.grace_operations_runtime import build_operational_coordination_view, create_coordination_request
from estate.core.helen_workforce import HelenWorkforceStore
from estate.core.readiness_evidence_projection import project_readiness_evidence
from estate.core.runtime_recovery import RuntimePersistenceStore
from estate.core.runtime_replay import RuntimeReplayEngine
from estate.core.steward_dashboard import build_operational_visibility

PILOT_ID = "CAMPAIGN-0681-WP0706-EVIDENCE-INTEGRITY"


def run_pilot(source_root: Path, sandbox_root: Path, *, occurred_at: str) -> dict[str, Any]:
    """Execute the authorized pilot in a disposable root and return its evidence."""
    sandbox_root.mkdir(parents=True, exist_ok=True)
    registry = sandbox_root / "data" / "registry"
    registry.mkdir(parents=True, exist_ok=True)
    for name in ("personnel.json", "mailboxes.json"):
        shutil.copy2(source_root / "data" / "registry" / name, registry / name)

    starting_evidence = "collaboration/evidence/CAMPAIGN_0681_WP0706_PILOT_AUTHORIZATION.md"
    readiness = project_readiness_evidence([{
        "subject_id": PILOT_ID, "evidence_id": "pilot-launch-validation",
        "state": "ready", "source_kind": "validation_result",
        "reference": starting_evidence, "issued_at": occurred_at,
    }], observed_at=occurred_at)

    momentum = {
        "campaign_id": "CAMPAIGN-0681", "observation_timestamp": occurred_at,
        "campaign_momentum_state": "active", "observation_only": True, "warnings": [],
        "packages": [{
            "package_id": "WP-0706-PILOT", "observed_state": "eligible",
            "evidence_references": [starting_evidence], "warnings": [],
            "dependency_satisfaction": {"satisfied": ["WP-0705"], "unmet": []},
            "explanation": "Perform the bounded evidence-integrity handoff.",
            "recommended_follow_up_destination": "Alfred",
        }],
    }
    grace_view = build_operational_coordination_view(momentum)
    grace_message = create_coordination_request(
        grace_view, "WP-0706-PILOT", destination="Alfred",
        destination_id=7, mailbox_id=7, created_at=occurred_at,
        message_id="msg_campaign0681_wp0706_pilot",
    )
    routed = route_operational_message(grace_message, root=sandbox_root, now=occurred_at)

    blocker = {
        "blocker_class": "staffing_or_capability_blocker", "protected_decision": False,
        "canonical_evidence_references": [starting_evidence],
    }
    workforce = HelenWorkforceStore(sandbox_root)
    workforce_request, workforce_path = workforce.create_operational_request(
        blocker, campaign_id="CAMPAIGN-0681", package_id="WP-0706-PILOT",
        need_kind="capability", required_role="Evidence reviewer",
        required_capabilities=["campaign evidence integrity review"], urgency="normal",
        duration="bounded pilot", constraints=["no staffing action"],
    )
    workforce_disposition, disposition_path = workforce.record_operational_disposition(
        workforce_request.request_id, disposition="deferred", decided_by="Helen",
        evidence_references=[starting_evidence],
        reason="Pilot proves the request lane only; no staffing is authorized or performed.",
    )

    dispatch = enqueue_dispatch_request(DispatchRequest(
        dispatch_id="dispatch-campaign0681-wp0706-pilot",
        work_package_id="WP-0706-PILOT",
        title="Validate the bounded pilot evidence inventory",
        requested_by="Grace", provider="codex-cli-openai",
        classification="Estate Internal", priority="Normal", state="Queued",
        sandbox="read-only", allowed_read_paths=["collaboration/evidence"],
        allowed_write_paths=[], allowed_providers=["codex-cli-openai"],
        validation_commands=["validate CAMPAIGN-0681 WP-0706 pilot evidence"],
        provider_metadata={"pilot_id": PILOT_ID, "live_provider_execution": False},
    ), sandbox_root)

    store = RuntimePersistenceStore(sandbox_root)
    store.persist_checkpoint(
        cycle_id="wp0706-pilot", cycle_state="running",
        campaign_state={"pilot_id": PILOT_ID, "phase": "interrupted"},
        completed_side_effects=[grace_message["id"]], last_durable_event_position=0,
        metadata={"controlled_interruption": True, "rollback": "discard sandbox root"},
    )
    store.append_event("campaign_state_updated", {
        "campaign_state": {"pilot_id": PILOT_ID, "phase": "duplicate-message-attempt"},
        "side_effect_id": grace_message["id"],
    })
    store.append_event("campaign_state_updated", {
        "campaign_state": {"pilot_id": PILOT_ID, "phase": "recovered-for-review"},
        "side_effect_id": "pilot-recovery-state",
    })
    recovery = RuntimeReplayEngine(sandbox_root).replay_from_checkpoint("wp0706-pilot")

    adapter_calls: list[dict[str, Any]] = []
    protected_cycle = run_momentum_cycle(
        cycle_id="wp0706-protected-stop", observed_at=occurred_at,
        inputs={"decision": {"state": "protected", "protected_decision": True,
                              "authorizes_action": False,
                              "evidence_references": [starting_evidence], "warnings": []}},
        candidates=[{
            "action_id": "accept-pilot", "permission": "protected", "priority": 100,
            "idempotency_key": "wp0706-accept-pilot", "source_refs": [starting_evidence],
            "canonical_mechanism": "existing_acceptance_lane", "authority_refs": [],
        }], mode="live", action_adapter=lambda action: adapter_calls.append(action) or {"evidence_reference": "invalid"},
    )

    visibility = build_operational_visibility([{
        "signal_id": "wp0706-protected-review", "domain": "pilot",
        "title": "WP-0706 pilot requires protected review",
        "summary": "Pilot evidence is complete; acceptance remains protected.",
        "state": "protected", "protected_decision": True,
        "requested_authority": "Chief Architect and Steward",
        "decision_question": "Release G7 after reviewing pilot and failure evidence?",
        "freshness": "current", "confidence": "high", "observed_at": occurred_at,
        "owner": "Chief Architect and Steward", "classification": "Estate Internal",
        "evidence_references": [starting_evidence], "warnings": [], "controls": [],
    }], viewer={"role": "steward", "identity_evidence": ["data/registry/personnel.json"],
               "allowed_classifications": ["Estate Internal"]}, generated_at=occurred_at)

    audit = append_operational_audit_event({
        "event_id": "campaign0681-wp0706-pilot-protected-stop",
        "event_kind": "escalation", "occurred_at": occurred_at,
        "correlations": {"campaign_id": "CAMPAIGN-0681", "work_package_id": "WP-0706", "cycle_id": "wp0706-protected-stop"},
        "source_evidence": [starting_evidence], "freshness": "current", "confidence": "high",
        "policy_disposition": "escalate",
        "authority": {"required": True, "references": ["collaboration/work_packages/planning/CAMPAIGN_0681_manifest.json"]},
        "outcome": "protected decision held for Chief Architect and Steward",
        "uncertainty": [],
    }, root=sandbox_root)

    return {
        "schema_version": "estate.campaign-0681-bounded-pilot-result.v1",
        "pilot_id": PILOT_ID, "occurred_at": occurred_at,
        "owner": "Grace / Office of Operations",
        "scope": "Validate the CAMPAIGN-0681 pilot evidence inventory through existing operational lanes.",
        "risk": "low; repository-evidence-only sandbox with no live provider call",
        "rollback": "Discard the isolated pilot root; committed result evidence is append-only.",
        "starting_state": {"authorization_reference": starting_evidence, "readiness": readiness},
        "grace": {"view": grace_view, "coordination_message_id": grace_message["id"]},
        "alfred": routed,
        "helen": {"request_id": workforce_request.request_id, "request_path": workforce_path.relative_to(sandbox_root).as_posix(), "disposition": workforce_disposition, "disposition_path": disposition_path.relative_to(sandbox_root).as_posix()},
        "engineering": {"dispatch_id": dispatch.dispatch_id, "state": dispatch.state, "provider": dispatch.provider, "live_provider_execution": False},
        "interruption_recovery": recovery,
        "protected_escalation": {"cycle": protected_cycle, "adapter_calls": len(adapter_calls)},
        "steward_visibility": visibility,
        "audit_event": audit,
        "outcome": "pilot workflow completed mechanically; G7 protected review remains pending",
        "protected_actions": {"merge": False, "deployment": False, "acceptance": False, "spending": False, "staffing": False, "disclosure": False, "campaign_closeout": False},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--sandbox-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--occurred-at", required=True)
    args = parser.parse_args()
    result = run_pilot(args.source_root, args.sandbox_root, occurred_at=args.occurred_at)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"pilot_id": result["pilot_id"], "outcome": result["outcome"], "output": str(args.output)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
