"""Real local Office command surface actions for WP-0213."""
from __future__ import annotations

import json
import traceback
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from estate.core.paths import ESTATE_ROOT
from estate.core.service_status_board import generate_service_status_board
from estate.core.provider_sync import sync_ollama_providers
from estate.core.production_readiness_validation import generate_production_readiness_report
from estate.core.work_package_validation import validate_work_package
from estate.core.assignment_queue import generate_assignment_queue, find_work_package, update_work_package_control
from estate.core.mailbox_index import generate_mailbox_index
from estate.ai_services.discovery import rediscover as ai_services_rediscover
from estate.ai_services.control import request as ai_services_request, status as ai_services_status
from estate.ai_services.execution import load_state as ai_services_load_state
from estate.core.operations_notification_center import generate_operations_notification_center, acknowledge_operations_notification
from estate.core.alfred_duty import run_alfred_duty
from estate.core.daily_board_integration import generate_daily_board_integration
from estate.core.mission_control_workspace import build_mission_control_workspace
from estate.core.morning_briefing import generate_morning_briefing
from estate.core.orchestrator_intake_decisions import OrchestratorIntakeDecisionRuntime
from estate.core.operations_control_runtime import OperationsControlRuntime
from estate.core.operations_runtime_service import OperationsRuntimeService
from estate.core.operations_runtime_host import OperationsRuntimeHost
from estate.core.operations_scheduler_runtime import OperationsSchedulerRuntime
from estate.core.operational_watch_runtime import OperationalWatchRuntime
from estate.core.merge_discovery_runtime import MergeDiscoveryRuntime
from estate.core.operations_manager import OperationsDecision
from estate.core.execution_session_controller import ExecutionSessionController
from estate.core.execution_attempt_runtime import ExecutionAttemptRuntime
from estate.core.execution_result_reconciliation_runtime import inspect_reconciliation, reconcile_result, format_reconciliation_report
from estate.core.operations_center_settings import save_settings_document, reset_operations_center_settings, export_operations_center_settings, import_operations_center_settings, SETTINGS_OUTPUT
from estate.core.office_parking_lot_controls import parking_action, roadmap_action, planning_undo, filter_items
from estate.core.office_personnel_directory import refresh_personnel_directory, open_employee_detail, route_personnel_mailbox, route_personnel_conversation
from estate.core.office_validation_actions import inspect_validation_control_center, request_validation, acknowledge_failure, automatic_validator_status, open_artifact as open_validation_artifact, governed_retry
from estate.core.office_mailbox_control import refresh_mailbox_control_center, open_message_detail, mark_message_read_state, route_message, local_attention_acknowledge, inspect_delivery_failures
from estate.core.collaboration_messages import acknowledge_message, create_reply
from estate.core.office_personnel_directory import open_employee_detail as mailbox_open_employee_detail

VALID_OUTCOMES = {"completed", "queued", "blocked", "failed"}
RESULT_LOG = "runtime/steward/office_command_surface_action_results.jsonl"

@dataclass
class OfficeActionResult:
    action_id: str
    action_label: str
    request_id: str
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


def _request_id(params: dict[str, Any] | None = None) -> str:
    value = (params or {}).get('request_id')
    return str(value) if value else f'office-{uuid.uuid4().hex[:12]}'

def _completed(action_id, label, tab, handler, msg, *, read=(), written=(), state=(), request_id: str | None = None):
    return OfficeActionResult(action_id, label, request_id or _request_id(), tab, 'completed', msg, handler, list(read), list(written), list(state))

def _blocked(action_id, label, tab, handler, reason, *, read=(), request_id: str | None = None):
    return OfficeActionResult(action_id, label, request_id or _request_id(), tab, 'blocked', reason, handler, list(read), [], [], 'gated_or_missing_requirement')


def refresh_ai_services(root=None, **_: Any) -> OfficeActionResult:
    base = _root(root)
    registry = ai_services_rediscover(base, actor='office')
    board = generate_service_status_board(root=base, write=True)
    msg = f"AI services rediscovered {registry.get('service_count', 0)} approved service(s); service board has {len(board.get('services') or [])} service rows."
    return _completed('ai_services.refresh_local_inventory', 'Refresh local AI service inventory', 'ai-services-models', 'estate.ai_services.discovery.rediscover + estate.core.service_status_board.generate_service_status_board', msg, read=['runtime/ai_services/implementations', 'data/registry/providers.json', 'data/registry/services.json'], written=['runtime/ai_services/registry.json', 'runtime/ai_services/state.json', 'runtime/ai_services/audit_log.jsonl', 'runtime/services/service_status_board.json', 'operations/services/service_status_board.md'], state=['AI service registry refreshed'])

def _ai_service_action(action_id: str, label: str, operation: str, root=None, service_id: str | None = None, model: str | None = None, approved_by: str | None = 'steward', dry_run: bool | str = False, **params: Any) -> OfficeActionResult:
    if not service_id:
        return _blocked(action_id, label, 'ai-services-models', 'estate.ai_services.control.request', 'service_id is required.', request_id=params.get('request_id'))
    dry = str(dry_run).lower() == 'true' if isinstance(dry_run, str) else bool(dry_run)
    payload = ai_services_request(operation, service_id, actor='office', approved_by=approved_by, root=_root(root), dry_run=dry, model=model, reason=params.get('reason'), runner=params.get('runner'), health_checker=params.get('health_checker'), health_timeout_seconds=float(params.get('health_timeout_seconds', 1)), health_interval_seconds=float(params.get('health_interval_seconds', 0.1)))
    outcome = 'completed' if payload.get('result') in {'planned', 'executed'} else 'blocked' if payload.get('result') in {'requires_approval', 'failed'} else 'failed'
    msg = f"AI service {operation} for {service_id} returned {payload.get('result')} / {payload.get('approval_state')}."
    result = OfficeActionResult(action_id, label, params.get('request_id') or _request_id(), 'ai-services-models', outcome, msg, 'estate.ai_services.control.request', ['runtime/ai_services/registry.json', 'runtime/ai_services/state.json'], ['runtime/ai_services/state.json', 'runtime/ai_services/approvals.json', 'runtime/ai_services/audit_log.jsonl'], [f'ai service {operation} {payload.get("result")}'])
    if outcome == 'blocked':
        result.authority_gating_status = 'gated_or_missing_requirement'
    return result

def ai_service_start(root=None, **params: Any) -> OfficeActionResult:
    return _ai_service_action('ai_services.start', 'Start AI service', 'start', root=root, **params)

def ai_service_stop(root=None, **params: Any) -> OfficeActionResult:
    return _ai_service_action('ai_services.stop', 'Stop AI service', 'stop', root=root, **params)

def ai_service_restart(root=None, service_id: str | None = None, **params: Any) -> OfficeActionResult:
    if not service_id:
        return _blocked('ai_services.restart', 'Restart AI service', 'ai-services-models', 'estate.ai_services.control.request', 'service_id is required.', request_id=params.get('request_id'))
    stop = ai_services_request('stop', service_id, actor='office', approved_by=params.get('approved_by') or 'steward', root=_root(root), dry_run=False, runner=params.get('runner'))
    start = ai_services_request('start', service_id, actor='office', approved_by=params.get('approved_by') or 'steward', root=_root(root), dry_run=False, runner=params.get('runner'), health_checker=params.get('health_checker'), health_timeout_seconds=float(params.get('health_timeout_seconds', 1)), health_interval_seconds=float(params.get('health_interval_seconds', 0.1)))
    outcome = 'completed' if start.get('result') in {'executed', 'planned'} else 'blocked'
    return OfficeActionResult('ai_services.restart', 'Restart AI service', params.get('request_id') or _request_id(), 'ai-services-models', outcome, f"Stop returned {stop.get('result')}; start returned {start.get('result')}.", 'estate.ai_services.control.request', ['runtime/ai_services/registry.json', 'runtime/ai_services/state.json'], ['runtime/ai_services/state.json', 'runtime/ai_services/audit_log.jsonl'], ['AI service restart attempted through canonical control plane'])

def ai_model_load(root=None, **params: Any) -> OfficeActionResult:
    return _ai_service_action('ai_services.load_model', 'Load supported model', 'load_model', root=root, **params)

def ai_model_unload(root=None, **params: Any) -> OfficeActionResult:
    return _ai_service_action('ai_services.unload_model', 'Unload supported model', 'unload_model', root=root, **params)

def ai_service_inspect(root=None, service_id: str | None = None, **params: Any) -> OfficeActionResult:
    st = ai_services_status(_root(root))
    services = st.get('registry', {}).get('services', [])
    if service_id and not any(s.get('service_id') == service_id for s in services):
        return _blocked('ai_services.inspect_state', 'Inspect service logs/readiness/provider state', 'ai-services-models', 'estate.ai_services.control.status', f'Unknown service: {service_id}.', request_id=params.get('request_id'))
    rel='runtime/ai_services/last_inspection.json'; path=_root(root)/rel; path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(st, indent=2, sort_keys=True)+'\n', encoding='utf-8')
    return _completed('ai_services.inspect_state', 'Inspect service logs/readiness/provider state', 'ai-services-models', 'estate.ai_services.control.status', f"Inspection captured {len(services)} service(s).", read=['runtime/ai_services/registry.json','runtime/ai_services/state.json','runtime/ai_services/audit_log.jsonl'], written=[rel], state=['AI service inspection evidence refreshed'], request_id=params.get('request_id'))

def ai_service_launch_interface(root=None, service_id: str | None = None, **params: Any) -> OfficeActionResult:
    st = ai_services_status(_root(root)); svc = next((s for s in st.get('registry', {}).get('services', []) if s.get('service_id') == service_id), None)
    if not svc:
        return _blocked('ai_services.launch_local_interface', 'Launch approved local interface route', 'ai-services-models', 'estate.ai_services.control.status', 'service_id must identify a registered local interface such as open_webui.', request_id=params.get('request_id'))
    endpoint = svc.get('default_endpoint')
    if not endpoint or not str(endpoint).startswith(('http://127.0.0.1', 'http://localhost', 'http://[::1]')):
        return _blocked('ai_services.launch_local_interface', 'Launch approved local interface route', 'ai-services-models', 'estate.ai_services.control.status', f'Interface endpoint is not approved loopback: {endpoint}.', request_id=params.get('request_id'))
    rel='runtime/ai_services/local_interface_routes.jsonl'; path=_root(root)/rel; path.parent.mkdir(parents=True, exist_ok=True); path.open('a', encoding='utf-8').write(json.dumps({'service_id':service_id,'endpoint':endpoint,'timestamp':datetime.now(timezone.utc).isoformat(timespec='seconds'),'request_id':params.get('request_id') or _request_id()}, sort_keys=True)+'\n')
    return _completed('ai_services.launch_local_interface', 'Launch approved local interface route', 'ai-services-models', 'estate.ai_services.control.status', f'Approved local interface route prepared for {service_id}: {endpoint}.', read=['runtime/ai_services/registry.json'], written=[rel], state=['local interface route evidence recorded'], request_id=params.get('request_id'))

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

def assign_work_package(root=None, work_package_id: str | None = None, owner: str | None = None, actor: str = "Office", reason: str = "Office assignment update", **params: Any) -> OfficeActionResult:
    if not work_package_id or not owner:
        return _blocked('work_packages.assign', 'Assign/reassign work package', 'work-packages', 'estate.core.assignment_queue.update_work_package_control', 'work_package_id and owner are required.', request_id=params.get('request_id'))
    base = _root(root)
    payload = update_work_package_control(work_package_id, root=base, owner=owner, actor=actor, reason=reason)
    wp = payload.get('work_package') or {}
    return _completed('work_packages.assign', 'Assign/reassign work package', 'work-packages', 'estate.core.assignment_queue.update_work_package_control', f"Assignment persisted for {work_package_id}: owner={wp.get('owner')}.", read=['collaboration/work_packages', 'runtime/work_packages/control_state.json'], written=['runtime/work_packages/control_state.json', 'runtime/work_packages/control_events.jsonl', 'runtime/work_packages/assignment_queue.json', 'operations/work_packages/assignment_queue.md'], state=['work package assignment persisted', 'Office payload refreshed'], request_id=params.get('request_id'))

def update_work_package_state(root=None, work_package_id: str | None = None, state: str | None = None, priority: str | None = None, actor: str = "Office", reason: str = "Office state update", **params: Any) -> OfficeActionResult:
    if not work_package_id or not (state or priority):
        return _blocked('work_packages.update_state', 'Change work package status/priority', 'work-packages', 'estate.core.assignment_queue.update_work_package_control', 'work_package_id plus state or priority are required.', request_id=params.get('request_id'))
    base = _root(root)
    payload = update_work_package_control(work_package_id, root=base, state=state, priority=priority, actor=actor, reason=reason)
    wp = payload.get('work_package') or {}
    return _completed('work_packages.update_state', 'Change work package status/priority', 'work-packages', 'estate.core.assignment_queue.update_work_package_control', f"Status/priority persisted for {work_package_id}: state={wp.get('state')} priority={wp.get('priority')}.", read=['collaboration/work_packages', 'runtime/work_packages/control_state.json'], written=['runtime/work_packages/control_state.json', 'runtime/work_packages/control_events.jsonl', 'runtime/work_packages/assignment_queue.json', 'operations/work_packages/assignment_queue.md'], state=['work package status or priority persisted', 'Office payload refreshed'], request_id=params.get('request_id'))

def promote_work_package(root=None, work_package_id: str | None = None, actor: str = "Office", reason: str = "Office canonical promotion", **params: Any) -> OfficeActionResult:
    if not work_package_id:
        return _blocked('work_packages.promote', 'Promote work package', 'work-packages', 'estate.core.assignment_queue.update_work_package_control', 'work_package_id is required.', request_id=params.get('request_id'))
    base = _root(root)
    payload = update_work_package_control(work_package_id, root=base, promote=True, actor=actor, reason=reason)
    wp = payload.get('work_package') or {}
    return _completed('work_packages.promote', 'Promote work package', 'work-packages', 'estate.core.assignment_queue.update_work_package_control', f"{work_package_id} promoted to canonical workflow state {wp.get('state')}.", read=['collaboration/work_packages', 'runtime/work_packages/control_state.json'], written=['runtime/work_packages/control_state.json', 'runtime/work_packages/control_events.jsonl', 'runtime/work_packages/assignment_queue.json', 'operations/work_packages/assignment_queue.md'], state=['work package canonical workflow state advanced', 'Office payload refreshed'], request_id=params.get('request_id'))

def open_work_package_artifact(root=None, work_package_id: str | None = None, artifact_kind: str = "source", **params: Any) -> OfficeActionResult:
    if not work_package_id:
        return _blocked('work_packages.open_artifact', 'Open work-package artifact/evidence', 'work-packages', 'estate.core.assignment_queue.generate_assignment_queue', 'work_package_id is required.', request_id=params.get('request_id'))
    base = _root(root)
    queue = generate_assignment_queue(root=base, write=False)
    wp = find_work_package(queue, work_package_id)
    if not wp:
        return _blocked('work_packages.open_artifact', 'Open work-package artifact/evidence', 'work-packages', 'estate.core.assignment_queue.generate_assignment_queue', f'Unknown work package: {work_package_id}.', request_id=params.get('request_id'))
    evidence = wp.get('evidence') or {}
    rel = evidence.get(artifact_kind) or (wp.get('related_references') or {}).get(artifact_kind)
    if not rel:
        return _blocked('work_packages.open_artifact', 'Open work-package artifact/evidence', 'work-packages', 'estate.core.assignment_queue.generate_assignment_queue', f'No {artifact_kind} reference is recorded for {work_package_id}.', request_id=params.get('request_id'))
    if not (base / rel).exists():
        return _blocked('work_packages.open_artifact', 'Open work-package artifact/evidence', 'work-packages', 'estate.core.assignment_queue.generate_assignment_queue', f'{artifact_kind} reference is recorded but not available: {rel}.', read=[rel], request_id=params.get('request_id'))
    return _completed('work_packages.open_artifact', 'Open work-package artifact/evidence', 'work-packages', 'estate.core.assignment_queue.generate_assignment_queue', f"{artifact_kind} available for {work_package_id}: {rel}.", read=[rel], state=['work package evidence route verified'], request_id=params.get('request_id'))

def filter_work_packages(root=None, query: str = '', state: str = '', priority: str = '', owner: str = '', **params: Any) -> OfficeActionResult:
    base = _root(root)
    queue = generate_assignment_queue(root=base, write=False)
    rows = queue.get('work_packages') or []
    def match(wp):
        hay = ' '.join(str(wp.get(k, '')) for k in ['work_package_id', 'title', 'owner', 'state', 'priority', 'next_action']).lower()
        return (not query or query.lower() in hay) and (not state or wp.get('state') == state) and (not priority or wp.get('priority') == priority) and (not owner or owner.lower() in str(wp.get('owner','')).lower())
    matches = [wp['work_package_id'] for wp in rows if match(wp)]
    rel = 'runtime/work_packages/last_filter_result.json'
    (base / rel).parent.mkdir(parents=True, exist_ok=True)
    (base / rel).write_text(json.dumps({'query': query, 'state': state, 'priority': priority, 'owner': owner, 'matches': matches}, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    return _completed('work_packages.filter', 'Filter/search/sort work packages', 'work-packages', 'estate.core.assignment_queue.generate_assignment_queue', f"Filter completed with {len(matches)} match(es): {', '.join(matches[:10])}.", read=['runtime/work_packages/assignment_queue.json', 'collaboration/work_packages'], written=[rel], state=['work package filtered result recorded'], request_id=params.get('request_id'))

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




def refresh_operational_activity(root=None, **params: Any) -> OfficeActionResult:
    base = _root(root)
    from estate.core.office_operational_activity import load_office_operational_activity
    payload = load_office_operational_activity(base)
    rel = 'runtime/operations/status/office_operational_activity_payload.json'
    path = base / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    return _completed('operational_activity.refresh', 'Refresh operational activity', 'operational-activity', 'estate.core.office_operational_activity.load_office_operational_activity', f"Operational activity refreshed with {(payload.get('summary') or {}).get('activity_count', 0)} item(s).", read=payload.get('expected_status_artifact_paths') or [], written=[rel], state=['operational activity payload refreshed'], request_id=params.get('request_id'))

def acknowledge_operational_activity(root=None, activity_id: str | None = None, acknowledged_by: str | None = None, reason: str | None = None, **params: Any) -> OfficeActionResult:
    if not activity_id or not acknowledged_by:
        return _blocked('operational_activity.acknowledge_attention', 'Acknowledge attention item', 'operational-activity', 'office_command_surface.acknowledge_operational_activity', 'activity_id and acknowledged_by are required.', request_id=params.get('request_id'))
    base=_root(root); rel='runtime/operations/status/attention_acknowledgements.json'; path=base/rel; path.parent.mkdir(parents=True, exist_ok=True)
    data=[]
    if path.exists():
        try: data=json.loads(path.read_text(encoding='utf-8'))
        except Exception: data=[]
    rec={'activity_id':activity_id,'acknowledged_by':acknowledged_by,'reason':reason or 'Office attention acknowledgement','timestamp':datetime.now(timezone.utc).isoformat(timespec='seconds'),'request_id':params.get('request_id') or _request_id()}
    data.append(rec); path.write_text(json.dumps(data, indent=2, sort_keys=True)+'\n', encoding='utf-8')
    refresh_operational_activity(base)
    return _completed('operational_activity.acknowledge_attention', 'Acknowledge attention item', 'operational-activity', 'office_command_surface.acknowledge_operational_activity', f"Attention item {activity_id} acknowledged locally by {acknowledged_by}.", read=['runtime/operations/status/active.json','runtime/operations/status/recent.json'], written=[rel,'runtime/operations/status/office_operational_activity_payload.json'], state=['attention acknowledgement evidence recorded'], request_id=rec['request_id'])

def route_operational_activity(root=None, activity_id: str | None = None, route_target: str | None = None, **params: Any) -> OfficeActionResult:
    if not activity_id:
        return _blocked('operational_activity.route_to_workspace', 'Route to controlling workspace', 'operational-activity', 'office_command_surface.route_operational_activity', 'activity_id is required.', request_id=params.get('request_id'))
    target = route_target or ('work-packages' if str(activity_id).startswith('WP-') else 'execution-control')
    rel='runtime/operations/status/activity_routes.jsonl'; base=_root(root); path=base/rel; path.parent.mkdir(parents=True, exist_ok=True)
    path.open('a',encoding='utf-8').write(json.dumps({'activity_id':activity_id,'target_tab':target,'timestamp':datetime.now(timezone.utc).isoformat(timespec='seconds'),'request_id':params.get('request_id') or _request_id()}, sort_keys=True)+'\n')
    return _completed('operational_activity.route_to_workspace', 'Route to controlling workspace', target, 'office_command_surface.route_operational_activity', f"Route prepared for {activity_id} to {target}.", written=[rel], state=['workspace route evidence recorded'], request_id=params.get('request_id'))

def open_operational_artifact(root=None, artifact_path: str | None = None, **params: Any) -> OfficeActionResult:
    if not artifact_path:
        return _blocked('operational_activity.open_artifact', 'Open related evidence/artifact', 'operational-activity', 'office_command_surface.open_operational_artifact', 'artifact_path is required.', request_id=params.get('request_id'))
    base=_root(root); path=(base/artifact_path).resolve()
    try: path.relative_to(base.resolve())
    except ValueError:
        return _blocked('operational_activity.open_artifact', 'Open related evidence/artifact', 'operational-activity', 'office_command_surface.open_operational_artifact', 'artifact_path must stay inside the Estate root.', request_id=params.get('request_id'))
    if not path.exists():
        return _blocked('operational_activity.open_artifact', 'Open related evidence/artifact', 'operational-activity', 'office_command_surface.open_operational_artifact', f'Artifact is not available: {artifact_path}.', read=[artifact_path], request_id=params.get('request_id'))
    return _completed('operational_activity.open_artifact', 'Open related evidence/artifact', 'operational-activity', 'office_command_surface.open_operational_artifact', f"Artifact available for opening: {artifact_path}.", read=[artifact_path], state=['artifact availability verified'], request_id=params.get('request_id'))

def filter_operational_activity(root=None, state: str = '', owner: str = '', priority: str = '', attention_required: str = '', **params: Any) -> OfficeActionResult:
    base=_root(root); rel='runtime/operations/status/activity_filter.json'; payload={'state':state,'owner':owner,'priority':priority,'attention_required':attention_required,'timestamp':datetime.now(timezone.utc).isoformat(timespec='seconds')}
    path=base/rel; path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(payload, indent=2, sort_keys=True)+'\n', encoding='utf-8')
    return _completed('operational_activity.filter', 'Filter operational activity', 'operational-activity', 'office_command_surface.filter_operational_activity', 'Operational activity filter persisted for the local Office render.', written=[rel], state=['operational activity filter state changed'], request_id=params.get('request_id'))


def validation_refresh_center(root=None, **params: Any) -> OfficeActionResult:
    base = _root(root); payload = inspect_validation_control_center(base, **{k: v for k, v in params.items() if k in {'result','package','date_from','date_to','owner','attention_state'}})
    return _completed('validation.refresh_center', 'Refresh validation/audit control center', 'validation', 'estate.core.office_validation_actions.inspect_validation_control_center', f"Validation/audit center refreshed with {(payload.get('summary') or {}).get('row_count', 0)} row(s). Evidence is not institutional acceptance.", written=['runtime/validation/office_validation_control_center.json'], state=['validation Office payload refreshed'], request_id=params.get('request_id'))

def validation_request(root=None, work_package_id: str | None = None, revalidate: Any = None, **params: Any) -> OfficeActionResult:
    if not work_package_id:
        return _blocked('validation.request', 'Request validation/revalidation', 'validation', 'estate.core.office_validation_actions.request_validation', 'work_package_id is required.', request_id=params.get('request_id'))
    base = _root(root); payload = request_validation(base, work_package_id, revalidate=_truthy(revalidate))
    return _completed('validation.request', 'Request validation/revalidation', 'validation', 'estate.core.work_package_validation.validate_work_package', f"Validation {'re' if _truthy(revalidate) else ''}run for {work_package_id} produced status {payload.get('validation_status')}; institutional acceptance not granted.", written=[f"runtime/validation/work_packages/{payload.get('validation_id')}.json", f"operations/validation/work_packages/{payload.get('validation_id')}.md", 'runtime/validation/office_validation_control_center.json'], state=['validation evidence generated'], request_id=params.get('request_id'))

def validation_acknowledge_failure(root=None, artifact_id: str | None = None, acknowledged_by: str | None = None, reason: str | None = None, **params: Any) -> OfficeActionResult:
    if not artifact_id or not acknowledged_by:
        return _blocked('validation.acknowledge_failure', 'Acknowledge validation failure', 'validation', 'estate.core.office_validation_actions.acknowledge_failure', 'artifact_id and acknowledged_by are required.', request_id=params.get('request_id'))
    base = _root(root); acknowledge_failure(base, artifact_id, acknowledged_by, reason)
    return _completed('validation.acknowledge_failure', 'Acknowledge validation failure', 'validation', 'estate.core.office_validation_actions.acknowledge_failure', f"Failure attention for {artifact_id} acknowledged locally; evidence remains unchanged.", written=['runtime/validation/failure_acknowledgements.jsonl','runtime/validation/office_validation_control_center.json'], state=['failure acknowledgement recorded'], request_id=params.get('request_id'))

def validation_auto_status(root=None, **params: Any) -> OfficeActionResult:
    payload = automatic_validator_status(_root(root))
    return _completed('validation.automatic_validator_status', 'Inspect automatic-validator status', 'validation', 'estate.core.office_validation_actions.automatic_validator_status', f"Automatic validator available={payload.get('available')} pending={payload.get('pending')} latest_verdict={payload.get('latest_verdict')}.", read=['runtime/post_merge_audit/status/latest.json','runtime/post_merge_audit/status/summary.json'], state=['automatic validator status inspected'], request_id=params.get('request_id'))

def validation_open_artifact(root=None, artifact_path: str | None = None, **params: Any) -> OfficeActionResult:
    if not artifact_path:
        return _blocked('validation.open_artifact', 'Open validation/audit/verdict artifact', 'validation', 'estate.core.office_validation_actions.open_artifact', 'artifact_path is required.', request_id=params.get('request_id'))
    payload = open_validation_artifact(_root(root), artifact_path)
    if payload.get('outcome') != 'completed':
        return _blocked('validation.open_artifact', 'Open validation/audit/verdict artifact', 'validation', 'estate.core.office_validation_actions.open_artifact', payload.get('message'), read=[artifact_path], request_id=params.get('request_id'))
    return _completed('validation.open_artifact', 'Open validation/audit/verdict artifact', 'validation', 'estate.core.office_validation_actions.open_artifact', payload.get('message'), read=[artifact_path], state=['artifact route verified'], request_id=params.get('request_id'))

def validation_governed_retry(root=None, max_count: Any = 1, **params: Any) -> OfficeActionResult:
    base = _root(root); payload = governed_retry(base, max_count=int(max_count or 1)); processed = payload.get('processed_count', 0)
    return _completed('validation.governed_retry', 'Run governed audit retry', 'validation', 'estate.core.post_merge_audit_processor.PostMergeAuditProcessor.process_all', f"Governed retry processed {processed} request(s); institutional acceptance not granted.", read=['runtime/post_merge_audit/requests'], written=['runtime/post_merge_audit/status/latest.json','runtime/post_merge_audit/status/summary.json'], state=['existing audit processor queue advanced'], request_id=params.get('request_id'))

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
        return OfficeActionResult('settings.save_apply', 'Save and apply settings', _request_id(params), 'settings', 'failed', f'Settings were not saved: {exc}', 'estate.core.operations_center_settings.save_settings_document')
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
        return OfficeActionResult('settings.import', 'Import settings', _request_id(), 'settings', 'failed', f'Import rejected without changing active settings: {exc}', 'estate.core.operations_center_settings.import_operations_center_settings')
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
    return OfficeActionResult('execution_session.preview', label, _request_id(params), 'execution-control', outcome, f"Preview session {payload.get('execution_session_id')} state={payload.get('state')} readiness={'ready' if not payload.get('blocking_reasons') else 'blocked'} reasons={payload.get('blocking_reasons') or []}.", handler, read, written, ['execution session preview artifact written'], 'governed_preview_no_provider_call')

def execution_session_start(root=None, dispatch_id: str | None = None, authorization_path: str | None = None, confirm_live_execution: Any = None, **params: Any) -> OfficeActionResult:
    label='Start execution session'; handler='estate.core.execution_session_controller.ExecutionSessionController.start'; data={'dispatch_id':dispatch_id,'authorization_path':authorization_path}
    if blocked := _require('execution_session.start', label, handler, data, ['dispatch_id','authorization_path']): return blocked
    base=_root(root); payload=ExecutionSessionController(root=base).start(str(dispatch_id), str(authorization_path), confirm_live_execution=_truthy(confirm_live_execution)); read,written=_session_refs(base,payload)
    outcome='completed' if payload.get('state') in {'completed_execution','validation_ready'} else 'blocked' if payload.get('state')=='blocked' else 'failed' if payload.get('state')=='failed' else 'completed'
    return OfficeActionResult('execution_session.start', label, _request_id(params), 'execution-control', outcome, f"Start session {payload.get('execution_session_id')} state={payload.get('state')} stage={payload.get('current_stage')} reasons={payload.get('blocking_reasons') or []}.", handler, read, written, ['execution session start advanced runtime state'] if outcome=='completed' else [], 'steward_and_traffic_controller_gated')

def execution_session_resume(root=None, session_id: str | None = None, **params: Any) -> OfficeActionResult:
    label='Resume execution session'; handler='estate.core.execution_session_controller.ExecutionSessionController.resume'
    if blocked := _require('execution_session.resume', label, handler, {'session_id':session_id}, ['session_id']): return blocked
    base=_root(root); payload=ExecutionSessionController(root=base).resume(str(session_id)); read,written=_session_refs(base,payload)
    outcome='failed' if payload.get('state')=='failed' else 'completed'
    return OfficeActionResult('execution_session.resume', label, _request_id(params), 'execution-control', outcome, f"Resume inspected session {session_id}; state={payload.get('state')} stage={payload.get('current_stage')}.", handler, read, written, ['session resume/reconciliation evidence updated'], 'duplicate_provider_call_protection_preserved')

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



def operations_host_control(root=None, host_action: str | None = None, **params: Any) -> OfficeActionResult:
    action = str(host_action or params.get('action') or '').strip()
    label = 'Operations Runtime host control'; handler = 'estate.core.operations_runtime_host.OperationsRuntimeHost'
    if action not in {'start', 'stop', 'restart', 'status'}:
        return _blocked('operations_surface.host_control', label, 'operational-activity', handler, 'host_action must be one of start, stop, restart, or status.', request_id=params.get('request_id'))
    base = _root(root); host = OperationsRuntimeHost(root=base)
    payload = getattr(host, action)()
    outcome = 'failed' if payload.get('state') == 'failed' else 'completed'
    return OfficeActionResult('operations_surface.host_control', label, _request_id(params), 'operational-activity', outcome, f"Operations Runtime host {action} returned state={payload.get('state') or payload.get('host_state') or 'recorded'}.", f'{handler}.{action}', ['runtime/operations_runtime/status/latest.json'], ['runtime/operations_runtime/status/latest.json', 'runtime/operations_runtime/heartbeat.json'], [f'operations runtime host {action} requested'], 'traffic_controller_constraints_preserved')


def operations_scheduler_control(root=None, scheduler_action: str | None = None, job_id: str | None = None, event_name: str | None = None, **params: Any) -> OfficeActionResult:
    action = str(scheduler_action or params.get('action') or '').strip()
    label = 'Operations Scheduler job control'; handler = 'estate.core.operations_scheduler_runtime.OperationsSchedulerRuntime'
    base = _root(root); runtime = OperationsSchedulerRuntime(base)
    if action == 'enable':
        if not job_id: return _blocked('operations_surface.scheduler_control', label, 'operational-activity', handler + '.enable', 'job_id is required.', request_id=params.get('request_id'))
        payload = runtime.enable(str(job_id)); h = handler + '.enable'; msg = f"Scheduler job {job_id} enabled={payload.get('state',{}).get('enabled')}."
    elif action == 'disable':
        if not job_id: return _blocked('operations_surface.scheduler_control', label, 'operational-activity', handler + '.disable', 'job_id is required.', request_id=params.get('request_id'))
        payload = runtime.disable(str(job_id)); h = handler + '.disable'; msg = f"Scheduler job {job_id} enabled={payload.get('state',{}).get('enabled')}."
    elif action == 'trigger':
        if not event_name: return _blocked('operations_surface.scheduler_control', label, 'operational-activity', handler + '.trigger', 'event_name is required.', request_id=params.get('request_id'))
        payload = runtime.trigger(str(event_name)); h = handler + '.trigger'; msg = f"Scheduler event {event_name} woke {payload.get('jobs_woken', 0)} job(s)."
    else:
        return _blocked('operations_surface.scheduler_control', label, 'operational-activity', handler, 'scheduler_action must be enable, disable, or trigger.', request_id=params.get('request_id'))
    return _completed('operations_surface.scheduler_control', label, 'operational-activity', h, msg, read=['runtime/operations_scheduler/state.json'], written=['runtime/operations_scheduler/state.json', 'runtime/operations_scheduler/status.json'], state=['operations scheduler state persisted'], request_id=params.get('request_id'))


def operations_extension_control(root=None, extension_action: str | None = None, extension_id: str | None = None, **params: Any) -> OfficeActionResult:
    from estate.core.background_operations_extension_runtime import BackgroundOperationsExtensionRuntime
    action = str(extension_action or params.get('action') or '').strip()
    label = 'Background Operations extension control'; handler = 'estate.core.background_operations_extension_runtime.BackgroundOperationsExtensionRuntime'
    base = _root(root); runtime = BackgroundOperationsExtensionRuntime(base)
    try:
        if action == 'inspect': payload = runtime.inspect(); h = handler + '.inspect'
        elif action == 'validate': payload = runtime.validate(); h = handler + '.validate'
        elif action == 'dry-run': payload = runtime.dry_run(); h = handler + '.dry_run'
        elif action == 'enable':
            if not extension_id: return _blocked('operations_surface.extension_control', label, 'operational-activity', handler + '.enable', 'extension_id is required.', request_id=params.get('request_id'))
            payload = runtime.enable(str(extension_id)); h = handler + '.enable'
        elif action == 'disable':
            if not extension_id: return _blocked('operations_surface.extension_control', label, 'operational-activity', handler + '.disable', 'extension_id is required.', request_id=params.get('request_id'))
            payload = runtime.disable(str(extension_id)); h = handler + '.disable'
        else:
            return _blocked('operations_surface.extension_control', label, 'operational-activity', handler, 'extension_action must be inspect, validate, dry-run, enable, or disable.', request_id=params.get('request_id'))
    except Exception as exc:
        return OfficeActionResult('operations_surface.extension_control', label, _request_id(params), 'operational-activity', 'failed', f'Extension control failed: {exc}', handler)
    return _completed('operations_surface.extension_control', label, 'operational-activity', h, f"Extension action {action} completed; valid={payload.get('valid', payload.get('validation',{}).get('valid'))}.", read=['config/background_operations/extensions.json'], written=['runtime/background_operations/extensions/status.json', 'runtime/background_operations/extensions/state.json'], state=['background operations extension state visible in Office'], request_id=params.get('request_id'))


def operations_watch_control(root=None, watch_action: str | None = None, watch_id: str | None = None, **params: Any) -> OfficeActionResult:
    action = str(watch_action or params.get('action') or '').strip()
    label = 'Operational Watch control'; handler = 'estate.core.operational_watch_runtime.OperationalWatchRuntime'
    if action not in {'enable', 'disable', 'pause', 'evaluate'}:
        return _blocked('operations_surface.watch_control', label, 'operational-activity', handler, 'watch_action must be enable, disable, pause, or evaluate.', request_id=params.get('request_id'))
    if not watch_id:
        return _blocked('operations_surface.watch_control', label, 'operational-activity', handler, 'watch_id is required.', request_id=params.get('request_id'))
    base = _root(root); runtime = OperationalWatchRuntime(base)
    if action == 'enable': payload = runtime.set_enabled(str(watch_id), True); h = handler + '.set_enabled'
    elif action == 'disable': payload = runtime.set_enabled(str(watch_id), False); h = handler + '.set_enabled'
    elif action == 'pause': payload = runtime.pause(str(watch_id)); h = handler + '.pause'
    else: payload = runtime.evaluate(str(watch_id), dry_run=True); h = handler + '.evaluate'
    return _completed('operations_surface.watch_control', label, 'operational-activity', h, f"Watch {watch_id} {action} completed; enabled={payload.get('enabled')}.", read=['runtime/background_operations/watch_state.json'], written=['runtime/background_operations/watch_state.json', 'runtime/background_operations/watches.json'], state=['operational watch state persisted or inspected'], request_id=params.get('request_id'))


def operations_cycle_control(root=None, dry_run: Any = None, mode: str = 'observe-only', max_audit_requests: Any = 1, **params: Any) -> OfficeActionResult:
    label = 'Trigger one bounded Operations Runtime cycle'; handler = 'estate.core.operations_runtime_service.OperationsRuntimeService.run_once'
    base = _root(root)
    payload = OperationsRuntimeService(base).run_once(dry_run=_truthy(dry_run), mode=str(mode or 'observe-only'), max_audit_requests=int(max_audit_requests or 1))
    outcome = 'failed' if payload.get('runtime_state') == 'failed' or payload.get('errors') else 'completed'
    return OfficeActionResult('operations_surface.trigger_cycle', label, _request_id(params), 'operational-activity', outcome, f"Bounded cycle {payload.get('cycle_id')} finished state={payload.get('runtime_state')} errors={len(payload.get('errors') or [])}.", handler, ['runtime/operations_runtime/status/latest.json'], ['runtime/operations_runtime/status/latest.json', 'runtime/operations_runtime/cycles'], ['one bounded operations runtime cycle completed'], 'traffic_controller_constraints_preserved')


def operations_hold_control(root=None, hold_action: str | None = None, work_package: str | None = None, target: str = 'estate-main', **params: Any) -> OfficeActionResult:
    action = str(hold_action or params.get('action') or '').strip()
    label = 'Merge discovery audit hold control'; handler = 'estate.core.merge_discovery_runtime.MergeDiscoveryRuntime'
    if action not in {'hold', 'release'}:
        return _blocked('operations_surface.hold_control', label, 'operational-activity', handler, 'hold_action must be hold or release.', request_id=params.get('request_id'))
    if not work_package:
        return _blocked('operations_surface.hold_control', label, 'operational-activity', handler, 'work_package is required.', request_id=params.get('request_id'))
    runtime = MergeDiscoveryRuntime(_root(root)); payload = getattr(runtime, action)(target=target, work_package=work_package)
    return _completed('operations_surface.hold_control', label, 'operational-activity', f'{handler}.{action}', f"Hold action {action} recorded for {work_package}; status={payload.get('status') or payload.get('state') or 'recorded'}.", read=['runtime/merge_discovery'], written=['runtime/merge_discovery'], state=['merge discovery admission hold state persisted'], request_id=params.get('request_id'))


def operations_inspect_evidence(root=None, evidence_path: str | None = None, **params: Any) -> OfficeActionResult:
    label = 'Inspect operations evidence'; handler = 'pathlib.Path.read_text'
    if not evidence_path:
        return _blocked('operations_surface.inspect_evidence', label, 'operational-activity', handler, 'evidence_path is required.', request_id=params.get('request_id'))
    base = _root(root); path = (base / evidence_path).resolve(); root_resolved = base.resolve()
    if not str(path).startswith(str(root_resolved)) or not path.exists() or not path.is_file():
        return _blocked('operations_surface.inspect_evidence', label, 'operational-activity', handler, 'Evidence path must be an existing file under the Estate root.', read=[str(evidence_path)], request_id=params.get('request_id'))
    sample = path.read_text(encoding='utf-8', errors='replace')[:500]
    return _completed('operations_surface.inspect_evidence', label, 'operational-activity', handler, f"Evidence {evidence_path} is readable ({path.stat().st_size} bytes): {sample}", read=[evidence_path], request_id=params.get('request_id'))


def operations_dashboard_refresh(root=None, **params: Any) -> OfficeActionResult:
    base = _root(root)
    # Regenerate the existing local Office payload/HTML; the dashboard itself reads durable artifacts only.
    from estate.core.steward_command_center import generate_command_center
    generate_command_center(root=base, write=True)
    return _completed('operations_dashboard.refresh', 'Refresh operational command dashboard', 'operational-dashboard', 'estate.core.steward_command_center.generate_command_center', 'Operational command dashboard refreshed from durable runtime artifacts.', read=['runtime/operations_runtime/status/latest.json','runtime/background_operations/status/latest.json','runtime/work_packages/assignment_queue.json','runtime/post_merge_audit/status/latest.json'], written=['runtime/steward/command_center.html'], state=['office operational command dashboard refreshed'], request_id=params.get('request_id'))

def operations_dashboard_inspect_evidence(root=None, evidence_path: str | None = None, **params: Any) -> OfficeActionResult:
    result = operations_inspect_evidence(root=root, evidence_path=evidence_path, **params)
    result.action_id = 'operations_dashboard.inspect_evidence'
    result.action_label = 'Inspect dashboard evidence'
    result.target_tab = 'operational-dashboard'
    return result

def _planning_result(action_id: str, label: str, tab: str, handler: str, payload, request_id: str | None = None) -> OfficeActionResult:
    return OfficeActionResult(action_id, label, request_id or _request_id(), tab, payload.outcome, payload.message, handler, payload.artifacts_read, payload.artifacts_written, payload.runtime_state_changed, 'safe_local_action' if payload.outcome == 'completed' else 'gated_or_missing_requirement')

def parking_lot_control(root=None, planning_action: str | None = None, item_id: str | None = None, **params: Any) -> OfficeActionResult:
    payload = parking_action(root=root, action=planning_action or params.get('action') or '', item_id=item_id, **params)
    return _planning_result('parking_lot.control', 'Parking Lot item control', 'parking', 'estate.core.office_parking_lot_controls.parking_action', payload, params.get('request_id'))

def roadmap_control(root=None, planning_action: str | None = None, item_id: str | None = None, **params: Any) -> OfficeActionResult:
    payload = roadmap_action(root=root, action=planning_action or params.get('action') or '', item_id=item_id, **params)
    return _planning_result('roadmap.control', 'Roadmap item control', 'roadmap', 'estate.core.office_parking_lot_controls.roadmap_action', payload, params.get('request_id'))

def planning_control_undo(root=None, **params: Any) -> OfficeActionResult:
    payload = planning_undo(root=root)
    tab = (payload.data or {}).get('surface') or 'parking'
    return _planning_result('planning.undo_last_local_change', 'Undo last planning change', tab, 'estate.core.office_parking_lot_controls.planning_undo', payload, params.get('request_id'))

def planning_filter(root=None, surface: str = 'parking', query: str = '', status: str = '', priority: str = '', owner: str = '', **params: Any) -> OfficeActionResult:
    payload = filter_items(root=root, surface=surface, query=query, status=status, priority=priority, owner=owner)
    return _planning_result('planning.filter', 'Filter/search planning items', 'parking' if surface == 'parking' else 'roadmap', 'estate.core.office_parking_lot_controls.filter_items', payload, params.get('request_id'))

def generate_daily_briefing(root=None, **_: Any) -> OfficeActionResult:
    base = _root(root); generate_daily_board_integration(root=base, write=True); generate_morning_briefing(root=base, write=True)
    return _completed('daily_board.generate_morning_briefing', 'Generate morning briefing', 'daily-board', 'estate.core.daily_board_integration.generate_daily_board_integration + estate.core.morning_briefing.generate_morning_briefing', 'Daily Board integration and morning briefing generated locally.', written=['runtime/operations/daily_board_integration.json', 'operations/boards/daily_board_integration.md', 'runtime/briefings/morning_briefing.json', 'operations/briefings/morning_briefing.md'], state=['daily board and briefing artifacts refreshed'])

def personnel_refresh(root=None, selected_employee_id: str | None = None, filters_json: str | None = None, **params: Any) -> OfficeActionResult:
    base = _root(root)
    filters = {}
    if filters_json:
        try:
            filters = json.loads(filters_json)
        except Exception:
            filters = {}
    payload = refresh_personnel_directory(base, selected_employee_id=selected_employee_id, filters=filters)
    summary = payload.get('summary') or {}
    msg = (f"Personnel refreshed: valid={summary.get('valid_record_count', 0)}, malformed={summary.get('malformed_record_count', 0)}, "
           f"duplicates={summary.get('duplicate_employee_id_count', 0)}, orphans={summary.get('orphaned_manager_count', 0)}, cycles={summary.get('cycle_count', 0)}, "
           f"added={summary.get('added_count', 0)}, changed={summary.get('changed_count', 0)}, removed={summary.get('removed_count', 0)}.")
    return _completed('personnel.refresh', 'Refresh Personnel', 'personnel', 'estate.core.office_personnel_directory.refresh_personnel_directory', msg, read=['data/registry/personnel.json', 'data/registry/mailboxes.json', 'collaboration/work_packages', 'collaboration/messages'], written=['runtime/steward/office_personnel_directory.json'], state=['office personnel payload refreshed'], request_id=params.get('request_id'))

def personnel_open_detail(root=None, employee_id: str | None = None, **params: Any) -> OfficeActionResult:
    if not employee_id:
        return _blocked('personnel.open_employee_detail', 'Open employee details', 'personnel', 'estate.core.office_personnel_directory.open_employee_detail', 'employee_id is required.', request_id=params.get('request_id'))
    payload = open_employee_detail(employee_id, root)
    if payload.get('outcome') != 'completed':
        return _blocked('personnel.open_employee_detail', 'Open employee details', 'personnel', 'estate.core.office_personnel_directory.open_employee_detail', payload.get('message') or 'Employee unavailable.', read=payload.get('artifacts_read') or [], request_id=params.get('request_id'))
    return _completed('personnel.open_employee_detail', 'Open employee details', 'personnel', 'estate.core.office_personnel_directory.open_employee_detail', f"Employee {employee_id} detail resolved.", read=payload.get('artifacts_read') or [], state=['selected employee detail resolved'], request_id=params.get('request_id'))

def personnel_open_mailbox(root=None, employee_id: str | None = None, **params: Any) -> OfficeActionResult:
    if not employee_id:
        return _blocked('personnel.open_mailbox', 'Open mailbox', 'personnel', 'estate.core.office_personnel_directory.route_personnel_mailbox', 'employee_id is required.', request_id=params.get('request_id'))
    payload = route_personnel_mailbox(employee_id, root)
    if payload.get('outcome') != 'completed':
        return _blocked('personnel.open_mailbox', 'Open mailbox', 'personnel', 'estate.core.office_personnel_directory.route_personnel_mailbox', payload.get('message') or 'Mailbox route blocked.', read=payload.get('artifacts_read') or [], request_id=params.get('request_id'))
    route = payload.get('route') or {}
    return _completed('personnel.open_mailbox', 'Open mailbox', 'mailboxes', 'estate.core.office_personnel_directory.route_personnel_mailbox', f"Mailbox route ready for employee {route.get('employee_id')} mailbox {route.get('mailbox_id')}.", read=payload.get('artifacts_read') or [], state=['mailbox route selected'], request_id=params.get('request_id'))

def personnel_open_conversation(root=None, employee_id: str | None = None, **params: Any) -> OfficeActionResult:
    if not employee_id:
        return _blocked('personnel.open_conversation', 'Open conversation', 'personnel', 'estate.core.office_personnel_directory.route_personnel_conversation', 'employee_id is required.', request_id=params.get('request_id'))
    payload = route_personnel_conversation(employee_id, root)
    if payload.get('outcome') != 'completed':
        return _blocked('personnel.open_conversation', 'Open conversation', 'personnel', 'estate.core.office_personnel_directory.route_personnel_conversation', payload.get('message') or 'Conversation route blocked.', read=payload.get('artifacts_read') or [], request_id=params.get('request_id'))
    route = payload.get('route') or {}
    return _completed('personnel.open_conversation', 'Open conversation', 'resident-conversations', 'estate.core.office_personnel_directory.route_personnel_conversation', f"Conversation route ready for employee {route.get('employee_id')} selected {route.get('selected')}.", read=payload.get('artifacts_read') or [], state=['conversation route selected'], request_id=params.get('request_id'))


def mailbox_refresh(root=None, query: str = '', status: str = '', mailbox_id: str = '', sort: str = 'created_at', **params: Any) -> OfficeActionResult:
    base = _root(root); payload = refresh_mailbox_control_center(base, query=query, status=status, mailbox_id=mailbox_id, sort=sort)
    return _completed('mailboxes.refresh', 'Refresh mailbox and notification state', 'mailboxes', 'estate.core.office_mailbox_control.refresh_mailbox_control_center', f"Mailbox state refreshed with {(payload.get('summary') or {}).get('filtered_message_count', 0)} visible message(s).", written=['collaboration/mailboxes/index.json','runtime/notifications/operations_notification_center.json','runtime/steward/mailbox_control_center.json'], state=['mailbox and notification Office payload refreshed'], request_id=params.get('request_id'))

def mailbox_open_message(root=None, message_id: str | None = None, **params: Any) -> OfficeActionResult:
    if not message_id:
        return _blocked('mailboxes.open_message', 'Open message details', 'mailboxes', 'estate.core.office_mailbox_control.open_message_detail', 'message_id is required.', request_id=params.get('request_id'))
    payload = open_message_detail(message_id, _root(root))
    return _completed('mailboxes.open_message', 'Open message details', 'mailboxes', 'estate.core.office_mailbox_control.open_message_detail', f"Message {payload.get('message_id')} opened from {payload.get('path')}.", read=[payload.get('path')], written=['runtime/steward/mailbox_control_center.json'], state=['selected message detail resolved'], request_id=params.get('request_id'))

def mailbox_acknowledge(root=None, message_id: str | None = None, actor: str = 'Office', note: str = 'Acknowledged from Office.', **params: Any) -> OfficeActionResult:
    if not message_id:
        return _blocked('mailboxes.local_acknowledge', 'Acknowledge message locally', 'mailboxes', 'estate.core.collaboration_messages.acknowledge_message', 'message_id is required.', request_id=params.get('request_id'))
    payload = acknowledge_message(message_id, actor=actor, note=note, root=_root(root)); refresh_mailbox_control_center(_root(root))
    return _completed('mailboxes.local_acknowledge', 'Acknowledge message locally', 'mailboxes', 'estate.core.collaboration_messages.acknowledge_message', f"Message {message_id} acknowledged via canonical Communication Bus acknowledgement; source closure semantics remain message-local.", read=[payload.get('message_path')], written=[payload.get('message_path'), payload.get('acknowledgement_path'), 'collaboration/mailboxes/index.json','runtime/steward/mailbox_control_center.json'], state=['message acknowledgement persisted'], request_id=params.get('request_id'))

def mailbox_mark_read(root=None, message_id: str | None = None, read_state: str = 'read', actor: str = 'Office', **params: Any) -> OfficeActionResult:
    if not message_id:
        return _blocked('mailboxes.mark_read_state', 'Mark message read/unread', 'mailboxes', 'estate.core.office_mailbox_control.mark_message_read_state', 'message_id is required.', request_id=params.get('request_id'))
    mark_message_read_state(message_id, read_state, _root(root), actor=actor)
    return _completed('mailboxes.mark_read_state', 'Mark message read/unread', 'mailboxes', 'estate.core.office_mailbox_control.mark_message_read_state', f"Message {message_id} marked {read_state} in durable Office read-state evidence.", read=['collaboration/messages'], written=['runtime/steward/mailbox_message_read_state.json','runtime/steward/mailbox_control_center.json'], state=['read/unread evidence persisted'], request_id=params.get('request_id'))

def mailbox_reply(root=None, message_id: str | None = None, actor: str = 'Office', body: str = '', route_target: str | None = None, **params: Any) -> OfficeActionResult:
    if not message_id:
        return _blocked('mailboxes.reply_or_route', 'Reply or route message', 'mailboxes', 'estate.core.collaboration_messages.create_reply + estate.core.office_mailbox_control.route_message', 'message_id is required.', request_id=params.get('request_id'))
    base=_root(root)
    if body:
        payload=create_reply(message_id, actor=actor, body=body, root=base); refresh_mailbox_control_center(base)
        return _completed('mailboxes.reply_or_route', 'Reply or route message', 'mailboxes', 'estate.core.collaboration_messages.create_reply', f"Reply created for {message_id} through canonical Communication Bus.", written=[payload.get('reply_path'),'collaboration/mailboxes/index.json','runtime/steward/mailbox_control_center.json'], state=['reply persisted'], request_id=params.get('request_id'))
    route=route_message(message_id, route_target or 'mailboxes', base, actor=actor)
    return _completed('mailboxes.reply_or_route', 'Reply or route message', 'mailboxes', 'estate.core.office_mailbox_control.route_message', f"Route evidence recorded for {message_id} to {route.get('route_target')}.", written=['runtime/steward/mailbox_message_routes.jsonl','runtime/steward/mailbox_control_center.json'], state=['route evidence persisted'], request_id=params.get('request_id'))

def mailbox_open_personnel(root=None, employee_id: str | None = None, **params: Any) -> OfficeActionResult:
    if not employee_id:
        return _blocked('mailboxes.open_personnel', 'Open sender/recipient personnel', 'mailboxes', 'estate.core.office_personnel_directory.open_employee_detail', 'employee_id is required.', request_id=params.get('request_id'))
    payload=mailbox_open_employee_detail(employee_id, _root(root))
    if payload.get('outcome') != 'completed':
        return _blocked('mailboxes.open_personnel', 'Open sender/recipient personnel', 'mailboxes', 'estate.core.office_personnel_directory.open_employee_detail', payload.get('message') or 'Personnel not found.', request_id=params.get('request_id'))
    return _completed('mailboxes.open_personnel', 'Open sender/recipient personnel', 'personnel', 'estate.core.office_personnel_directory.open_employee_detail', f"Personnel details opened for employee {employee_id}.", read=payload.get('artifacts_read') or [], state=['personnel detail route resolved'], request_id=params.get('request_id'))

def mailbox_clear_attention(root=None, attention_id: str | None = None, actor: str = 'Office', reason: str = 'Resolved locally', **params: Any) -> OfficeActionResult:
    if not attention_id:
        return _blocked('attention.clear_local', 'Clear resolved local attention', 'notifications', 'estate.core.office_mailbox_control.local_attention_acknowledge', 'attention_id is required.', request_id=params.get('request_id'))
    local_attention_acknowledge(attention_id, _root(root), actor=actor, reason=reason)
    return _completed('attention.clear_local', 'Clear resolved local attention', 'notifications', 'estate.core.office_mailbox_control.local_attention_acknowledge', f"Attention {attention_id} cleared locally only; authoritative source closure was not changed.", written=['runtime/steward/local_attention_acknowledgements.json','runtime/steward/mailbox_control_center.json'], state=['local attention acknowledgement persisted'], request_id=params.get('request_id'))

def mailbox_inspect_failures(root=None, **params: Any) -> OfficeActionResult:
    payload=inspect_delivery_failures(_root(root))
    return _completed('delivery.inspect_failures', 'Inspect delivery failures', 'notifications', 'estate.core.office_mailbox_control.inspect_delivery_failures', f"Delivery failure inspection found {payload.get('failure_count', 0)} actionable failure source(s).", read=payload.get('sources') or [], written=['runtime/steward/delivery_failure_inspection.json'], state=['delivery failure evidence inspected'], request_id=params.get('request_id'))

HANDLERS: dict[str, Callable[..., OfficeActionResult]] = {f.__name__: f for f in []}
HANDLERS.update({
 'ai_services.refresh_local_inventory': refresh_ai_services,
 'ai_services.start': ai_service_start,
 'ai_services.stop': ai_service_stop,
 'ai_services.restart': ai_service_restart,
 'ai_services.load_model': ai_model_load,
 'ai_services.unload_model': ai_model_unload,
 'ai_services.inspect_state': ai_service_inspect,
 'ai_services.launch_local_interface': ai_service_launch_interface,
 'validation.run_production_readiness': run_production_readiness,
 'validation.refresh_center': validation_refresh_center,
 'validation.request': validation_request,
 'validation.acknowledge_failure': validation_acknowledge_failure,
 'validation.automatic_validator_status': validation_auto_status,
 'validation.open_artifact': validation_open_artifact,
 'validation.governed_retry': validation_governed_retry,
 'work_packages.validate_selected': validate_selected_work_package,
 'work_packages.refresh_assignment_queue': refresh_work_package_queue,
 'work_packages.assign': assign_work_package,
 'work_packages.update_state': update_work_package_state,
 'work_packages.promote': promote_work_package,
 'work_packages.open_artifact': open_work_package_artifact,
 'work_packages.filter': filter_work_packages,

 'mailboxes.refresh': mailbox_refresh,
 'mailboxes.open_message': mailbox_open_message,
 'mailboxes.local_acknowledge': mailbox_acknowledge,
 'mailboxes.mark_read_state': mailbox_mark_read,
 'mailboxes.reply_or_route': mailbox_reply,
 'mailboxes.open_personnel': mailbox_open_personnel,
 'attention.clear_local': mailbox_clear_attention,
 'delivery.inspect_failures': mailbox_inspect_failures,
 'notifications.refresh_center': refresh_notifications,
 'notifications.local_acknowledge': local_ack_notification,
 'alfred.request_briefing': request_alfred_briefing,
 'mission_control.refresh_payload': refresh_mission_control,
 'daily_board.generate_morning_briefing': generate_daily_briefing,
 'orchestrator_intake.record_decision': record_orchestrator_intake_decision,
 'operations_control.record_decision': record_operations_control_decision,
 'operations_surface.inspect_evidence': operations_inspect_evidence,
 'operations_surface.hold_control': operations_hold_control,
 'operations_surface.trigger_cycle': operations_cycle_control,
 'operations_surface.extension_control': operations_extension_control,
 'operations_surface.watch_control': operations_watch_control,
 'operations_surface.scheduler_control': operations_scheduler_control,
 'operations_surface.host_control': operations_host_control,
 'operational_activity.refresh': refresh_operational_activity,
 'operational_activity.acknowledge_attention': acknowledge_operational_activity,
 'operational_activity.route_to_workspace': route_operational_activity,
 'operational_activity.open_artifact': open_operational_artifact,
 'operational_activity.filter': filter_operational_activity,
 'operations_dashboard.refresh': operations_dashboard_refresh,
 'operations_dashboard.inspect_evidence': operations_dashboard_inspect_evidence,
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
 'parking_lot.control': parking_lot_control,
 'roadmap.control': roadmap_control,
 'planning.undo_last_local_change': planning_control_undo,
 'planning.filter': planning_filter,
 'personnel.refresh': personnel_refresh,
 'personnel.open_employee_detail': personnel_open_detail,
 'personnel.open_mailbox': personnel_open_mailbox,
 'personnel.open_conversation': personnel_open_conversation,
})

ACTION_CONTROLS = [

 {'action_id':'personnel.refresh','label':'Refresh Personnel','target_tab':'personnel','handler':'personnel_refresh','availability':'available','note':'Rebuilds the Office personnel/org-chart payload from canonical artifacts.'},
 {'action_id':'personnel.open_employee_detail','label':'Open employee details','target_tab':'personnel','handler':'personnel_open_detail','availability':'available','requires_input':'employee_id'},
 {'action_id':'personnel.open_mailbox','label':'Open mailbox','target_tab':'personnel','handler':'personnel_open_mailbox','availability':'available','requires_input':'employee_id'},
 {'action_id':'personnel.open_conversation','label':'Open conversation','target_tab':'personnel','handler':'personnel_open_conversation','availability':'available','requires_input':'employee_id'},
 {'action_id':'parking_lot.control','label':'Parking Lot item control','target_tab':'parking','handler':'parking_lot_control','availability':'available','requires_input':'planning_action,item_id','note':'Actions: create, edit, move_up, move_down, reorder, set_priority, accept, archive, reject, restore, promote.'},
 {'action_id':'roadmap.control','label':'Roadmap item control','target_tab':'roadmap','handler':'roadmap_control','availability':'available','requires_input':'planning_action,item_id','note':'Actions: create, edit, move_up, move_down, reorder, set_priority.'},
 {'action_id':'planning.undo_last_local_change','label':'Undo last planning change','target_tab':'parking','handler':'planning_control_undo','availability':'available','note':'Restores the last safe local Parking Lot or Roadmap order/status/content change.'},
 {'action_id':'planning.filter','label':'Search/filter planning items','target_tab':'parking','handler':'planning_filter','availability':'available','requires_input':'surface,query,status,priority,owner'},
 {'action_id':'planning.undo_last_local_change','label':'Undo last planning change','target_tab':'roadmap','handler':'planning_control_undo','availability':'available','note':'Restores the last safe local Parking Lot or Roadmap order/status/content change.'},
 {'action_id':'planning.filter','label':'Search/filter planning items','target_tab':'roadmap','handler':'planning_filter','availability':'available','requires_input':'surface,query,status,priority,owner'},
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
 {'action_id':'ai_services.start','label':'Start AI service','target_tab':'ai-services-models','handler':'ai_service_start','availability':'available','requires_input':'service_id,approved_by','note':'Starts only registered services through estate.ai_services.control.request.'},
 {'action_id':'ai_services.stop','label':'Stop AI service','target_tab':'ai-services-models','handler':'ai_service_stop','availability':'available','requires_input':'service_id,approved_by','note':'Stops only tracked registered service processes.'},
 {'action_id':'ai_services.restart','label':'Restart AI service','target_tab':'ai-services-models','handler':'ai_service_restart','availability':'available','requires_input':'service_id,approved_by','note':'Composes canonical stop then start; unsupported steps are reported truthfully.'},
 {'action_id':'ai_services.load_model','label':'Load supported model','target_tab':'ai-services-models','handler':'ai_model_load','availability':'available','requires_input':'service_id,model,approved_by','note':'Loads only model names accepted by the registered manifest/policy.'},
 {'action_id':'ai_services.unload_model','label':'Unload supported model','target_tab':'ai-services-models','handler':'ai_model_unload','availability':'available','requires_input':'service_id,model,approved_by','note':'Blocked unless the manifest declares unload_model.'},
 {'action_id':'ai_services.inspect_state','label':'Inspect logs/readiness/provider state','target_tab':'ai-services-models','handler':'ai_service_inspect','availability':'available','requires_input':'service_id'},
 {'action_id':'ai_services.launch_local_interface','label':'Open local interface route','target_tab':'ai-services-models','handler':'ai_service_launch_interface','availability':'available','requires_input':'service_id','note':'Routes only registered loopback interfaces such as Open WebUI.'},
 {'action_id':'validation.refresh_center','label':'Refresh validation/audit center','target_tab':'validation','handler':'validation_refresh_center','availability':'available','requires_input':'result,package,date_from,date_to,owner,attention_state','note':'Inspects pending, running, completed, and failed validation/audit/verdict artifacts without granting acceptance.'},
 {'action_id':'validation.request','label':'Request validation/revalidation','target_tab':'validation','handler':'validation_request','availability':'available','requires_input':'work_package_id,revalidate','note':'Delegates to canonical work-package validation and optional production-readiness refresh.'},
 {'action_id':'validation.acknowledge_failure','label':'Acknowledge failure attention','target_tab':'validation','handler':'validation_acknowledge_failure','availability':'available','requires_input':'artifact_id,acknowledged_by,reason','note':'Local durable acknowledgement only; source evidence remains unchanged.'},
 {'action_id':'validation.automatic_validator_status','label':'Inspect automatic-validator status','target_tab':'validation','handler':'validation_auto_status','availability':'available'},
 {'action_id':'validation.open_artifact','label':'Open validation/audit/verdict artifact','target_tab':'validation','handler':'validation_open_artifact','availability':'available','requires_input':'artifact_path'},
 {'action_id':'validation.governed_retry','label':'Run governed audit retry','target_tab':'validation','handler':'validation_governed_retry','availability':'available','requires_input':'max_count','note':'Uses existing PostMergeAuditProcessor queue; no second retry queue.'},
 {'action_id':'validation.run_production_readiness','label':'Run production readiness refresh','target_tab':'validation','handler':'run_production_readiness','availability':'available','note':'Evidence is not institutional acceptance.'},
 {'action_id':'work_packages.refresh_assignment_queue','label':'Refresh assignment queue','target_tab':'work-packages','handler':'refresh_work_package_queue','availability':'available'},
 {'action_id':'work_packages.validate_selected','label':'Validate selected work package','target_tab':'work-packages','handler':'validate_selected_work_package','availability':'available','requires_input':'work_package_id'},
 {'action_id':'work_packages.assign','label':'Assign/reassign','target_tab':'work-packages','handler':'assign_work_package','availability':'available','requires_input':'work_package_id,owner','note':'Persists assignment through the canonical local assignment-queue runtime and refreshes the Office payload.'},
 {'action_id':'work_packages.update_state','label':'Change status/priority','target_tab':'work-packages','handler':'update_work_package_state','availability':'available','requires_input':'work_package_id,state,priority','note':'Supported states: pending, open, claimed, blocked, completed. Supported priorities: low, normal, high, urgent.'},
 {'action_id':'work_packages.promote','label':'Promote canonical state','target_tab':'work-packages','handler':'promote_work_package','availability':'available','requires_input':'work_package_id','note':'Advances pending → open → claimed → completed; blocked/completed packages are truthfully blocked.'},
 {'action_id':'work_packages.open_artifact','label':'Open source/evidence','target_tab':'work-packages','handler':'open_work_package_artifact','availability':'available','requires_input':'work_package_id,artifact_kind','note':'artifact_kind may be source, completion_receipt, validation, operations_validation, pr, or commit.'},
 {'action_id':'work_packages.filter','label':'Filter/search/sort','target_tab':'work-packages','handler':'filter_work_packages','availability':'available','requires_input':'query,state,priority,owner'},

 {'action_id':'mailboxes.refresh','label':'Refresh mailbox/notification state','target_tab':'mailboxes','handler':'mailbox_refresh','availability':'available','requires_input':'query,status,mailbox_id,sort'},
 {'action_id':'mailboxes.open_message','label':'Open message details','target_tab':'mailboxes','handler':'mailbox_open_message','availability':'available','requires_input':'message_id'},
 {'action_id':'mailboxes.local_acknowledge','label':'Acknowledge message locally','target_tab':'mailboxes','handler':'mailbox_acknowledge','availability':'available','requires_input':'message_id,actor,note','note':'Uses canonical Communication Bus acknowledgement; not authoritative external closure.'},
 {'action_id':'mailboxes.mark_read_state','label':'Mark read/unread','target_tab':'mailboxes','handler':'mailbox_mark_read','availability':'available','requires_input':'message_id,read_state'},
 {'action_id':'mailboxes.reply_or_route','label':'Reply or route','target_tab':'mailboxes','handler':'mailbox_reply','availability':'available','requires_input':'message_id,body,route_target','note':'Replies use canonical collaboration messages; routes record local route evidence.'},
 {'action_id':'mailboxes.open_personnel','label':'Open sender/recipient personnel','target_tab':'mailboxes','handler':'mailbox_open_personnel','availability':'available','requires_input':'employee_id'},
 {'action_id':'attention.clear_local','label':'Clear resolved local attention','target_tab':'notifications','handler':'mailbox_clear_attention','availability':'available','requires_input':'attention_id,actor,reason','note':'Local acknowledgement only; source closure remains distinct.'},
 {'action_id':'delivery.inspect_failures','label':'Inspect delivery failures','target_tab':'notifications','handler':'mailbox_inspect_failures','availability':'available'},
 {'action_id':'notifications.refresh_center','label':'Refresh notification center','target_tab':'notifications','handler':'refresh_notifications','availability':'available'},
 {'action_id':'notifications.local_acknowledge','label':'Acknowledge notification locally','target_tab':'notifications','handler':'local_ack_notification','availability':'available','requires_input':'notification_id','note':'Local state only; authoritative closure is unchanged.'},
 {'action_id':'alfred.request_briefing','label':'Request Alfred briefing','target_tab':'alfred','handler':'request_alfred_briefing','availability':'available'},
 {'action_id':'mission_control.refresh_payload','label':'Refresh Mission Control payload','target_tab':'mission-control','handler':'refresh_mission_control','availability':'available'},
 {'action_id':'daily_board.generate_morning_briefing','label':'Generate morning briefing','target_tab':'daily-board','handler':'generate_daily_briefing','availability':'available'},
 {'action_id':'operations_dashboard.refresh','label':'Refresh operational command dashboard','target_tab':'operational-dashboard','handler':'operations_dashboard_refresh','availability':'available','note':'Rebuilds the Office dashboard from durable local runtime artifacts.'},
 {'action_id':'operations_dashboard.inspect_evidence','label':'Inspect dashboard evidence','target_tab':'operational-dashboard','handler':'operations_dashboard_inspect_evidence','availability':'available','requires_input':'evidence_path','note':'Drill-down only; reads existing local evidence under Estate root.'},
 {'action_id':'operations_surface.host_control','label':'Start/stop/restart Operations Runtime host','target_tab':'operational-activity','handler':'operations_host_control','availability':'available','requires_input':'host_action','note':'Actions: start, stop, restart, status. Delegates to OperationsRuntimeHost; no provider execution.'},
 {'action_id':'operations_surface.scheduler_control','label':'Enable/disable scheduler job or trigger event','target_tab':'operational-activity','handler':'operations_scheduler_control','availability':'available','requires_input':'scheduler_action,job_id,event_name','note':'Actions: enable, disable, trigger. State persists in operations scheduler artifacts.'},
 {'action_id':'operations_surface.extension_control','label':'Inspect/validate/enable background extension','target_tab':'operational-activity','handler':'operations_extension_control','availability':'available','requires_input':'extension_action,extension_id','note':'Actions: inspect, validate, dry-run, enable, disable. Uses committed extension configuration only.'},
 {'action_id':'operations_surface.watch_control','label':'Enable/disable/evaluate operational watch','target_tab':'operational-activity','handler':'operations_watch_control','availability':'available','requires_input':'watch_action,watch_id','note':'Actions: enable, disable, pause, evaluate. Evaluate is dry-run evidence inspection.'},
 {'action_id':'operations_surface.trigger_cycle','label':'Trigger one bounded operations cycle','target_tab':'operational-activity','handler':'operations_cycle_control','availability':'available','requires_input':'dry_run,mode,max_audit_requests','note':'Runs one existing OperationsRuntimeService cycle; does not bypass Traffic Controller constraints.'},
 {'action_id':'operations_surface.hold_control','label':'Place/release audit admission hold','target_tab':'operational-activity','handler':'operations_hold_control','availability':'available','requires_input':'hold_action,work_package,target','note':'Actions: hold, release. Delegates to merge discovery admission runtime.'},
 {'action_id':'operations_surface.inspect_evidence','label':'Inspect operations evidence','target_tab':'operational-activity','handler':'operations_inspect_evidence','availability':'available','requires_input':'evidence_path','note':'Reads an existing evidence file under the Estate root and returns truthful status.'},
 {'action_id':'orchestrator_intake.record_decision','label':'Record Orchestrator intake decision','target_tab':'operational-activity','handler':'record_orchestrator_intake_decision','availability':'available','requires_input':'intake_id,decision,decided_by','note':'Records a durable decision artifact; does not schedule or execute work.'},
 {'action_id':'operations_control.record_decision','label':'Record operations-control decision','target_tab':'operational-activity','handler':'record_operations_control_decision','availability':'available','requires_input':'decision_type,target_type,decided_by','note':'Writes an operations-control decision artifact; does not execute providers.'},
 {'action_id':'operational_activity.refresh','label':'Refresh operational activity','target_tab':'operational-activity','handler':'refresh_operational_activity','availability':'available'},
 {'action_id':'operational_activity.acknowledge_attention','label':'Acknowledge attention item','target_tab':'operational-activity','handler':'acknowledge_operational_activity','availability':'available','requires_input':'activity_id,acknowledged_by,reason','note':'Records local durable acknowledgement evidence; source activity is not falsified.'},
 {'action_id':'operational_activity.route_to_workspace','label':'Route to controlling workspace','target_tab':'operational-activity','handler':'route_operational_activity','availability':'available','requires_input':'activity_id,route_target'},
 {'action_id':'operational_activity.open_artifact','label':'Open related artifact','target_tab':'operational-activity','handler':'open_operational_artifact','availability':'available','requires_input':'artifact_path'},
 {'action_id':'operational_activity.filter','label':'Filter operational activity','target_tab':'operational-activity','handler':'filter_operational_activity','availability':'available','requires_input':'state,owner,priority,attention_required'},
 {'action_id':'operations_control.run_provider','label':'Run provider','target_tab':'operational-activity','availability':'gated','disabled_reason':'Provider execution is intentionally outside the Office traffic-controller panel.'},
 {'action_id':'ai_services.start_stop_load','label':'Legacy combined AI service control','target_tab':'ai-services-models','availability':'gated','disabled_reason':'Legacy approval workflow control is replaced by registered granular controls: ai_services.start, stop, restart, load_model, unload_model, inspect_state, or launch_local_interface.'},
]

def controls_for_tab(tab: str) -> list[dict[str, Any]]:
    return [dict(c) for c in ACTION_CONTROLS if c['target_tab'] == tab]

def execute_office_action(action_id: str, *, root=None, **params: Any) -> dict[str, Any]:
    base = _root(root)
    request_id = _request_id(params)
    params['request_id'] = request_id
    control = next((c for c in ACTION_CONTROLS if c['action_id'] == action_id), None)
    if not control:
        result = _blocked(action_id, action_id, 'unknown', 'office_command_surface.execute_office_action', f'No Office action is registered for {action_id}.', request_id=request_id)
        return _write_result(base, result).to_dict()
    if control.get('availability') != 'available':
        result = _blocked(action_id, control['label'], control['target_tab'], control.get('handler', 'gated_control'), control.get('disabled_reason') or 'Action is gated.', request_id=request_id)
        return _write_result(base, result).to_dict()
    try:
        result = HANDLERS[action_id](root=base, **params)
        result.request_id = request_id
    except Exception as exc:
        diag = _diagnostic(base, action_id, exc)
        result = OfficeActionResult(action_id, control['label'], request_id, control['target_tab'], 'failed', f'Action attempted and failed: {type(exc).__name__}: {exc}', control.get('handler') or action_id, diagnostics_path=diag)
    return _write_result(base, result).to_dict()
