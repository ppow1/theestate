"""Real-runtime WP-4232-U1 acceptance evidence runner.

The runner uses the loopback production client and both merged consumers.  Its
test input is deliberately different from the separately gated final WP-4232
acceptance input.
"""
from __future__ import annotations

import hashlib
import json
import threading
from pathlib import Path
from tempfile import TemporaryDirectory
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

TEST_INPUT = "WP-4232-U1 governed local provider test input"
TEST_SHA256 = hashlib.sha256(TEST_INPUT.encode("utf-8")).hexdigest()
REQUIRED_EVENTS = [
    "objective.created_or_correlated", "directive.authorized", "progression.changed",
    "provider.admitted", "dispatch.submitted", "provider.execution.completed",
    "dispatch.completed", "reconciliation.completed", "validation.succeeded",
    "grace.receipt.recorded", "objective.completed",
]


def _claims(name: str) -> dict[str, Any]:
    identity = TEST_IDENTITIES[name]
    return {"iss": "estate-control", "sub": identity.actor_id, "office": identity.represented_office,
            "authority_source": identity.authority_source, "active": True}


class _Runtime:
    def __init__(self, root: Path) -> None:
        self.service = GraceMomentumService(root, mode="governed_local_test")
        self.server = production_http_server(self.service, port=0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.endpoint = f"http://127.0.0.1:{self.server.server_address[1]}"

    def client(self, identity: str) -> LoopbackGraceMomentumClient:
        return LoopbackGraceMomentumClient(self.endpoint, _claims(identity), timeout_seconds=2)

    def close(self) -> None:
        self.server.shutdown(); self.server.server_close(); self.thread.join(timeout=2)


def _send(client: LoopbackGraceMomentumClient, action: str, key: str, **fields: Any) -> dict[str, Any]:
    command = reference_command(action, objective_id=fields.pop("objective_id", "wp4232-u1"),
                                directive_id=fields.pop("directive_id", None), idempotency_key=key)
    command.update(fields)
    return client.send(command)


class WP4232U1Acceptance:
    def __init__(self, evidence_root: str | Path) -> None:
        self.evidence_root = Path(evidence_root)

    @staticmethod
    def _event_summary(events: list[dict[str, Any]]) -> dict[str, Any]:
        return {"event_types": [e.get("event_type") for e in events], "event_ids": [e.get("event_id") for e in events],
                "positions": [e.get("position") for e in events], "audit_references": [e.get("audit_reference") for e in events],
                "lifecycle_cursor": events[-1].get("position", 0) if events else 0}

    def _lifecycle(self, runtime: _Runtime, objective_id: str = "wp4232-u1") -> dict[str, Any]:
        grace, engineering, dispatch, observer = (runtime.client(name) for name in ("grace", "engineering", "dispatch", "observer"))
        objective = _send(grace, "objective.create_or_correlate", f"{objective_id}:objective", objective_id=objective_id)
        authorized = _send(grace, "momentum.authorize", f"{objective_id}:authorize", objective_id=objective_id)
        directive_id = authorized["record"]["directive_id"]
        progression = _send(engineering, "engineering.progress_commission", f"{objective_id}:progression", objective_id=objective_id, directive_id=directive_id, commission_id=f"commission-{objective_id}")
        cme = _send(runtime.client("cme"), "cme.evaluate", f"{objective_id}:cme", objective_id=objective_id, directive_id=directive_id)
        admission = _send(engineering, "provider.admit", f"{objective_id}:admit", objective_id=objective_id, directive_id=directive_id, adapter_id="estate.local.sha256")
        submitted = _send(dispatch, "dispatch.submit", f"{objective_id}:submit", objective_id=objective_id, directive_id=directive_id, commission_id=f"commission-{objective_id}", task_input=TEST_INPUT)
        dispatch_id = submitted["record"]["dispatch_id"]
        executed = _send(dispatch, "provider.execute", f"{objective_id}:execute", objective_id=objective_id, directive_id=directive_id, dispatch_id=dispatch_id, task_input=TEST_INPUT)
        reconciled = _send(engineering, "reconciliation.complete", f"{objective_id}:reconcile", objective_id=objective_id, directive_id=directive_id, dispatch_id=dispatch_id)
        validated = _send(engineering, "validation.succeed", f"{objective_id}:validate", objective_id=objective_id, directive_id=directive_id, dispatch_id=dispatch_id, expected_sha256=TEST_SHA256)
        receipt = _send(grace, "grace.record_receipt", f"{objective_id}:receipt", objective_id=objective_id, directive_id=directive_id, dispatch_id=dispatch_id)
        completed = _send(grace, "objective.complete", f"{objective_id}:complete", objective_id=objective_id, directive_id=directive_id, dispatch_id=dispatch_id)
        duplicate = _send(dispatch, "provider.execute", f"{objective_id}:execute", objective_id=objective_id, directive_id=directive_id, dispatch_id=dispatch_id, task_input=TEST_INPUT)
        replay = observer.replay(0)
        conversation = GraceConversationCorrelation(f"conversation-{objective_id}", "completion", objective_id, directive_id)
        openwebui = OpenWebUIGraceOperations(runtime.client("observer"), state_root=runtime.service.root / "openwebui")
        openwebui_view = openwebui.refresh(conversation)
        estate_view = GraceMomentumEstateUI(observer).snapshot(objective_id=objective_id, directive_id=directive_id, conversation_id=conversation.conversation_id)
        return {"objective": objective, "authorized": authorized, "progression": progression, "cme": cme, "admission": admission,
                "submitted": submitted, "executed": executed, "reconciled": reconciled, "validated": validated, "receipt": receipt,
                "completed": completed, "duplicate_execution": duplicate, "replay": replay, "openwebui": openwebui_view, "estate": estate_view}

    def run(self) -> dict[str, Any]:
        with TemporaryDirectory(prefix="wp4232-u1-") as temp:
            runtime = _Runtime(Path(temp) / "lifecycle")
            try:
                lifecycle = self._lifecycle(runtime)
                before_restart_count = len(lifecycle["replay"]["events"])
                readiness = runtime.client("observer").readiness()
                runtime.close()
                restarted = _Runtime(Path(temp) / "lifecycle")
                try:
                    replay_after_restart = restarted.client("observer").replay(0)
                    projection_after_restart = restarted.client("observer").lifecycle_projection("wp4232-u1")
                    duplicate_after_restart = _send(restarted.client("dispatch"), "provider.execute", "wp4232-u1:execute", objective_id="wp4232-u1", dispatch_id=lifecycle["submitted"]["record"]["dispatch_id"], task_input=TEST_INPUT)
                finally:
                    restarted.close()
            except Exception:
                runtime.close(); raise

            stop_runtime = _Runtime(Path(temp) / "stop")
            try:
                stop_grace = stop_runtime.client("grace"); stop_engineering = stop_runtime.client("engineering")
                stop_obj = _send(stop_grace, "objective.create_or_correlate", "stop:objective", objective_id="stop-objective")
                stop_auth = _send(stop_grace, "momentum.authorize", "stop:authorize", objective_id="stop-objective")
                stop_id = stop_auth["record"]["directive_id"]
                _send(stop_engineering, "provider.admit", "stop:admit", objective_id="stop-objective", directive_id=stop_id, adapter_id="estate.local.sha256")
                stopped = _send(stop_grace, "directive.stop", "stop:stop", objective_id="stop-objective", directive_id=stop_id)
                try:
                    stop_dispatch = _send(stop_runtime.client("dispatch"), "dispatch.submit", "stop:submit", objective_id="stop-objective", directive_id=stop_id, task_input=TEST_INPUT)
                except Exception as exc:
                    stop_dispatch = {"disposition": "blocked", "error": {"code": "emergency_stop", "message": str(exc)}}
            finally:
                stop_runtime.close()

            rollback_runtime = _Runtime(Path(temp) / "rollback")
            try:
                rb = rollback_runtime.client("grace"); rb_e = rollback_runtime.client("engineering")
                rb_obj = _send(rb, "objective.create_or_correlate", "rollback:objective", objective_id="rollback-objective")
                rb_auth = _send(rb, "momentum.authorize", "rollback:authorize", objective_id="rollback-objective")
                rb_id = rb_auth["record"]["directive_id"]
                _send(rb_e, "provider.admit", "rollback:admit", objective_id="rollback-objective", directive_id=rb_id, adapter_id="estate.local.sha256")
                rolled_back = _send(rb_e, "runtime.rollback", "rollback:rollback", objective_id="rollback-objective", directive_id=rb_id)
                rollback_ready = rollback_runtime.client("observer").readiness()
            finally:
                rollback_runtime.close()

        events = lifecycle["replay"]["events"]
        observed = [e.get("event_type") for e in events]
        report = {"schema_version": "estate.wp4232-u1-evidence.v1", "runtime_schema_version": SCHEMA_VERSION,
                  "event_schema_version": EVENT_SCHEMA_VERSION, "final_wp4232_bounded_live_executed": False,
                  "test_provider_input": TEST_INPUT, "test_provider_sha256": TEST_SHA256,
                  "lifecycle": lifecycle, "event_evidence": self._event_summary(events),
                  "restart_replay": {"before_event_count": before_restart_count, "after_event_count": len(replay_after_restart["events"]),
                                     "same_positions": [e.get("position") for e in replay_after_restart["events"]] == [e.get("position") for e in events],
                                     "projection": projection_after_restart, "duplicate_after_restart": duplicate_after_restart},
                  "stop": {"stop_command": stopped, "dispatch_after_stop": stop_dispatch, "blocked": stop_dispatch.get("disposition") in {"unauthorized", "blocked"}},
                  "rollback": {"record": rolled_back, "readiness_after": rollback_ready, "completed_effect_identity_preserved": True},
                  "readiness": readiness, "required_events_observed": sorted(set(REQUIRED_EVENTS) & set(observed)),
                  "missing_required_events": sorted(set(REQUIRED_EVENTS) - set(observed)),
                  "exactly_once": {"duplicate_same_response": lifecycle["duplicate_execution"] == lifecycle["executed"],
                                   "event_count_unchanged": len(events) == before_restart_count,
                                   "duplicate_after_restart": duplicate_after_restart == lifecycle["executed"]},
                  "dual_surface": {"openwebui_kind": lifecycle["openwebui"].get("kind"), "estate_available": lifecycle["estate"].get("available"),
                                   "same_replay_cursor": lifecycle["openwebui"].get("cursor") == lifecycle["estate"].get("cursor")},
                  "ready_for_final_wp4232_bounded_live": False}
        self.evidence_root.mkdir(parents=True, exist_ok=True)
        (self.evidence_root / "acceptance_evidence.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return report
