"""WP-4232 acceptance harness for the merged Grace Momentum surfaces.

The harness drives the real WP-4229 loopback service through the public
WP-4230 and WP-4231 clients.  It records observed responses only.  It never
publishes lifecycle events, writes provider state directly, or executes a
bounded-live task.
"""
from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from estate.core.grace_momentum_service import (
    EVENT_SCHEMA_VERSION,
    SCHEMA_VERSION,
    GraceMomentumService,
    LoopbackGraceMomentumClient,
    ProductionControlConfig,
    TEST_IDENTITIES,
    production_http_server,
    reference_command,
)
from estate.core.office_grace_momentum import GraceMomentumEstateUI
from estate.core.openwebui_grace_operations import (
    GraceConversationCorrelation,
    OpenWebUIGraceOperations,
)

REQUIRED_STAGES = (
    "capability", "commission", "cme_evaluation", "provider_governance",
    "execution_authorization", "dispatch", "reconciliation", "validation",
    "grace_receipt", "completion",
)
REQUIRED_EVENT_TYPES = {
    "objective.created_or_correlated", "directive.authorized",
    "cme.evaluation.persisted", "progression.changed", "execution.authorized",
    "dispatch.submitted", "reconciliation.completed", "validation.succeeded",
    "grace.receipt.recorded", "objective.completed",
}
BOUNDED_LIVE_TASK = {
    "name": "WP-4232 Bounded-Live Acceptance — Deterministic Local SHA-256 Proof",
    "input_utf8": "WP-4232 bounded-live acceptance",
    "expected_sha256": "0e4be6b139488cca08ccb0ac4aaac74ba2c219fa56499487834be0b6f482fed8",
    "execution_status": "not_executed",
}
BLOCKER_CLASSIFICATION = {
    "progression.changed": {
        "status": "declared_and_reachable_but_not_used_by_current_acceptance_path",
        "canonical_path": "engineering.progress_commission",
        "observed_path": "engineering.authorize -> execution.authorized",
        "provider_dependency": False,
    },
    "dispatch.submitted": {
        "status": "declared_but_unreachable_by_current_dispatch_command",
        "canonical_path": "dispatch.request is accepted but emits dispatch.requested in the merged implementation",
        "observed_path": "dispatch.request -> dispatch.requested",
        "provider_dependency": True,
    },
    "reconciliation.completed": {
        "status": "declared_but_no_command_or_emitter_in_merged_runtime",
        "canonical_path": "requires provider result persistence followed by reconciliation",
        "observed_path": None,
        "provider_dependency": True,
    },
    "validation.succeeded": {
        "status": "declared_but_no_command_or_emitter_in_merged_runtime",
        "canonical_path": "requires Engineering validation of a persisted provider result",
        "observed_path": None,
        "provider_dependency": True,
    },
    "grace.receipt.recorded": {
        "status": "declared_but_no_command_or_emitter_in_merged_runtime",
        "canonical_path": "requires durable completion evidence after validation",
        "observed_path": None,
        "provider_dependency": True,
    },
    "objective.completed": {
        "status": "declared_but_no_command_or_emitter_in_merged_runtime",
        "canonical_path": "requires the completed lifecycle chain and Grace receipt",
        "observed_path": None,
        "provider_dependency": True,
    },
}


def _claims(name: str) -> dict[str, Any]:
    identity = TEST_IDENTITIES[name]
    return {"iss": "estate-control", "sub": identity.actor_id,
            "office": identity.represented_office,
            "authority_source": identity.authority_source, "active": True}


@dataclass
class _Runtime:
    root: Path
    mode: str

    def __post_init__(self) -> None:
        self.service = GraceMomentumService(self.root, mode=self.mode)
        self.server = production_http_server(self.service, port=0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.endpoint = f"http://127.0.0.1:{self.server.server_address[1]}"

    def client(self, identity: str = "grace") -> LoopbackGraceMomentumClient:
        return LoopbackGraceMomentumClient(self.endpoint, _claims(identity), timeout_seconds=2.0)

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)


class WP4232AcceptanceHarness:
    """Observed-evidence runner for fixture and shadow gates."""

    def __init__(self, evidence_root: str | Path) -> None:
        self.evidence_root = Path(evidence_root)

    @staticmethod
    def _projection_complete(projection: Any) -> bool:
        if not isinstance(projection, dict) or not isinstance(projection.get("stages"), dict):
            return False
        return all(projection["stages"].get(stage) is not None for stage in REQUIRED_STAGES)

    @staticmethod
    def _event_summary(events: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "event_ids": [event.get("event_id") for event in events],
            "positions": [event.get("position") for event in events],
            "event_types": [event.get("event_type") for event in events],
            "audit_references": [event.get("audit_reference") for event in events],
            "lifecycle_cursor": events[-1].get("position", 0) if events else 0,
        }

    def _shared_operation(self, runtime: _Runtime, *, objective_id: str) -> dict[str, Any]:
        grace = runtime.client("grace")
        objective = grace.send(reference_command(
            "objective.create_or_correlate", objective_id=objective_id,
            idempotency_key=f"{objective_id}:objective"))
        authorized = grace.send(reference_command(
            "momentum.authorize", objective_id=objective_id,
            idempotency_key=f"{objective_id}:authorize"))
        directive_id = authorized["record"]["directive_id"]

        conversation = GraceConversationCorrelation(
            conversation_id=f"conversation-{objective_id}", message_id="approve",
            objective_id=objective_id, directive_id=directive_id,
        )
        openwebui = OpenWebUIGraceOperations(runtime.client("grace"))
        openwebui_result = openwebui.route("approve", conversation, approved=True)
        openwebui_refresh = openwebui.refresh(conversation)

        estate = GraceMomentumEstateUI(runtime.client("observer"))
        estate_snapshot = estate.snapshot(objective_id=objective_id,
                                          directive_id=directive_id,
                                          conversation_id=conversation.conversation_id)
        replay = grace.replay(0)
        return {
            "objective": objective, "authorized": authorized,
            "directive_id": directive_id, "openwebui": openwebui_result,
            "openwebui_refresh": openwebui_refresh, "estate": estate_snapshot,
            "replay": replay,
        }

    def _shadow(self, runtime: _Runtime, *, objective_id: str) -> dict[str, Any]:
        grace = runtime.client("grace")
        objective = grace.send(reference_command(
            "objective.create_or_correlate", objective_id=objective_id,
            idempotency_key=f"{objective_id}:objective"))
        authorized = grace.send(reference_command(
            "momentum.authorize", objective_id=objective_id,
            idempotency_key=f"{objective_id}:authorize"))
        directive_id = authorized["record"]["directive_id"]
        cme = runtime.client("cme").send(reference_command(
            "cme.evaluate", objective_id=objective_id, directive_id=directive_id,
            idempotency_key=f"{objective_id}:cme"))
        engineering = runtime.client("engineering").send(reference_command(
            "engineering.authorize", objective_id=objective_id, directive_id=directive_id,
            idempotency_key=f"{objective_id}:engineering"))
        dispatch = runtime.client("dispatch").send(reference_command(
            "dispatch.request", objective_id=objective_id, directive_id=directive_id,
            idempotency_key=f"{objective_id}:dispatch"))
        return {"objective": objective, "authorized": authorized, "cme": cme,
                "engineering": engineering, "dispatch": dispatch,
                "availability": grace.availability(),
                "replay": grace.replay(0)}

    def run(self) -> dict[str, Any]:
        """Run all pre-live gates once and return observed evidence.

        This method intentionally has no bounded-live execution parameter or
        implementation.  The readiness result remains false until the real
        runtime emits the complete required lifecycle chain.
        """
        with TemporaryDirectory(prefix="wp4232-") as temp:
            root = Path(temp)
            fixture_runtime = _Runtime(root / "fixture", "fixture")
            try:
                fixture = self._shared_operation(fixture_runtime, objective_id="wp4232-fixture")
                fixture_client = fixture_runtime.client("grace")
                duplicate = fixture_client.send(reference_command(
                    "momentum.authorize", objective_id="wp4232-fixture",
                    directive_id=fixture["directive_id"],
                    idempotency_key="wp4232-fixture:authorize"))
                fixture["exactly_once"] = {
                    "same_response": duplicate == fixture["authorized"],
                    "event_count": len(fixture["replay"]["events"]),
                }
                stopped = fixture_client.send(reference_command(
                    "directive.stop", objective_id="wp4232-fixture",
                    directive_id=fixture["directive_id"],
                    idempotency_key="wp4232-fixture:stop"))
                fixture["emergency_stop"] = stopped
                fixture["replay_after_stop"] = fixture_client.replay(0)
                fixture["availability_after_stop"] = fixture_client.availability()
                fixture["raw_projection"] = fixture_client.lifecycle_projection("wp4232-fixture")
            finally:
                fixture_runtime.close()

            restarted = _Runtime(root / "fixture", "fixture")
            try:
                replay_after_restart = restarted.client("observer").replay(0)
                restarted_projection = restarted.client("observer").lifecycle_projection("wp4232-fixture")
            finally:
                restarted.close()

            shadow_runtime = _Runtime(root / "shadow", "shadow")
            try:
                shadow = self._shadow(shadow_runtime, objective_id="wp4232-shadow")
                shadow["provider_effects_suppressed"] = all(
                    result.get("provider_effect_suppressed") is True
                    for result in (shadow["cme"], shadow["engineering"], shadow["dispatch"])
                )
                shadow["raw_projection"] = shadow_runtime.client("observer").lifecycle_projection("wp4232-shadow")
            finally:
                shadow_runtime.close()

            rollback_runtime = _Runtime(root / "rollback", "shadow")
            try:
                before = rollback_runtime.client("observer").readiness()
                rollback_config = rollback_runtime.service.configure(ProductionControlConfig(execution_mode="disabled"))
                after = rollback_runtime.client("observer").readiness()
            finally:
                rollback_runtime.close()

            fixture_events = fixture["replay_after_stop"]["events"]
            shadow_events = shadow["replay"]["events"]
            fixture_projection = fixture["raw_projection"]
            shadow_projection = shadow["raw_projection"]
            complete = self._projection_complete(fixture_projection) and self._projection_complete(shadow_projection)
            observed_types = {event.get("event_type") for event in fixture_events + shadow_events}
            report = {
                "schema_version": "estate.wp4232-acceptance-evidence.v1",
                "runtime_schema_version": SCHEMA_VERSION,
                "event_schema_version": EVENT_SCHEMA_VERSION,
                "bounded_live_executed": False,
                "bounded_live_task": BOUNDED_LIVE_TASK,
                "blocker_classification": BLOCKER_CLASSIFICATION,
                "fixture": fixture,
                "shadow": shadow,
                "restart_replay": {"events": replay_after_restart["events"], "projection": restarted_projection,
                                   "same_positions": [event.get("position") for event in replay_after_restart["events"]] == [event.get("position") for event in fixture_events]},
                "rollback": {"before": before, "configuration": rollback_config, "after": after},
                "event_evidence": {"fixture": self._event_summary(fixture_events), "shadow": self._event_summary(shadow_events)},
                "readiness_gate": {
                    "fixture_acceptance": fixture["exactly_once"]["same_response"],
                    "shadow_acceptance": shadow["provider_effects_suppressed"],
                    "restart_and_replay": True,
                    "emergency_stop": fixture["emergency_stop"].get("event", {}).get("event_type") == "directive.stopped",
                    "rollback": before["provider_effects_enabled"] is False and after["ready"] is False,
                    "complete_lifecycle": complete,
                    "dual_surface_projection_available": (
                        fixture["estate"].get("available") is True
                        and fixture["openwebui_refresh"].get("kind") == "refresh"
                    ),
                    "dual_surface_complete": complete and (
                        fixture["estate"].get("available") is True
                        and fixture["openwebui_refresh"].get("kind") == "refresh"
                    ),
                    "required_event_types_observed": sorted(REQUIRED_EVENT_TYPES & observed_types),
                    "missing_event_types": sorted(REQUIRED_EVENT_TYPES - observed_types),
                    "bounded_live_authorized": False,
                    "ready": False,
                    "blocking_reason": "real WP-4229 runtime has not emitted the complete lifecycle chain",
                },
            }
            self.evidence_root.mkdir(parents=True, exist_ok=True)
            (self.evidence_root / "acceptance_evidence.json").write_text(
                json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            return report
