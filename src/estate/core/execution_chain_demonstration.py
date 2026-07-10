"""Deterministic end-to-end execution-chain demonstration for WP-0509."""

from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from estate.core.codex_bridge import CodexBridgeResult, CodexParsedOutput
from estate.core.codex_live_execution_gate import LiveExecutionAuthorization
from estate.core.execution_dispatch import DispatchRequest, enqueue_dispatch_request, inspect_dispatch_item
from estate.core.execution_session_controller import ExecutionSessionController
from estate.core.execution_activity import EVENTS_OUTPUT as ACTIVITY_EVENTS_OUTPUT, generate_execution_activity_surface

WORK_PACKAGE_ID = "WP-0509"
PROVIDER_ID = "codex-cli-openai"
PROVIDER_TYPE = "codex-cli"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _rel(path: Path, root: Path) -> str:
    return str(path.relative_to(root)).replace("\\", "/")


@dataclass
class FakeProviderRunner:
    status: str = "succeeded"
    calls: list[dict[str, Any]] = field(default_factory=list)

    def __call__(self, bridge_request: Any, *, root: str | Path, dry_run: bool = False) -> CodexBridgeResult:
        base = Path(root)
        self.calls.append({"request_id": bridge_request.request_id, "dry_run": dry_run, "called_at": _now()})
        started = _now()
        fake_dir = base / "runtime/execution_adapters/fake_provider"
        events = fake_dir / f"{bridge_request.request_id}_events.jsonl"
        status = fake_dir / f"{bridge_request.request_id}_status.json"
        audit = fake_dir / f"{bridge_request.request_id}_audit.json"
        events.parent.mkdir(parents=True, exist_ok=True)
        events.write_text(json.dumps({"event_type": "fake_provider_invoked", "request_id": bridge_request.request_id}) + "\n", encoding="utf-8")
        _write_json(status, {"status": self.status, "request_id": bridge_request.request_id})
        _write_json(audit, {"fake_provider_runner_used": True, "live_provider_called": False})
        failed = self.status != "succeeded"
        return CodexBridgeResult(
            request_id=bridge_request.request_id,
            status="failed" if failed else "succeeded",
            started_at=started,
            finished_at=_now(),
            duration_seconds=0.0,
            command=["fake-provider-runner"],
            cwd=str(base),
            provider=bridge_request.provider,
            model=bridge_request.model,
            profile_label=bridge_request.codex_home_profile,
            sandbox=bridge_request.sandbox,
            exit_code=1 if failed else 0,
            stdout="fake provider completed" if not failed else "",
            stderr="fake provider failed" if failed else "",
            stdout_hash="fake-stdout-hash",
            stderr_hash="fake-stderr-hash",
            parsed_output=CodexParsedOutput(mode="fake", final_message="Fake provider completed." if not failed else "Fake provider failed."),
            usage=None,
            final_message="Fake provider completed." if not failed else "Fake provider failed.",
            lifecycle_events=[{"event_type": "execution_complete" if not failed else "execution_failed", "at": _now()}],
            events_path=_rel(events, base),
            status_snapshot_path=_rel(status, base),
            audit_path=_rel(audit, base),
            changed_files=["docs/demonstrations/wp-0509_fake_output.md"] if not failed else [],
            tests_run=[],
            known_limitations=[],
            promotion_recommendation="manual_review_required",
            validation_errors=["fake provider failure requested"] if failed else [],
        )


def _fixture(root: Path, *, invalid_authorization: bool = False) -> tuple[str, Path]:
    prompt = root / "work_packages/WP-0509_demo_prompt.md"
    prompt.parent.mkdir(parents=True, exist_ok=True)
    prompt.write_text("Harmless deterministic WP-0509 fake provider prompt.\n", encoding="utf-8")
    dispatch_id = "dispatch-wp-0509-demo"
    decision = "decision/WP-0509/demo-authorized"
    enqueue_dispatch_request(DispatchRequest(
        dispatch_id=dispatch_id,
        work_package_id=WORK_PACKAGE_ID,
        title="WP-0509 deterministic execution-chain demonstration",
        requested_by="Traffic Controller / Operations Manager",
        assigned_worker="codex_cloud_web",
        provider=PROVIDER_ID,
        profile_label="default",
        classification="Estate Internal",
        priority="High",
        state="Ready",
        prompt_source=_rel(prompt, root),
        sandbox="workspace-write",
        allowed_read_paths=["work_packages"],
        allowed_write_paths=["docs/demonstrations"],
        allowed_providers=[PROVIDER_ID],
        provider_metadata={
            "provider_type": PROVIDER_TYPE,
            "authorization_reference": decision,
            "decision_reference": decision,
            "traffic_controller_authorization_reference": "tc/WP-0509/demo-authorized",
            "steward_approval_reference": "steward/WP-0509/demo-approved",
            "validation_required": True,
            "codex_home_profile": "default",
            "approval_policy": "never",
            "json_mode": True,
            "requested_by": "Traffic Controller / Operations Manager",
        },
    ), root=root)
    # Preview prepares the adapter request and writes the handoff reference.
    controller = ExecutionSessionController(root=root)
    temp_auth = root / "runtime/execution_adapters/authorizations/WP-0509-temp.json"
    _write_json(temp_auth, {
        "execution_authorization_id": "auth-wp-0509-demo-temp",
        "dispatch_id": dispatch_id,
        "adapter_request_id": "adapter-dispatch-wp-0509-demo",
        "provider_id": PROVIDER_ID,
        "provider_type": PROVIDER_TYPE,
        "work_package_id": WORK_PACKAGE_ID,
        "decision_reference": decision,
        "traffic_controller_authorization_reference": "tc/WP-0509/demo-authorized",
        "steward_approval_reference": "steward/WP-0509/demo-approved",
        "approved_by": "Steward",
        "approved_at": _now(),
        "approval_scope": "deterministic fake provider demonstration only",
        "allowed_sandbox": "workspace-write",
        "allowed_read_paths": ["work_packages"],
        "allowed_write_paths": ["docs/demonstrations"],
        "approved_codex_profile": "default",
        "workspace_clean_required": False,
    })
    preview = controller.preview(dispatch_id, temp_auth)
    adapter_request_id = preview.get("adapter_request_id") or "adapter-dispatch-wp-0509-demo"
    auth_path = root / "runtime/execution_adapters/authorizations/auth-wp-0509-demo.json"
    auth = json.loads(temp_auth.read_text(encoding="utf-8"))
    auth["execution_authorization_id"] = "auth-wp-0509-demo"
    auth["adapter_request_id"] = "wrong-adapter-request" if invalid_authorization else adapter_request_id
    _write_json(auth_path, auth)
    return dispatch_id, auth_path


def run_execution_chain_demonstration(*, root: str | Path | None = None, fake_provider_status: str = "succeeded", invalid_authorization: bool = False) -> dict[str, Any]:
    started = _now(); failures: list[str] = []; warnings: list[str] = []
    owns_temp = root is None
    with tempfile.TemporaryDirectory(prefix="estate-wp-0509-") as tmp:
        base = Path(tmp) if owns_temp else Path(root)  # type: ignore[arg-type]
        base.mkdir(parents=True, exist_ok=True)
        dispatch_id, auth_path = _fixture(base, invalid_authorization=invalid_authorization)
        runner = FakeProviderRunner(status=fake_provider_status)
        controller = ExecutionSessionController(root=base, gate_factory=lambda: __import__("estate.core.codex_live_execution_gate", fromlist=["CodexLiveExecutionGate"]).CodexLiveExecutionGate(root=base, bridge_runner=runner, codex_binary_checker=lambda _: True))
        preview = controller.preview(dispatch_id, auth_path)
        start = controller.start(dispatch_id, auth_path, confirm_live_execution=True)
        session_id = start.get("execution_session_id") or preview.get("execution_session_id")
        if session_id:
            controller.status(session_id); controller.report(session_id); controller.resume(session_id)
        final_item = inspect_dispatch_item(dispatch_id, base)
        activity = generate_execution_activity_surface(base, write=True)
        result = {
            "demonstration_id": f"demo-wp-0509-{uuid4().hex[:8]}", "work_package_id": WORK_PACKAGE_ID,
            "dispatch_id": dispatch_id, "execution_session_id": session_id, "execution_attempt_id": start.get("execution_attempt_id"),
            "adapter_request_id": start.get("adapter_request_id") or preview.get("adapter_request_id"), "provider_id": PROVIDER_ID,
            "preview_status": preview.get("state"), "start_status": start.get("state"), "provider_call_count": len(runner.calls),
            "provider_result_status": (start.get("result") or {}).get("status") or ("completed" if start.get("result_reference") else None),
            "reconciliation_status": "reconciled" if start.get("reconciliation_reference") else None,
            "final_dispatch_state": final_item.state,
            "lease_released": not (base / "runtime/execution_adapters/leases" / f"{dispatch_id}.json").exists(),
            "activity_evidence_count": sum((activity.get("summary") or {}).get(k, 0) for k in ["active_count", "blocked_count", "attention_required_count", "failed_count", "recently_completed_count"]),
            "institutional_acceptance_state": final_item.provider_metadata.get("institutional_acceptance_state", "not_granted"),
            "live_provider_called": False, "fake_provider_runner_used": True, "started_at": started, "finished_at": _now(),
            "artifacts": {"root": str(base), "session": start.get("execution_session_id"), "result": start.get("result_reference"), "reconciliation": start.get("reconciliation_reference"), "activity": str(ACTIVITY_EVENTS_OUTPUT), "report": f"runtime/execution_adapters/reports/{session_id}_session.md" if session_id else None},
            "failures": failures, "warnings": warnings,
        }
        required = {"provider_call_count": 1, "final_dispatch_state": "Validation", "institutional_acceptance_state": "not_granted", "live_provider_called": False, "fake_provider_runner_used": True}
        if not invalid_authorization and fake_provider_status == "succeeded":
            for key, expected in required.items():
                if result.get(key) != expected: failures.append(f"{key} expected {expected!r}, got {result.get(key)!r}")
            if preview.get("live_provider_called") is not False: failures.append("preview called provider")
            if not result["lease_released"]: failures.append("lease was not released")
            if len(runner.calls) != 1: failures.append("duplicate provider call detected")
        demo_dir = base / "runtime/execution_adapters/demonstrations"
        result_path = _write_json(demo_dir / f"{result['demonstration_id']}.json", result)
        report_path = base / "runtime/execution_adapters/reports" / f"{result['demonstration_id']}_end_to_end.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(format_demonstration_report(result), encoding="utf-8")
        result["artifacts"].update({"demonstration_result": _rel(result_path, base), "demonstration_report": _rel(report_path, base)})
        _write_json(result_path, result)
        if owns_temp:
            # Preserve the isolated evidence outside the context manager only by returning copied payload; no active runtime touched.
            result["artifacts"]["temporary_root_removed_after_run"] = True
        return result


def format_demonstration_report(result: dict[str, Any]) -> str:
    lines = ["# WP-0509 End-to-End Execution Chain Demonstration", "", f"Demonstration: `{result.get('demonstration_id')}`", f"Dispatch: `{result.get('dispatch_id')}`", f"Session: `{result.get('execution_session_id')}`", f"Provider calls: `{result.get('provider_call_count')}`", f"Final dispatch state: `{result.get('final_dispatch_state')}`", f"Lease released: `{result.get('lease_released')}`", f"Institutional acceptance: `{result.get('institutional_acceptance_state')}`", "", "This deterministic demonstration uses a fake provider runner and makes no live provider calls.", ""]
    if result.get("failures"):
        lines += ["## Failures", *[f"- {f}" for f in result["failures"]]]
    else:
        lines += ["## Result", "PASS"]
    return "\n".join(lines) + "\n"
