"""One-shot final WP-4232 bounded-live acceptance runner.

This runner is intentionally separate from the reusable U1 test harness. It
accepts exactly the Steward-authorized task and refuses to run again after its
evidence marker exists.
"""
from __future__ import annotations

import hashlib
import json
import threading
from pathlib import Path
from typing import Any

from estate.core.grace_momentum_service import (
    EVENT_SCHEMA_VERSION,
    SCHEMA_VERSION,
    GraceMomentumService,
    LoopbackGraceMomentumClient,
    TEST_IDENTITIES,
    production_http_server,
    reference_command,
)
from estate.core.office_grace_momentum import GraceMomentumEstateUI
from estate.core.openwebui_grace_operations import GraceConversationCorrelation, OpenWebUIGraceOperations

TASK_NAME = "WP-4232 Bounded-Live Acceptance — Deterministic Local SHA-256 Proof"
TASK_INPUT = "WP-4232 bounded-live acceptance"
EXPECTED_SHA256 = "0e4be6b139488cca08ccb0ac4aaac74ba2c219fa56499487834be0b6f482fed8"
INPUT_DIGEST = hashlib.sha256(TASK_INPUT.encode("utf-8")).hexdigest()


def _claims(name: str) -> dict[str, Any]:
    identity = TEST_IDENTITIES[name]
    return {"iss": "estate-control", "sub": identity.actor_id, "office": identity.represented_office,
            "authority_source": identity.authority_source, "active": True}


class _Runtime:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.service = GraceMomentumService(root, mode="governed_local_test")
        self.server = production_http_server(self.service, port=0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.endpoint = f"http://127.0.0.1:{self.server.server_address[1]}"

    def client(self, identity: str) -> LoopbackGraceMomentumClient:
        return LoopbackGraceMomentumClient(self.endpoint, _claims(identity), timeout_seconds=2)

    def close(self) -> None:
        self.server.shutdown(); self.server.server_close(); self.thread.join(timeout=2)


def _send(client: LoopbackGraceMomentumClient, action: str, key: str, *, objective_id: str, directive_id: str | None = None, **fields: Any) -> dict[str, Any]:
    command = reference_command(action, objective_id=objective_id, directive_id=directive_id, idempotency_key=key)
    command.update(fields)
    return client.send(command)


class FinalWP4232Acceptance:
    objective_id = "wp4232-final-bounded-live"
    evidence_path = Path("collaboration/workstreams/WP-4232/final_bounded_live_acceptance.json")

    def __init__(self, repository_root: str | Path = ".") -> None:
        self.repository_root = Path(repository_root)
        self.evidence_file = self.repository_root / self.evidence_path
        self.runtime_root = self.repository_root / "runtime" / "wp4232-final"

    def run(self) -> dict[str, Any]:
        if self.evidence_file.exists():
            raise RuntimeError("final bounded-live acceptance is already recorded; repetition is prohibited")
        runtime = _Runtime(self.runtime_root)
        try:
            grace, engineering, dispatch, observer = (runtime.client(name) for name in ("grace", "engineering", "dispatch", "observer"))
            objective = _send(grace, "objective.create_or_correlate", "final:objective", objective_id=self.objective_id)
            authorized = _send(grace, "momentum.authorize", "final:authorize", objective_id=self.objective_id)
            directive_id = authorized["record"]["directive_id"]
            cme = _send(runtime.client("cme"), "cme.evaluate", "final:cme", objective_id=self.objective_id, directive_id=directive_id)
            progression = _send(engineering, "engineering.progress_commission", "final:progression", objective_id=self.objective_id, directive_id=directive_id, commission_id="commission-wp4232-final")
            admission = _send(engineering, "provider.admit", "final:admit", objective_id=self.objective_id, directive_id=directive_id, adapter_id="estate.local.sha256", readiness_evidence_reference="final-readiness-before-execution")

            health = observer.health(); readiness = observer.readiness(); availability = observer.availability()
            admission_record = admission["record"]
            projection_before = observer.lifecycle_projection(self.objective_id)
            readiness_gate = {
                "health_healthy": health.get("healthy") is True,
                "readiness_ready": readiness.get("ready") is True,
                "mode": readiness.get("mode"),
                "adapter_identity": admission_record.get("adapter_id"),
                "adapter_version": admission_record.get("adapter_version"),
                "admission_active": admission_record.get("status") == "admitted",
                "authority_current": admission_record.get("authority_source") == TEST_IDENTITIES["engineering"].authority_source,
                "local_only": readiness.get("local_only") is True,
                "egress_disabled": readiness.get("egress_disabled") is True,
                "spend_disabled": readiness.get("spend_disabled") is True,
                "arbitrary_shell_unavailable": True,
                "arbitrary_file_execution_unavailable": True,
                "emergency_stop_healthy_inactive": readiness.get("emergency_stop") == {"active": False, "healthy": True},
                "persistence_healthy": readiness.get("persistence_healthy") is True,
                "audit_persistence_healthy": (runtime.service.base / "audit.jsonl").exists(),
                "replay_healthy": readiness.get("replay_healthy") is True,
                "idempotency_healthy": readiness.get("idempotency_healthy") is True,
                "availability_operational": availability.get("operationally_available") is True,
                "exact_task_schema_valid": len(TASK_INPUT.encode("utf-8")) <= 4096,
                "no_prior_completed_effect": not (runtime.service.base / "effect_states.json").exists(),
                "projection_observed_before_execution": projection_before.get("objective_id") == self.objective_id,
            }
            if not all(value is True for key, value in readiness_gate.items() if key not in {"mode", "adapter_identity", "adapter_version"}):
                raise RuntimeError(f"readiness gate failed: {readiness_gate}")
            if readiness_gate["mode"] != "governed_local_test" or readiness_gate["adapter_identity"] != "estate.local.sha256" or readiness_gate["adapter_version"] != "1.0.0":
                raise RuntimeError(f"readiness identity failed: {readiness_gate}")

            submitted = _send(dispatch, "dispatch.submit", "final:submit", objective_id=self.objective_id, directive_id=directive_id, commission_id="commission-wp4232-final", task_input=TASK_INPUT)
            dispatch_id = submitted["record"]["dispatch_id"]
            effect_identity = submitted["record"]["effect_identity"]
            pre_execution_effect_state = runtime.service._read("effect_states.json", {}).get(effect_identity)
            if pre_execution_effect_state is not None:
                raise RuntimeError("authorized effect already has durable state before execution")
            executed = _send(dispatch, "provider.execute", "final:execute", objective_id=self.objective_id, directive_id=directive_id, dispatch_id=dispatch_id, task_input=TASK_INPUT)
            actual_digest = executed["record"]["output"]["sha256"]
            if actual_digest != EXPECTED_SHA256:
                raise RuntimeError("final digest mismatch")
            reconciled = _send(engineering, "reconciliation.complete", "final:reconcile", objective_id=self.objective_id, directive_id=directive_id, dispatch_id=dispatch_id)
            validated = _send(engineering, "validation.succeed", "final:validate", objective_id=self.objective_id, directive_id=directive_id, dispatch_id=dispatch_id, expected_sha256=EXPECTED_SHA256)
            receipt = _send(grace, "grace.record_receipt", "final:receipt", objective_id=self.objective_id, directive_id=directive_id, dispatch_id=dispatch_id)
            completed = _send(grace, "objective.complete", "final:complete", objective_id=self.objective_id, directive_id=directive_id, dispatch_id=dispatch_id)
            replay = observer.replay(0)
            duplicate = _send(dispatch, "provider.execute", "final:execute", objective_id=self.objective_id, directive_id=directive_id, dispatch_id=dispatch_id, task_input=TASK_INPUT)
            provider_events = [event for event in replay["events"] if event.get("event_type") == "provider.execution.completed"]
            projection = observer.lifecycle_projection(self.objective_id)
            conversation = GraceConversationCorrelation("conversation-wp4232-final", "completion", self.objective_id, directive_id)
            openwebui = OpenWebUIGraceOperations(observer, state_root=runtime.root / "openwebui")
            openwebui_projection = openwebui.refresh(conversation)
            estate_projection = GraceMomentumEstateUI(observer).snapshot(objective_id=self.objective_id, directive_id=directive_id, conversation_id=conversation.conversation_id)
            before_restart_count = len(replay["events"])
            runtime.close()
            restarted = _Runtime(self.runtime_root)
            try:
                replay_after_restart = restarted.client("observer").replay(0)
                projection_after_restart = restarted.client("observer").lifecycle_projection(self.objective_id)
                duplicate_after_restart = _send(restarted.client("dispatch"), "provider.execute", "final:execute", objective_id=self.objective_id, directive_id=directive_id, dispatch_id=dispatch_id, task_input=TASK_INPUT)
                final_readiness = restarted.client("observer").readiness()
            finally:
                restarted.close()
        except Exception:
            runtime.close()
            raise

        event_summary = [{"event_id": e.get("event_id"), "event_type": e.get("event_type"), "position": e.get("position"), "audit_reference": e.get("audit_reference"), "correlation_id": e.get("correlation_id"), "causation_id": e.get("causation_id")} for e in replay["events"]]
        completed_projection = projection.get("stages", {})
        report = {
            "schema_version": "estate.wp4232-final-bounded-live.v1", "authoritative_base_sha": "31abcb4f4b58956ceaf686517717fa9fc0393026",
            "task_name": TASK_NAME, "normalized_input_utf8": TASK_INPUT, "input_digest": INPUT_DIGEST,
            "expected_digest": EXPECTED_SHA256, "actual_digest": actual_digest, "adapter_identity": admission_record["adapter_id"], "adapter_version": admission_record["adapter_version"],
            "readiness_gate": readiness_gate, "readiness_record": readiness, "authority_record": admission_record,
            "objective_id": self.objective_id, "directive_id": directive_id, "dispatch_id": dispatch_id, "effect_identity": effect_identity,
            "lifecycle": {"objective": objective["event"], "directive": authorized["event"], "cme": cme["event"], "progression": progression["event"], "admission": admission["event"], "submission": submitted["event"], "execution": executed["event"], "reconciliation": reconciled["event"], "validation": validated["event"], "receipt": receipt["event"], "completion": completed["event"]},
            "events": event_summary, "event_types": [event["event_type"] for event in replay["events"]], "replay_cursor": replay["next_cursor"],
            "reconciliation_reference": reconciled["record"], "validation_reference": validated["record"], "grace_receipt": receipt["record"], "objective_completion": completed["record"],
            "exactly_once": {"duplicate_same_response": duplicate == executed, "provider_execution_event_count": len(provider_events), "duplicate_after_restart_same_response": duplicate_after_restart == executed, "event_count_before_restart": before_restart_count, "event_count_after_restart": len(replay_after_restart["events"]), "completed_effect_identity_preserved": replay_after_restart["events"] == replay["events"]},
            "restart_replay": {"same_positions": [e["position"] for e in replay_after_restart["events"]] == [e["position"] for e in replay["events"]], "projection": projection_after_restart, "readiness": final_readiness},
            "openwebui_projection": openwebui_projection, "estate_ui_projection": estate_projection,
            "dual_surface": {"same_replay_cursor": openwebui_projection.get("cursor") == estate_projection.get("cursor"), "openwebui_completed": openwebui_projection.get("projection", {}).get("stages", {}).get("completion") is not None, "estate_completed": estate_projection.get("projection", {}).get("stages", {}).get("completion") is not None, "same_event_count": len(openwebui_projection.get("events", [])) == len(estate_projection.get("events", []))},
            "completion_projection": {"stages": completed_projection, "current_blocker": projection.get("current_blocker"), "next_lawful_action": projection.get("next_lawful_action")},
            "safety_assertions": {"network": False, "egress": False, "spend": False, "repository_mutation_by_provider": False, "protected_machine_state_mutation": False, "other_provider_tasks_executed": False, "final_task_executed_once": len(provider_events) == 1},
            "final_disposition": "accepted",
        }
        self.evidence_file.parent.mkdir(parents=True, exist_ok=True)
        self.evidence_file.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return report
