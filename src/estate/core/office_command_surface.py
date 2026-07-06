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
})

ACTION_CONTROLS = [
 {'action_id':'ai_services.refresh_local_inventory','label':'Refresh local AI service inventory','target_tab':'ai-services-models','handler':'refresh_ai_services','availability':'available'},
 {'action_id':'validation.run_production_readiness','label':'Run production readiness refresh','target_tab':'validation','handler':'run_production_readiness','availability':'available','note':'Evidence is not institutional acceptance.'},
 {'action_id':'work_packages.refresh_assignment_queue','label':'Refresh assignment queue','target_tab':'work-packages','handler':'refresh_work_package_queue','availability':'available'},
 {'action_id':'work_packages.validate_selected','label':'Validate selected work package','target_tab':'work-packages','handler':'validate_selected_work_package','availability':'available','requires_input':'work_package_id'},
 {'action_id':'notifications.refresh_center','label':'Refresh notification center','target_tab':'notifications','handler':'refresh_notifications','availability':'available'},
 {'action_id':'notifications.local_acknowledge','label':'Acknowledge notification locally','target_tab':'notifications','handler':'local_ack_notification','availability':'available','requires_input':'notification_id','note':'Local state only; authoritative closure is unchanged.'},
 {'action_id':'alfred.request_briefing','label':'Request Alfred briefing','target_tab':'alfred','handler':'request_alfred_briefing','availability':'available'},
 {'action_id':'mission_control.refresh_payload','label':'Refresh Mission Control payload','target_tab':'mission-control','handler':'refresh_mission_control','availability':'available'},
 {'action_id':'daily_board.generate_morning_briefing','label':'Generate morning briefing','target_tab':'daily-board','handler':'generate_daily_briefing','availability':'available'},
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
