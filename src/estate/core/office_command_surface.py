"""Real local Office command surface actions for WP-0213."""
from __future__ import annotations

import json
import traceback
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from estate.core.paths import ESTATE_ROOT
from estate.core.service_status_board import generate_service_status_board
from estate.core.provider_sync import sync_ollama_providers
from estate.core.production_readiness_validation import generate_production_readiness_report
from estate.core.work_package_validation import validate_work_package
from estate.core.assignment_queue import generate_assignment_queue
from estate.core.mailbox_index import generate_mailbox_index
from estate.core.operations_notification_center import generate_operations_notification_center, acknowledge_operations_notification
from estate.core.alfred_duty import run_alfred_duty
from estate.core.daily_board_integration import generate_daily_board_integration
from estate.core.mission_control_workspace import build_mission_control_workspace
from estate.core.morning_briefing import generate_morning_briefing
from estate.core.orchestrator_intake_decisions import OrchestratorIntakeDecisionRuntime
from estate.core.operations_control_runtime import OperationsControlRuntime
from estate.core.operations_manager import OperationsDecision
from estate.core.execution_session_controller import ExecutionSessionController
from estate.core.execution_attempt_runtime import ExecutionAttemptRuntime
from estate.core.execution_result_reconciliation_runtime import inspect_reconciliation, reconcile_result, format_reconciliation_report
from estate.core.operations_center_settings import save_settings_document, reset_operations_center_settings, export_operations_center_settings, import_operations_center_settings, SETTINGS_OUTPUT

VALID_OUTCOMES = {"completed", "queued", "blocked", "failed"}
RESULT_LOG = "runtime/steward/office_command_surface_action_results.jsonl"

@dataclass
class OfficeActionResult:
    action_id: str
    action_label: str
    target_tab: str
    outcome: str
    steward_message: str
    source_handler: str
    artifacts_read: list[str] = field(default_factory=list)
    artifacts_written: list[str] = field(default_factory=list)
    runtime_state_changed: list[str] = field(default_factory=list)
    authority_gating_status: str = "safe_local_action"
    diagnostics_path: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds"))

    def to_dict(self) -> dict[str, Any]:
        if self.outcome not in VALID_OUTCOMES:
            raise ValueError(f"Invalid action outcome: {self.outcome}")
        return asdict(self)


def _root(root=None) -> Path:
    return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())

def _rel(root: Path, path: str | Path) -> str:
    p = Path(path)
    try:
        return str(p.relative_to(root)).replace('\\', '/') if p.is_absolute() else str(p).replace('\\', '/')
    except ValueError:
        return str(p).replace('\\', '/')

def _write_result(root: Path, result: OfficeActionResult) -> OfficeActionResult:
    path = root / RESULT_LOG
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a', encoding='utf-8') as f:
        f.write(json.dumps(result.to_dict(), sort_keys=True) + '\n')
    return result

def _diagnostic(root: Path, action_id: str, exc: BaseException) -> str:
    safe = ''.join(ch if ch.isalnum() or ch in '-_.' else '_' for ch in action_id)
    rel = f"runtime/steward/diagnostics/{safe}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.txt"
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(''.join(traceback.format_exception(exc)), encoding='utf-8')
    return rel


def _completed(action_id, label, tab, handler, msg, *, read=(), written=(), state=()):
    return OfficeActionResult(action_id, label, tab, 'completed', msg, handler, list(read), list(written), list(state))

def _blocked(action_id, label, tab, handler, reason, *, read=()):
    return OfficeActionResult(action_id, label, tab, 'blocked', reason, handler, list(read), [], [], 'gated_or_missing_requirement')


def refresh_ai_services(root=None, **_: Any) -> OfficeActionResult:
    base = _root(root)
    board = generate_service_status_board(root=base, write=True)
    created, ec_id = sync_ollama_providers()
    msg = f"AI services refreshed locally; service board has {len(board.get('services') or [])} service rows and provider sync created {len(created)} provider(s). Estate change: {ec_id}."
    return _completed('ai_services.refresh_local_inventory', 'Refresh local AI service inventory', 'ai-services-models', 'estate.core.service_status_board.generate_service_status_board + estate.core.provider_sync.sync_ollama_providers', msg, read=['data/registry/providers.json', 'data/registry/services.json'], written=['runtime/services/service_status_board.json', 'operations/services/service_status_board.md', 'data/registry/providers.json'], state=['local provider registry may be updated'])

def run_production_readiness(root=None, **_: Any) -> OfficeActionResult:
    base = _root(root); payload = generate_production_readiness_report(root=base, write=True)
    status = (payload.get('summary') or {}).get('status') or payload.get('status') or 'generated'
    return _completed('validation.run_production_readiness', 'Run production readiness refresh', 'validation', 'estate.core.production_readiness_validation.generate_production_readiness_report', f"Production readiness refresh completed with status {status}. Evidence is not institutional acceptance.", written=['runtime/validation/production_readiness.json', 'operations/validation/production_readiness.md'], state=['validation readiness artifacts refreshed'])

def validate_selected_work_package(root=None, work_package_id: str | None = None, **_: Any) -> OfficeActionResult:
    if not work_package_id:
        return _blocked('work_packages.validate_selected', 'Validate selected work package', 'work-packages', 'estate.core.work_package_validation.validate_work_package', 'Select a work package id before running validation.')
    base = _root(root); payload = validate_work_package(work_package_id, root=base, write=True)
    status = payload.get('validation_status')
    return _completed('work_packages.validate_selected', 'Validate selected work package', 'work-packages', 'estate.core.work_package_validation.validate_work_package', f"Validation attempted for {payload.get('work_package_id')} with status {status}.", read=[f'collaboration/work_packages/**/{payload.get("work_package_id")}_*.md'], written=[f'runtime/validation/work_packages/{payload.get("validation_id")}.json', f'operations/validation/work_packages/{payload.get("validation_id")}.md'], state=['work package validation evidence generated'])

def refresh_work_package_queue(root=None, **_: Any) -> OfficeActionResult:
    base = _root(root); payload = generate_assignment_queue(root=base, write=True)
    return _completed('work_packages.refresh_assignment_queue', 'Refresh assignment queue', 'work-packages', 'estate.core.assignment_queue.generate_assignment_queue', f"Assignment queue refreshed with {len(payload.get('work_packages') or [])} work package(s).", read=['collaboration/work_packages'], written=['runtime/work_packages/assignment_queue.json', 'operations/work_packages/assignment_queue.md'], state=['work package pipeline refreshed'])

def refresh_notifications(root=None, **_: Any) -> OfficeActionResult:
    base = _root(root); payload = generate_operations_notification_center(root=base, write=True)
    return _completed('notifications.refresh_center', 'Refresh notification center', 'notifications', 'estate.core.operations_notification_center.generate_operations_notification_center', f"Notification center refreshed with {(payload.get('summary') or {}).get('filtered_notification_count', 0)} visible notification(s).", written=['runtime/notifications/operations_notification_center.json', 'operations/notifications/operations_notification_center.md'], state=['notification center refreshed'])

def local_ack_notification(root=None, notification_id: str | None = None, **_: Any) -> OfficeActionResult:
    if not notification_id:
        return _blocked('notifications.local_acknowledge', 'Acknowledge notification locally', 'notifications', 'estate.core.operations_notification_center.acknowledge_operations_notification', 'Select a notification id before acknowledging it locally.')
    base = _root(root); acknowledge_operations_notification(notification_id, root=base); generate_operations_notification_center(root=base, write=True)
    return _completed('notifications.local_acknowledge', 'Acknowledge notification locally', 'notifications', 'estate.core.operations_notification_center.acknowledge_operations_notification', f"Notification {notification_id} acknowledged in local Notification Center state only; authoritative source closure was not changed.", read=['runtime/notifications/operations_notification_center.json'], written=['runtime/notifications/operations_notification_center_acknowledgements.json', 'runtime/notifications/operations_notification_center.json'], state=['local acknowledgement recorded'])

def request_alfred_briefing(root=None, **_: Any) -> OfficeActionResult:
    base = _root(root); run_alfred_duty(root=base, write=True)
    return _completed('alfred.request_briefing', 'Request Alfred briefing', 'alfred', 'estate.core.alfred_duty.run_alfred_duty', 'Alfred duty briefing generated locally. Alfred did not approve or execute privileged actions.', written=['runtime/alfred/duty_state.json', 'runtime/alfred/duty_runs.jsonl', 'operations/alfred/duty_summary.md', 'runtime/residents/presence.json'], state=['Alfred local duty status refreshed'])

def refresh_mission_control(root=None, **_: Any) -> OfficeActionResult:
    base = _root(root); build_mission_control_workspace(base)
    return _completed('mission_control.refresh_payload', 'Refresh Mission Control payload', 'mission-control', 'estate.core.mission_control_workspace.build_mission_control_workspace', 'Mission Control payload refreshed from local artifacts.', written=['runtime/steward/mission_control_workspace.json'], state=['mission control runtime payload refreshed'])

def record_orchestrator_intake_decision(root=None, intake_id: str | None = None, decision: str | None = None, decided_by: str | None = None, reason: str | None = None, **params: Any) -> OfficeActionResult:
    if not intake_id or not decision or not decided_by:
        return _blocked('orchestrator_intake.record_decision', 'Record Orchestrator intake decision', 'operational-activity', 'estate.core.orchestrator_intake_decisions.OrchestratorIntakeDecisionRuntime.decide', 'intake_id, decision, and decided_by are required.')
    base = _root(root)
    artifact, paths = OrchestratorIntakeDecisionRuntime(base).decide(intake_id=intake_id, decision=decision, decided_by=decided_by, reason=reason, metadata={k: v for k, v in params.items() if k in {'summary_safe', 'boundary_review_completed'}})
    return _completed('orchestrator_intake.record_decision', 'Record Orchestrator intake decision', 'operational-activity', 'estate.core.orchestrator_intake_decisions.OrchestratorIntakeDecisionRuntime.decide', f"Decision {artifact.decision} recorded for {artifact.intake_id}; next state is {artifact.next_state}.", read=['runtime/orchestrator/intake/status/queue.json'], written=[_rel(base, paths['decision']), 'runtime/orchestrator/intake/status/latest.json', 'runtime/orchestrator/intake/status/queue.json', 'runtime/operations/status/latest.json'], state=['orchestrator intake decision state updated'])

def record_operations_control_decision(root=None, decision_type: str | None = None, target_type: str | None = None, target_id: str | None = None, decided_by: str | None = None, reason: str | None = None, priority: str = "normal", **params: Any) -> OfficeActionResult:
    if not decision_type or not target_type or not decided_by:
        return _blocked('operations_control.record_decision', 'Record operations-control decision', 'operational-activity', 'estate.core.operations_control_runtime.OperationsControlRuntime.record_decision', 'decision_type, target_type, and decided_by are required.')
    base = _root(root)
    decision = OperationsDecision.create(
        decided_by=decided_by,
        decision_type=decision_type,
        target_type=target_type,
        target_id=target_id or None,
        priority=priority or 'normal',
        reason=reason or f'Office recorded {decision_type} decision for {target_type}.',
        assignment_label=params.get('assignment_label'),
        provider_id=params.get('provider_id'),
        worker_id=params.get('worker_id'),
        requires_boundary_review=bool(params.get('requires_boundary_review')) or decision_type == 'request_boundary_review',
        requires_steward_attention=decision_type in {'escalate', 'request_boundary_review'},
        summary_safe=bool(params.get('summary_safe')),
        metadata={k: v for k, v in params.items() if k not in {'assignment_label', 'provider_id', 'worker_id', 'requires_boundary_review', 'summary_safe'}},
    )
    paths = OperationsControlRuntime(base).record_decision(decision)
    return _completed('operations_control.record_decision', 'Record operations-control decision', 'operational-activity', 'estate.core.operations_control_runtime.OperationsControlRuntime.record_decision', f"Operations decision {decision.decision_type} recorded for {decision.target_type}:{decision.target_id or ''}.", read=['runtime/operations/control/status/latest.json'], written=[_rel(base, paths['decision']), 'runtime/operations/control/status/summary.json', 'runtime/operations/control/status/summary.md', 'runtime/operations/status/latest.json'], state=['operations-control decision artifact recorded'])



def settings_load_current(root=None, **_: Any) -> OfficeActionResult:
    return _completed('settings.load_current', 'Load current settings', 'settings', 'estate.core.operations_center_settings.load_operations_center_settings', 'Current settings are loaded in the refreshed Office payload.', read=[SETTINGS_OUTPUT], state=['settings payload refreshed'])

def settings_save_apply(root=None, settings_json: str | None = None, **params: Any) -> OfficeActionResult:
    if not settings_json:
        return _blocked('settings.save_apply', 'Save and apply settings', 'settings', 'estate.core.operations_center_settings.save_settings_document', 'settings_json is required.')
    base = _root(root)
    try:
        document = json.loads(settings_json)
        settings = document.get('settings', document) if isinstance(document, dict) else None
        if not isinstance(settings, dict):
            raise ValueError('settings_json must be a settings object or export document.')
        save_settings_document(base, settings, backup=True)
    except Exception as exc:
        return OfficeActionResult('settings.save_apply', 'Save and apply settings', 'settings', 'failed', f'Settings were not saved: {exc}', 'estate.core.operations_center_settings.save_settings_document')
    return _completed('settings.save_apply', 'Save and apply settings', 'settings', 'estate.core.operations_center_settings.save_settings_document', 'Settings saved atomically and will be applied by the refreshed Office payload.', read=[SETTINGS_OUTPUT], written=[SETTINGS_OUTPUT], state=['settings persisted', 'office payload configuration changed'])

def settings_reset_defaults(root=None, **_: Any) -> OfficeActionResult:
    reset_operations_center_settings(_root(root))
    return _completed('settings.reset_defaults', 'Reset settings to defaults', 'settings', 'estate.core.operations_center_settings.reset_operations_center_settings', 'Settings reset to documented defaults.', written=[SETTINGS_OUTPUT], state=['settings persisted', 'office payload configuration changed'])

def settings_export(root=None, **_: Any) -> OfficeActionResult:
    base=_root(root); payload=export_operations_center_settings(base); rel='runtime/steward/operations_center_settings_export.json'; path=base/rel; path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(payload, indent=2, sort_keys=True)+'\n', encoding='utf-8')
    return _completed('settings.export', 'Export settings', 'settings', 'estate.core.operations_center_settings.export_operations_center_settings', f'Settings export written to {rel}.', read=[SETTINGS_OUTPUT], written=[rel], state=['settings export artifact written'])

def settings_import(root=None, settings_json: str | None = None, **_: Any) -> OfficeActionResult:
    if not settings_json:
        return _blocked('settings.import', 'Import settings', 'settings', 'estate.core.operations_center_settings.import_operations_center_settings', 'settings_json is required.')
    base=_root(root)
    try:
        document=json.loads(settings_json); payload=import_operations_center_settings(base, document)
    except Exception as exc:
        return OfficeActionResult('settings.import', 'Import settings', 'settings', 'failed', f'Import rejected without changing active settings: {exc}', 'estate.core.operations_center_settings.import_operations_center_settings')
    written=[SETTINGS_OUTPUT] + ([payload.get('import_backup_path')] if payload.get('import_backup_path') else [])
    return _completed('settings.import', 'Import settings', 'settings', 'estate.core.operations_center_settings.import_operations_center_settings', 'Settings import validated, previous settings backed up, and new settings applied.', read=[SETTINGS_OUTPUT], written=written, state=['settings persisted', 'office payload configuration changed'])

def _truthy(value: Any) -> bool:
    return value is True or str(value).strip().lower() in {"true", "1", "yes", "on", "confirm", "confirmed"}

def _require(action_id: str, label: str, handler: str, params: dict[str, Any], fields: list[str]) -> OfficeActionResult | None:
    missing = [f for f in fields if not str(params.get(f) or "").strip()]
    if missing:
        return _blocked(action_id, label, 'execution-control', handler, 'Required input missing: ' + ', '.join(missing))
    return None

def _session_refs(base: Path, payload: dict[str, Any]) -> tuple[list[str], list[str]]:
    sid = payload.get('execution_session_id')
    read: list[str] = []
    written = ['runtime/execution_adapters/status/sessions_summary.json']
    if sid:
        written += [f'runtime/execution_adapters/sessions/{sid}.json', f'runtime/execution_adapters/session_stages/{sid}.jsonl', f'runtime/execution_adapters/reports/{sid}_session.md']
    if payload.get('result_reference'):
        read.append(str(payload['result_reference']))
    return read, written

def execution_session_preview(root=None, dispatch_id: str | None = None, authorization_path: str | None = None, **params: Any) -> OfficeActionResult:
    label='Preview execution session'; handler='estate.core.execution_session_controller.ExecutionSessionController.preview'; data={'dispatch_id':dispatch_id,'authorization_path':authorization_path}
    if blocked := _require('execution_session.preview', label, handler, data, ['dispatch_id','authorization_path']): return blocked
    base=_root(root); payload=ExecutionSessionController(root=base).preview(str(dispatch_id), str(authorization_path)); read,written=_session_refs(base,payload)
    outcome='blocked' if payload.get('state')=='blocked' else 'completed'
    return OfficeActionResult('execution_session.preview', label, 'execution-control', outcome, f"Preview session {payload.get('execution_session_id')} state={payload.get('state')} readiness={'ready' if not payload.get('blocking_reasons') else 'blocked'} reasons={payload.get('blocking_reasons') or []}.", handler, read, written, ['execution session preview artifact written'], 'governed_preview_no_provider_call')

def execution_session_start(root=None, dispatch_id: str | None = None, authorization_path: str | None = None, confirm_live_execution: Any = None, **params: Any) -> OfficeActionResult:
    label='Start execution session'; handler='estate.core.execution_session_controller.ExecutionSessionController.start'; data={'dispatch_id':dispatch_id,'authorization_path':authorization_path}
    if blocked := _require('execution_session.start', label, handler, data, ['dispatch_id','authorization_path']): return blocked
    base=_root(root); payload=ExecutionSessionController(root=base).start(str(dispatch_id), str(authorization_path), confirm_live_execution=_truthy(confirm_live_execution)); read,written=_session_refs(base,payload)
    outcome='completed' if payload.get('state') in {'completed_execution','validation_ready'} else 'blocked' if payload.get('state')=='blocked' else 'failed' if payload.get('state')=='failed' else 'completed'
    return OfficeActionResult('execution_session.start', label, 'execution-control', outcome, f"Start session {payload.get('execution_session_id')} state={payload.get('state')} stage={payload.get('current_stage')} reasons={payload.get('blocking_reasons') or []}.", handler, read, written, ['execution session start advanced runtime state'] if outcome=='completed' else [], 'steward_and_traffic_controller_gated')

def execution_session_resume(root=None, session_id: str | None = None, **params: Any) -> OfficeActionResult:
    label='Resume execution session'; handler='estate.core.execution_session_controller.ExecutionSessionController.resume'
    if blocked := _require('execution_session.resume', label, handler, {'session_id':session_id}, ['session_id']): return blocked
    base=_root(root); payload=ExecutionSessionController(root=base).resume(str(session_id)); read,written=_session_refs(base,payload)
    outcome='failed' if payload.get('state')=='failed' else 'completed'
    return OfficeActionResult('execution_session.resume', label, 'execution-control', outcome, f"Resume inspected session {session_id}; state={payload.get('state')} stage={payload.get('current_stage')}.", handler, read, written, ['session resume/reconciliation evidence updated'], 'duplicate_provider_call_protection_preserved')

def execution_session_status(root=None, session_id: str | None = None, **params: Any) -> OfficeActionResult:
    label='Refresh execution-session status'; handler='estate.core.execution_session_controller.ExecutionSessionController.status'
    if blocked := _require('execution_session.status', label, handler, {'session_id':session_id}, ['session_id']): return blocked
    base=_root(root); payload=ExecutionSessionController(root=base).status(str(session_id))
    return _completed('execution_session.status', label, 'execution-control', handler, f"Session {session_id} state={payload.get('state')} stage={payload.get('current_stage')}.", read=[f'runtime/execution_adapters/sessions/{session_id}.json'])

def execution_session_report(root=None, session_id: str | None = None, **params: Any) -> OfficeActionResult:
    label='Generate/open execution-session report'; handler='estate.core.execution_session_controller.ExecutionSessionController.report'
    if blocked := _require('execution_session.report', label, handler, {'session_id':session_id}, ['session_id']): return blocked
    base=_root(root); ExecutionSessionController(root=base).report(str(session_id)); return _completed('execution_session.report', label, 'execution-control', handler, f"Session report generated for {session_id}.", read=[f'runtime/execution_adapters/sessions/{session_id}.json'], written=[f'runtime/execution_adapters/reports/{session_id}_session.md'])

def execution_attempt_cancel_request(root=None, dispatch_id: str | None = None, attempt_id: str | None = None, actor: str | None = None, reason: str | None = None, **params: Any) -> OfficeActionResult:
    label='Request cancellation'; handler='estate.core.execution_attempt_runtime.ExecutionAttemptRuntime.request_cancellation'; data=locals()
    if blocked := _require('execution_attempt.cancel_request', label, handler, data, ['dispatch_id','attempt_id','actor','reason']): return blocked
    base=_root(root); payload=ExecutionAttemptRuntime(root=base).request_cancellation(str(dispatch_id), str(attempt_id), requested_by=str(actor), reason=str(reason))
    return _completed('execution_attempt.cancel_request', label, 'execution-control', handler, f"Cancellation requested for {attempt_id}; provider stop is not claimed. status={payload.get('status')}.", written=[f'runtime/execution_adapters/cancellations/{attempt_id}.json', f'runtime/execution_adapters/attempts/{attempt_id}.json'], state=['cancellation request recorded'])

def execution_attempt_inspect_recovery(root=None, dispatch_id: str | None = None, **params: Any) -> OfficeActionResult:
    label='Inspect recovery state'; handler='estate.core.execution_attempt_runtime.ExecutionAttemptRuntime.inspect_recovery'
    if blocked := _require('execution_attempt.inspect_recovery', label, handler, {'dispatch_id':dispatch_id}, ['dispatch_id']): return blocked
    base=_root(root); payload=ExecutionAttemptRuntime(root=base).inspect_recovery(str(dispatch_id))
    return _completed('execution_attempt.inspect_recovery', label, 'execution-control', handler, f"Recovery classification: {payload.get('classification')}; stale_release_safe={payload.get('stale_release_safe')}.", written=[f'runtime/execution_adapters/recovery/{dispatch_id}.json'])

def execution_attempt_retry_eligibility(root=None, dispatch_id: str | None = None, **params: Any) -> OfficeActionResult:
    label='Inspect retry eligibility'; handler='estate.core.execution_attempt_runtime.ExecutionAttemptRuntime.retry_eligibility'
    if blocked := _require('execution_attempt.retry_eligibility', label, handler, {'dispatch_id':dispatch_id}, ['dispatch_id']): return blocked
    base=_root(root); payload=ExecutionAttemptRuntime(root=base).retry_eligibility(str(dispatch_id))
    return _completed('execution_attempt.retry_eligibility', label, 'execution-control', handler, f"Retry eligible={payload.get('retry_eligible')}; automatic retry started={payload.get('automatic_retry_started')}.", read=['runtime/execution_adapters/attempts'], state=['retry eligibility evidence updated; no retry started'])

def execution_attempt_release_stale(root=None, dispatch_id: str | None = None, attempt_id: str | None = None, reason: str | None = None, confirm_stale_release: Any = None, released_by: str = 'Steward', **params: Any) -> OfficeActionResult:
    label='Release stale lease'; handler='estate.core.execution_attempt_runtime.ExecutionAttemptRuntime.release_stale'; data=locals()
    if blocked := _require('execution_attempt.release_stale', label, handler, data, ['dispatch_id','attempt_id','reason']): return blocked
    if not _truthy(confirm_stale_release): return _blocked('execution_attempt.release_stale', label, 'execution-control', handler, 'Explicit stale-release confirmation is required.')
    base=_root(root)
    try:
        payload=ExecutionAttemptRuntime(root=base).release_stale(str(dispatch_id), str(attempt_id), confirm_stale_release=True, released_by=str(released_by), reason=str(reason))
    except ValueError as exc:
        return _blocked('execution_attempt.release_stale', label, 'execution-control', handler, str(exc), read=[f'runtime/execution_adapters/recovery/{dispatch_id}.json'])
    return _completed('execution_attempt.release_stale', label, 'execution-control', handler, f"Stale lease released for {attempt_id}; retry_authorized={payload.get('retry_authorized')}.", written=[f'runtime/execution_adapters/attempts/{attempt_id}.json'], state=['stale lease explicitly released'])

def execution_result_inspect_reconciliation(root=None, dispatch_id: str | None = None, **params: Any) -> OfficeActionResult:
    label='Inspect execution result reconciliation'; handler='estate.core.execution_result_reconciliation_runtime.inspect_reconciliation'
    if blocked := _require('execution_result.inspect_reconciliation', label, handler, {'dispatch_id':dispatch_id}, ['dispatch_id']): return blocked
    base=_root(root); payload=inspect_reconciliation(str(dispatch_id), base)
    return _completed('execution_result.inspect_reconciliation', label, 'execution-control', handler, f"Reconciliation status={payload.get('status')}; institutional acceptance={payload.get('institutional_acceptance_state')}.", read=[f'runtime/execution_adapters/reconciliation/{dispatch_id}.json'])

def execution_result_reconcile(root=None, dispatch_id: str | None = None, result_path: str | None = None, **params: Any) -> OfficeActionResult:
    label='Reconcile execution result'; handler='estate.core.execution_result_reconciliation_runtime.reconcile_result'
    if blocked := _require('execution_result.reconcile', label, handler, {'dispatch_id':dispatch_id,'result_path':result_path}, ['dispatch_id','result_path']): return blocked
    base=_root(root); payload=reconcile_result(str(dispatch_id), str(result_path), base)
    return _completed('execution_result.reconcile', label, 'execution-control', handler, f"Result reconciled status={payload.get('status')} dispatch_state={payload.get('dispatch_state')} acceptance={payload.get('institutional_acceptance_state')}.", read=[str(result_path)], written=[payload.get('reconciliation_path') or f'runtime/execution_adapters/reconciliation/{dispatch_id}.json', payload.get('report_path') or f'runtime/execution_adapters/reports/{dispatch_id}_reconciliation.md'], state=['result reconciliation updated dispatch evidence'])

def execution_result_report(root=None, dispatch_id: str | None = None, **params: Any) -> OfficeActionResult:
    label='Generate/open reconciliation report'; handler='estate.core.execution_result_reconciliation_runtime.format_reconciliation_report'
    if blocked := _require('execution_result.report', label, handler, {'dispatch_id':dispatch_id}, ['dispatch_id']): return blocked
    base=_root(root); rec_path=base/'runtime/execution_adapters/reconciliation'/f'{dispatch_id}.json'
    if not rec_path.exists(): return _blocked('execution_result.report', label, 'execution-control', handler, 'No reconciliation artifact exists for this dispatch.', read=[_rel(base, rec_path)])
    payload=json.loads(rec_path.read_text(encoding='utf-8')); report=base/'runtime/execution_adapters/reports'/f'{dispatch_id}_reconciliation.md'; report.parent.mkdir(parents=True, exist_ok=True); report.write_text(format_reconciliation_report(payload)+'\n', encoding='utf-8')
    return _completed('execution_result.report', label, 'execution-control', handler, f"Reconciliation report generated for {dispatch_id}.", read=[_rel(base, rec_path)], written=[_rel(base, report)])

def generate_daily_briefing(root=None, **_: Any) -> OfficeActionResult:
    base = _root(root); generate_daily_board_integration(root=base, write=True); generate_morning_briefing(root=base, write=True)
    return _completed('daily_board.generate_morning_briefing', 'Generate morning briefing', 'daily-board', 'estate.core.daily_board_integration.generate_daily_board_integration + estate.core.morning_briefing.generate_morning_briefing', 'Daily Board integration and morning briefing generated locally.', written=['runtime/operations/daily_board_integration.json', 'operations/boards/daily_board_integration.md', 'runtime/briefings/morning_briefing.json', 'operations/briefings/morning_briefing.md'], state=['daily board and briefing artifacts refreshed'])

HANDLERS: dict[str, Callable[..., OfficeActionResult]] = {f.__name__: f for f in []}
HANDLERS.update({
 'ai_services.refresh_local_inventory': refresh_ai_services,
 'validation.run_production_readiness': run_production_readiness,
 'work_packages.validate_selected': validate_selected_work_package,
 'work_packages.refresh_assignment_queue': refresh_work_package_queue,
 'notifications.refresh_center': refresh_notifications,
 'notifications.local_acknowledge': local_ack_notification,
 'alfred.request_briefing': request_alfred_briefing,
 'mission_control.refresh_payload': refresh_mission_control,
 'daily_board.generate_morning_briefing': generate_daily_briefing,
 'orchestrator_intake.record_decision': record_orchestrator_intake_decision,
 'operations_control.record_decision': record_operations_control_decision,
 'execution_session.preview': execution_session_preview,
 'execution_session.start': execution_session_start,
 'execution_session.resume': execution_session_resume,
 'execution_session.status': execution_session_status,
 'execution_session.report': execution_session_report,
 'execution_attempt.cancel_request': execution_attempt_cancel_request,
 'execution_attempt.inspect_recovery': execution_attempt_inspect_recovery,
 'execution_attempt.retry_eligibility': execution_attempt_retry_eligibility,
 'execution_attempt.release_stale': execution_attempt_release_stale,
 'execution_result.inspect_reconciliation': execution_result_inspect_reconciliation,
 'execution_result.reconcile': execution_result_reconcile,
 'execution_result.report': execution_result_report,
 'settings.load_current': settings_load_current,
 'settings.save_apply': settings_save_apply,
 'settings.reset_defaults': settings_reset_defaults,
 'settings.export': settings_export,
 'settings.import': settings_import,
})

ACTION_CONTROLS = [
 {'action_id':'execution_session.preview','label':'Preview execution session','target_tab':'execution-control','handler':'execution_session_preview','availability':'available','requires_input':'dispatch_id,authorization_path','note':'No provider call; writes preview/session evidence.'},
 {'action_id':'execution_session.start','label':'Start execution session','target_tab':'execution-control','handler':'execution_session_start','availability':'available','requires_input':'dispatch_id,authorization_path,confirm_live_execution','note':'Requires explicit confirmation and existing authorization evidence.'},
 {'action_id':'execution_session.resume','label':'Resume execution session','target_tab':'execution-control','handler':'execution_session_resume','availability':'available','requires_input':'session_id','note':'Preserves duplicate-provider-call protection.'},
 {'action_id':'execution_session.status','label':'Refresh execution-session status','target_tab':'execution-control','handler':'execution_session_status','availability':'available','requires_input':'session_id'},
 {'action_id':'execution_session.report','label':'Generate/open execution-session report','target_tab':'execution-control','handler':'execution_session_report','availability':'available','requires_input':'session_id'},
 {'action_id':'execution_attempt.cancel_request','label':'Request cancellation','target_tab':'execution-control','handler':'execution_attempt_cancel_request','availability':'available','requires_input':'dispatch_id,attempt_id,actor,reason','note':'Records request; does not claim provider stopped.'},
 {'action_id':'execution_attempt.inspect_recovery','label':'Inspect recovery state','target_tab':'execution-control','handler':'execution_attempt_inspect_recovery','availability':'available','requires_input':'dispatch_id'},
 {'action_id':'execution_attempt.retry_eligibility','label':'Inspect retry eligibility','target_tab':'execution-control','handler':'execution_attempt_retry_eligibility','availability':'available','requires_input':'dispatch_id','note':'Does not authorize or start a retry.'},
 {'action_id':'execution_attempt.release_stale','label':'Release stale lease','target_tab':'execution-control','handler':'execution_attempt_release_stale','availability':'available','requires_input':'dispatch_id,attempt_id,reason,confirm_stale_release','note':'Requires explicit confirmation and stale-safe evidence.'},
 {'action_id':'execution_result.inspect_reconciliation','label':'Inspect execution result reconciliation','target_tab':'execution-control','handler':'execution_result_inspect_reconciliation','availability':'available','requires_input':'dispatch_id'},
 {'action_id':'execution_result.reconcile','label':'Reconcile execution result','target_tab':'execution-control','handler':'execution_result_reconcile','availability':'available','requires_input':'dispatch_id,result_path','note':'Idempotent; never grants institutional acceptance.'},
 {'action_id':'execution_result.report','label':'Generate/open reconciliation report','target_tab':'execution-control','handler':'execution_result_report','availability':'available','requires_input':'dispatch_id'},
 {'action_id':'settings.load_current','label':'Load current settings','target_tab':'settings','handler':'settings_load_current','availability':'available'},
 {'action_id':'settings.save_apply','label':'Save and apply settings','target_tab':'settings','handler':'settings_save_apply','availability':'available','requires_input':'settings_json','note':'Persists atomically and reloads Office payload.'},
 {'action_id':'settings.reset_defaults','label':'Reset to defaults','target_tab':'settings','handler':'settings_reset_defaults','availability':'available'},
 {'action_id':'settings.export','label':'Export settings','target_tab':'settings','handler':'settings_export','availability':'available'},
 {'action_id':'settings.import','label':'Import settings','target_tab':'settings','handler':'settings_import','availability':'available','requires_input':'settings_json'},
 {'action_id':'ai_services.refresh_local_inventory','label':'Refresh local AI service inventory','target_tab':'ai-services-models','handler':'refresh_ai_services','availability':'available'},
 {'action_id':'validation.run_production_readiness','label':'Run production readiness refresh','target_tab':'validation','handler':'run_production_readiness','availability':'available','note':'Evidence is not institutional acceptance.'},
 {'action_id':'work_packages.refresh_assignment_queue','label':'Refresh assignment queue','target_tab':'work-packages','handler':'refresh_work_package_queue','availability':'available'},
 {'action_id':'work_packages.validate_selected','label':'Validate selected work package','target_tab':'work-packages','handler':'validate_selected_work_package','availability':'available','requires_input':'work_package_id'},
 {'action_id':'notifications.refresh_center','label':'Refresh notification center','target_tab':'notifications','handler':'refresh_notifications','availability':'available'},
 {'action_id':'notifications.local_acknowledge','label':'Acknowledge notification locally','target_tab':'notifications','handler':'local_ack_notification','availability':'available','requires_input':'notification_id','note':'Local state only; authoritative closure is unchanged.'},
 {'action_id':'alfred.request_briefing','label':'Request Alfred briefing','target_tab':'alfred','handler':'request_alfred_briefing','availability':'available'},
 {'action_id':'mission_control.refresh_payload','label':'Refresh Mission Control payload','target_tab':'mission-control','handler':'refresh_mission_control','availability':'available'},
 {'action_id':'daily_board.generate_morning_briefing','label':'Generate morning briefing','target_tab':'daily-board','handler':'generate_daily_briefing','availability':'available'},
 {'action_id':'orchestrator_intake.record_decision','label':'Record Orchestrator intake decision','target_tab':'operational-activity','handler':'record_orchestrator_intake_decision','availability':'available','requires_input':'intake_id,decision,decided_by','note':'Records a durable decision artifact; does not schedule or execute work.'},
 {'action_id':'operations_control.record_decision','label':'Record operations-control decision','target_tab':'operational-activity','handler':'record_operations_control_decision','availability':'available','requires_input':'decision_type,target_type,decided_by','note':'Writes an operations-control decision artifact; does not execute providers.'},
 {'action_id':'operations_control.run_provider','label':'Run provider','target_tab':'operational-activity','availability':'gated','disabled_reason':'Provider execution is intentionally outside the Office traffic-controller panel.'},
 {'action_id':'ai_services.start_stop_load','label':'Start/stop/load AI service','target_tab':'ai-services-models','availability':'gated','disabled_reason':'Process-control approval workflow is not implemented for Office controls; use existing governed service approval path first.'},
]

def controls_for_tab(tab: str) -> list[dict[str, Any]]:
    return [dict(c) for c in ACTION_CONTROLS if c['target_tab'] == tab]

def execute_office_action(action_id: str, *, root=None, **params: Any) -> dict[str, Any]:
    base = _root(root)
    control = next((c for c in ACTION_CONTROLS if c['action_id'] == action_id), None)
    if not control:
        result = _blocked(action_id, action_id, 'unknown', 'office_command_surface.execute_office_action', f'No Office action is registered for {action_id}.')
        return _write_result(base, result).to_dict()
    if control.get('availability') != 'available':
        result = _blocked(action_id, control['label'], control['target_tab'], control.get('handler', 'gated_control'), control.get('disabled_reason') or 'Action is gated.')
        return _write_result(base, result).to_dict()
    try:
        result = HANDLERS[action_id](root=base, **params)
    except Exception as exc:
        diag = _diagnostic(base, action_id, exc)
        result = OfficeActionResult(action_id, control['label'], control['target_tab'], 'failed', f'Action attempted and failed: {type(exc).__name__}: {exc}', control.get('handler') or action_id, diagnostics_path=diag)
    return _write_result(base, result).to_dict()
