import argparse
import json
from pathlib import Path
from estate.core.ledger import create_change
from estate.core.residents import register_resident
from estate.core.registry import load_registry
from estate.core.services import list_services, list_capabilities, list_providers
from estate.core.discovery import observe_ai_environment, generate_discovery_report
from estate.core.provider_sync import sync_ollama_providers
from estate.core.discovery_catalog import load_discovery_catalog, sync_discovery_catalog_from_latest, format_discovery_catalog_report
from estate.core.discovery_cycle import run_discovery_cycle, format_discovery_cycle_report
from estate.core.discovery_service import get_discovery_service
from estate.core.service_layer import service_status, route_capability, alfred_capabilities, format_service_status, format_alfred_capabilities, service_readiness, format_service_readiness, capability_help, format_capability_help
from estate.core.alfred import plan_goal, create_job, list_jobs, format_plan, format_job, format_jobs, execute_job, format_execution_result, inspect_job, cancel_job, retry_job, get_execution_policy, format_job_inspection, format_execution_policy, get_job_result, format_job_result, run_task, format_task_result, alfred_status, format_alfred_status, create_request, list_requests, promote_request, format_requests, triage_requests, format_request_triage, alfred_briefing, format_alfred_briefing, cleanup_jobs, format_cleanup_result, artifact_index, format_artifact_index, estate_health_report, format_estate_health_report, get_job_result, format_job_result, run_task, format_task_result, alfred_status, format_alfred_status, create_request, list_requests, promote_request, format_requests, triage_requests, format_request_triage, alfred_briefing, format_alfred_briefing, cleanup_jobs, format_cleanup_result, artifact_index, format_artifact_index, estate_health_report, format_estate_health_report
from estate.core.audit import print_audit_report
from estate.core.collaboration_ops import run_routing_engine, watch_worker_inboxes, format_routing_report, format_inbox_summary
from estate.core.collaboration_messages import acknowledge_message, create_reply
from estate.core.collaboration_events import generate_event_summary, format_event_summary
from estate.core.operations_board import generate_operations_board, format_operations_board_summary
from estate.core.daily_board_integration import generate_daily_board_integration, format_daily_board_integration_summary
from estate.core.capability_lifecycle import generate_capability_lifecycle_report, format_capability_lifecycle_summary
from estate.core.estate_capability_registry import generate_estate_capability_registry, format_estate_capability_registry_summary
from estate.core.capability_dependency_visualization import generate_capability_dependency_visualization, format_capability_dependency_visualization_summary
from estate.core.capability_gap_report import generate_capability_gap_report, format_capability_gap_summary
from estate.core.estate_service_catalog import generate_estate_service_catalog, format_estate_service_catalog_summary
from estate.core.service_dependency_matrix import generate_service_dependency_matrix, format_service_dependency_matrix_summary
from estate.core.service_health_registry import generate_service_health_registry, format_service_health_registry_summary
from estate.core.service_status_board import generate_service_status_board, format_service_status_board_summary
from estate.core.operator_activity_stream import generate_operator_activity_stream, format_operator_activity_stream_summary
from estate.core.operations_notification_center import generate_operations_notification_center, acknowledge_operations_notification, format_operations_notification_center_summary
from estate.core.operational_validation import generate_operational_validation_report, format_operational_validation_summary
from estate.core.steward_dashboard import generate_steward_dashboard, format_steward_dashboard_summary
from estate.core.dependency_graph import generate_dependency_graph, format_dependency_graph_summary
from estate.core.audit_runtime import save_audit_report, summarize_audit_artifact, format_audit_summary
from estate.core.mailbox_index import generate_mailbox_index, mailbox_index_summary
from estate.core.personnel_identity import resolve_personnel_identity, format_resolution
from estate.core.check_updates import generate_check_updates, format_check_updates
from estate.core.mailbox_sync_duty import generate_mailbox_sync_duty, format_mailbox_sync_duty
from estate.core.local_operational_validation import generate_local_operational_validation_run, format_local_operational_validation_summary
from estate.core.onboarding_manifest import check_onboarding_manifests, format_onboarding_manifest_check
from estate.core.hr_onboarding import run_employee_onboarding, format_onboarding_result
from estate.core.work_package_handoff import list_pending_handoffs, format_handoff_list
from estate.core.institutional_search import search_institutional_index, format_search_report
from estate.core.global_search_command_palette import search_global_palette, execute_registered_command, format_palette_report
from estate.core.document_registry import load_document_registry, format_document_registry
from estate.core.notification_router import generate_notification_router_report, format_notification_router_report, route_notification_events
from estate.core.morning_briefing import generate_morning_briefing, format_morning_briefing
from estate.core.gotify_adapter import send_gotify_recall, format_gotify_delivery_report
from estate.core.worker_runtime_heartbeat import create_worker_heartbeat, generate_worker_runtime_summary, format_worker_runtime_summary
from estate.core.worker_runtime_monitor import generate_worker_runtime_monitor, format_worker_runtime_monitor
from estate.core.validation_observations import append_observation, load_observations, update_observation_status, render_markdown_log
from estate.core.validation_metrics_dashboard import generate_validation_metrics_dashboard, format_validation_metrics_summary
from estate.core.validation_handoff_artifact_workflow import generate_validation_handoff_artifact_workflow, format_validation_handoff_summary
from estate.core.work_package_validation import validate_work_package, format_validation_markdown
from estate.core.production_readiness_validation import generate_production_readiness_report, format_production_readiness_markdown
from estate.core.codex_bridge import load_bridge_request, run_codex_bridge_request, format_codex_bridge_result
from estate.core.execution_activity import generate_execution_activity_surface, format_execution_activity_report, format_execution_activity_summary
from estate.core.execution_provider_adapter_runtime import load_adapter_request as load_adapter_contract_request, run_dry_run_adapter, validate_adapter_request_file
from estate.core.codex_bridge_execution_provider_adapter import run_codex_bridge_adapter_dry_run, CodexBridgeExecutionProviderAdapter
from estate.core.execution_adapter_handoff_runtime import inspect_handoff, prepare_handoff, validate_handoff, dry_run_handoff
from estate.core.codex_live_execution_gate import CodexLiveExecutionGate
from estate.core.execution_result_reconciliation_runtime import inspect_reconciliation, reconcile_result, format_reconciliation_report
from estate.core.execution_attempt_runtime import ExecutionAttemptRuntime
from estate.core.provider_routing_recommendations import explain_provider_routing_recommendation, evaluate_provider_routing_recommendation
from estate.core.provider_routing_recommendations_runtime import evaluate_recommendation_file, load_recommendation_request
from estate.core.execution_dispatch import (
    block_dispatch_item,
    cancel_dispatch_item,
    complete_dispatch_item,
    enqueue_dispatch_request,
    format_dispatch_item,
    format_execution_dispatch_report,
    format_execution_dispatch_summary,
    generate_current_dispatch_snapshot,
    inspect_dispatch_item,
    list_dispatch_items,
    load_dispatch_request,
    mark_dispatch_attention,
    prepare_codex_bridge_handoff,
    update_dispatch_state,
)
from estate.core.operational_readiness_dashboard import generate_operational_readiness_dashboard, format_operational_readiness_summary
from estate.core.steward_presence import generate_steward_presence_state, format_steward_presence_state
from estate.core.assignment_queue import generate_assignment_queue, format_assignment_queue_markdown
from estate.core.post_merge_audit_processor import PostMergeAuditProcessor
from estate.core.autonomous_work_queue_scheduler import generate_autonomous_work_queue_scheduler, format_autonomous_work_queue_scheduler
from estate.core.autonomous_operations_audit import append_autonomous_operations_audit, format_autonomous_operations_audit
from estate.core.steward_command_center import generate_command_center, serve_command_center
from estate.core.operations_center_bootstrap import operations_center_start, operations_center_status, operations_center_stop, format_operations_center_bootstrap
from estate.core.operations_center_workspace_profiles import resolve_workspace_profile, save_workspace_profile
from estate.core.operations_center_settings import load_operations_center_settings, save_operations_center_settings
from estate.core.decision_queue import generate_decision_queue, format_decision_queue_markdown
from estate.core.resident_presence import build_resident_presence, filter_resident, format_resident_presence
from estate.core.resident_conversation_sessions import create_session, list_sessions, load_session, format_session_list
from estate.core.alfred_duty import run_alfred_duty, format_alfred_duty
from estate.core.helen_duty import run_helen_duty, format_helen_duty
from estate.core.resident_authority import check_authority, list_authority, format_authority_decision
from estate.core.resident_interaction import process_chat, load_history, forget_conversation, resident_surface, alfred_llm_diagnostic
from estate.core.paths import ESTATE_ROOT, LEDGER_PATH, DEVLOG_PATH
from estate.core.planning_provider import PlanningProviderRequest
from estate.core.planning_provider_registry import default_planning_provider_registry
from estate.core.planning_provider_runtime import PlanningProviderRuntimeWriter
from estate.core.operational_events import OperationalEvent
from estate.core.operational_status import record_operational_event, format_summary_for_cli
from estate.core.orchestrator_intake import OrchestratorIntakeRequest
from estate.core.orchestrator_intake_runtime import OrchestratorIntakeRuntime, format_queue_for_cli, safe_summary
from estate.core.orchestrator_intake_decisions import OrchestratorIntakeDecisionRuntime
from estate.core.orchestrator_schedule_runtime import OrchestratorScheduleRuntime, format_schedule_queue_for_cli
from estate.core.provider_catalog import load_provider_catalog, write_office_status, format_provider_list
from estate.core.provider_health import ProviderHealthRecord, write_health_record, generate_provider_health_summary, format_provider_health_summary
from estate.core.provider_capacity import ProviderCapacityRecord, write_capacity_record
from estate.core.worker_assignment_runtime import WorkerAssignmentRuntime, format_assignment_board
from estate.core.orchestrator_cycle import OrchestratorCycleRuntime, format_cycle_summary, format_dispatch_queue
from estate.core.operations_manager import OperationsDecision
from estate.core.operations_control_runtime import OperationsControlRuntime, format_operations_review, format_operations_decisions
from estate.core.alfred_runtime import build_alfred_event, render_alfred_briefing
from estate.core.background_operations_runtime import BackgroundOperationsRuntime, format_background_operations_report
from estate.core.operational_targets_runtime import OperationalTargetRuntime
from estate.core.operational_target_resolution import OperationalTargetResolver
from estate.core.operational_target_validation_binding import OperationalTargetValidationBinder
from estate.core.operations_runtime_service import OperationsRuntimeService, OperationsRuntimeLockError
from estate.core.merge_discovery_runtime import MergeDiscoveryRuntime

def _repo_path(rel):
    return (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd()) / rel




def cmd_operational_targets(args):
    try:
        rt = OperationalTargetRuntime()
        action = args.operational_targets_action
        if action == "list": payload = rt.list_payload()
        elif action == "resolve": payload = OperationalTargetResolver().resolve(args.target).to_dict()
        elif action == "binding": payload = OperationalTargetValidationBinder().bind(args.target).to_dict()
        elif action == "aliases": payload = {"aliases": {t.target_id: t.aliases for t in rt.load_targets()}}
        elif action == "show": payload = rt.get(args.target).to_dict()
        elif action == "status": payload = rt.write_status()
        else:
            state = {"enable":"enabled","pause":"paused","resume":"enabled","disable":"disabled","retire":"retired","import-candidate":"import_candidate"}[action]
            payload = rt.transition(args.target, state)
        print(json.dumps(payload, indent=2, sort_keys=True) if getattr(args, "json", False) else json.dumps(payload, indent=2, sort_keys=True))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Operational targets failed: {exc}")
        raise SystemExit(1)

def cmd_background_operations(args):
    try:
        runtime = BackgroundOperationsRuntime()
        action = args.background_operations_action
        if action == "cycle":
            payload = runtime.run_cycle(write=True)
            if getattr(args, "json", False):
                print(json.dumps(payload, indent=2, sort_keys=True))
            else:
                print(format_background_operations_report(payload))
        elif action == "watches":
            payload = {"watches": [w.to_dict() for w in runtime.load_watches()]}
            print(json.dumps(payload, indent=2, sort_keys=True) if getattr(args, "json", False) else "\n".join(w["watch_id"] for w in payload["watches"]))
        elif action == "requests":
            payload = {"requests": runtime.list_requests()}
            print(json.dumps(payload, indent=2, sort_keys=True) if getattr(args, "json", False) else "\n".join(r.get("request_id", "unknown") for r in payload["requests"]))
        elif action == "status":
            payload = runtime.load_status()
            print(json.dumps(payload, indent=2, sort_keys=True) if getattr(args, "json", False) else format_background_operations_report(payload))
        elif action == "report":
            print(format_background_operations_report(runtime.load_status()))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Background operations failed: {exc}")
        raise SystemExit(1)

def cmd_merge_discovery(args):
    runtime = MergeDiscoveryRuntime()
    action = args.merge_discovery_action
    target = getattr(args, "target", "estate-main")
    if action == "scan":
        payload = runtime.scan(target=target, max_commits=getattr(args, "max_commits", 100))
    elif action == "replay":
        payload = runtime.replay(target=target, max_commits=getattr(args, "max_commits", 50))
    elif action == "status":
        payload = runtime.status(target=target)
    elif action == "candidates":
        payload = runtime.candidates(target=target)
    else:
        raise SystemExit(1)
    print(json.dumps(payload, indent=2, sort_keys=True) if getattr(args, "json", False) else json.dumps(payload, indent=2, sort_keys=True))

def cmd_post_merge_audit(args):
    processor = PostMergeAuditProcessor()
    action = args.post_merge_audit_action
    if action == "process-next":
        payload = processor.process_next()
    elif action == "process-all":
        payload = processor.process_all(max_count=args.max)
    elif action == "demonstrate":
        payload = processor.demonstrate(args.work_package, pr=args.pr)
    elif action == "status":
        payload = processor.summary()
    else:
        raise SystemExit(1)
    print(json.dumps(payload, indent=2, sort_keys=True) if getattr(args, "json", False) else json.dumps(payload, indent=2, sort_keys=True))

def cmd_operations_runtime(args):
    try:
        service = OperationsRuntimeService()
        action = args.operations_runtime_action
        if action == "run-once":
            mode = "discover-merges-and-process-audits-and-ring2" if getattr(args, "discover_merges", False) and getattr(args, "process_audits_and_ring2", False) else ("discover-merges-and-process-audits" if getattr(args, "discover_merges", False) and getattr(args, "process_audits", False) else ("discover-merges" if getattr(args, "discover_merges", False) else ("process-audits-and-ring2" if getattr(args, "process_audits_and_ring2", False) else ("process-audits" if getattr(args, "process_audits", False) else "observe-only"))))
            payload = service.run_once(dry_run=getattr(args, "dry_run", False), mode=mode)
            print(json.dumps(payload, indent=2, sort_keys=True) if getattr(args, "json", False) else json.dumps(payload, indent=2, sort_keys=True))
        elif action == "start":
            mode = "discover-merges-and-process-audits-and-ring2" if getattr(args, "discover_merges", False) and getattr(args, "process_audits_and_ring2", False) else ("discover-merges-and-process-audits" if getattr(args, "discover_merges", False) and getattr(args, "process_audits", False) else ("discover-merges" if getattr(args, "discover_merges", False) else ("process-audits-and-ring2" if getattr(args, "process_audits_and_ring2", False) else ("process-audits" if getattr(args, "process_audits", False) else "observe-only"))))
            payload = service.start(max_cycles=args.max_cycles, interval_seconds=args.interval_seconds, dry_run=getattr(args, "dry_run", False), mode=mode)
            print(json.dumps(payload, indent=2, sort_keys=True) if getattr(args, "json", False) else json.dumps(payload, indent=2, sort_keys=True))
        elif action == "status":
            payload = service.status()
            print(json.dumps(payload, indent=2, sort_keys=True) if getattr(args, "json", False) else service.report())
        elif action == "request-stop":
            payload = service.request_stop()
            print(json.dumps(payload, indent=2, sort_keys=True) if getattr(args, "json", False) else "Operations Runtime stop requested")
        elif action == "report":
            print(service.report())
    except OperationsRuntimeLockError as exc:
        print(f"Operations runtime blocked: {exc}")
        raise SystemExit(2)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Operations runtime failed: {exc}")
        raise SystemExit(1)

def cmd_operations_review(args):
    try:
        review, paths = OperationsControlRuntime().generate_review(classification=args.classification, write=True)
        if getattr(args, "json", False):
            print(json.dumps(review.to_dict(), indent=2, sort_keys=True))
        else:
            print(format_operations_review(review, paths))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Operations review failed: {exc}")
        raise SystemExit(1)

def cmd_operations_decide(args):
    try:
        decision = OperationsDecision.create(decided_by=args.decided_by, decision_type=args.decision_type, target_type=args.target_type, target_id=args.target_id, classification=args.classification, priority=args.priority, reason=args.reason, next_state=args.next_state, assignment_label=args.assignment_label, provider_id=args.provider_id, worker_id=args.worker_id, seat_id=args.seat_id, requires_boundary_review=args.requires_boundary_review, requires_steward_attention=args.requires_steward_attention, summary_safe=args.summary_safe)
        paths = OperationsControlRuntime().record_decision(decision)
        print(f"Operations decision recorded: {decision.decision_id}")
        print(f"Type: {decision.decision_type}")
        print(f"Target: {decision.target_type}:{decision.target_id or ''}")
        if decision.assignment_label:
            print(f"Assignment label: {decision.assignment_label}")
        print(f"Decision: {paths['decision']}")
        print(f"Summary: {paths['summary_json']}")
    except (OSError, ValueError) as exc:
        print(f"Operations decision failed: {exc}")
        raise SystemExit(1)

def cmd_operations_decisions_list(args):
    try:
        decisions = OperationsControlRuntime().list_decisions()
        if getattr(args, "json", False):
            print(json.dumps([d.to_dict() for d in decisions], indent=2, sort_keys=True))
        else:
            print(format_operations_decisions(decisions))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Operations decisions list failed: {exc}")
        raise SystemExit(1)

def cmd_worker_assignment_create(args):
    try:
        metadata = {"summary_safe": args.summary_safe}
        runtime = WorkerAssignmentRuntime()
        record, paths = runtime.create_assignment(
            assigned_by=args.assigned_by, assigned_to=args.assigned_to, assignment_label=args.assignment_label or args.assigned_to,
            worker_id=args.worker_id, worker_role=args.worker_role, provider_id=args.provider_id, provider_type=args.provider_type, seat_id=args.seat_id, profile_id=args.profile_id,
            work_package_id=args.work_package_id, work_package_path=args.work_package_path, intake_id=args.intake_id, schedule_id=args.schedule_id, classification=args.classification,
            priority=args.priority, state=args.state, mission=args.mission, summary=args.summary or args.mission, expected_outputs=args.expected_output or [], validation_required=not args.no_validation_required,
            requires_attention=args.requires_attention, blocked_reason=args.blocked_reason, metadata=metadata,
        )
        print(f"Worker assignment created: {record.assignment_id}")
        print(f"State: {record.state}")
        print(f"Record: {paths['record']}")
        print(f"Board: {paths['board']}")
    except (OSError, ValueError) as exc:
        print(f"Worker assignment create failed: {exc}")
        raise SystemExit(1)

def cmd_worker_assignment_update(args):
    try:
        metadata = {"summary_safe": args.summary_safe} if args.summary_safe else None
        record, paths = WorkerAssignmentRuntime().update_assignment(args.assignment_id, state=args.state, blocked_reason=args.blocked_reason, requires_attention=args.requires_attention, metadata=metadata)
        print(f"Worker assignment updated: {record.assignment_id}")
        print(f"State: {record.state}")
        print(f"Record: {paths['record']}")
        print(f"Board: {paths['board']}")
    except (OSError, ValueError) as exc:
        print(f"Worker assignment update failed: {exc}")
        raise SystemExit(1)

def cmd_worker_assignment_list(args):
    try:
        board = WorkerAssignmentRuntime().generate_board(write=True)
        if getattr(args, "json", False):
            print(json.dumps(board, indent=2, sort_keys=True))
        else:
            print(format_assignment_board(board))
    except (OSError, ValueError) as exc:
        print(f"Worker assignment list failed: {exc}")
        raise SystemExit(1)

def cmd_providers_list(args):
    try:
        catalog = load_provider_catalog()
        write_office_status(catalog)
        if getattr(args, "json", False):
            print(json.dumps(catalog.status_export(), indent=2, sort_keys=True))
        else:
            print(format_provider_list(catalog))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"Provider catalog load failed: {exc}")
        raise SystemExit(1)

def cmd_providers_show(args):
    try:
        catalog = load_provider_catalog()
        provider = catalog.get_provider(args.provider_id)
        write_office_status(catalog)
        if getattr(args, "json", False):
            print(json.dumps(provider.to_dict(), indent=2, sort_keys=True))
        else:
            print(f"Provider: {provider.provider_id}")
            print(f"Name: {provider.display_name}")
            print(f"Type: {provider.provider_type}")
            print(f"Implementation: {provider.implementation_kind}")
            print(f"Status: {provider.status}")
            print(f"Capabilities: {', '.join(provider.capabilities)}")
            print(f"Classification ceiling: {provider.classification_ceiling}")
    except KeyError as exc:
        print(str(exc))
        raise SystemExit(1)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"Provider catalog show failed: {exc}")
        raise SystemExit(1)

def cmd_providers_find(args):
    try:
        catalog = load_provider_catalog()
        providers = catalog.providers_with_capability(args.capability)
        write_office_status(catalog)
        if getattr(args, "json", False):
            print(json.dumps([provider.to_dict() for provider in providers], indent=2, sort_keys=True))
        else:
            if not providers:
                print(f"No providers found for capability: {args.capability}")
            for provider in providers:
                print(f"{provider.provider_id} | {provider.provider_type} | {provider.status}")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"Provider catalog find failed: {exc}")
        raise SystemExit(1)

def cmd_providers_health_set(args):
    try:
        metadata = {"summary_safe": args.summary_safe}
        record = ProviderHealthRecord.create(provider_id=args.provider_id, status=args.status, reported_by=args.reported_by, message=args.message, classification=args.classification, source=args.source, metadata=metadata)
        paths = write_health_record(record, force=args.force)
        print(f"Provider health recorded: {record.provider_id} -> {record.status}")
        if paths.get("warning"):
            print(f"Warning: {paths['warning']}")
        print(f"Record: {paths['record']}")
        print(f"Summary: {paths['summary_json']}")
    except (OSError, ValueError) as exc:
        print(f"Provider health set failed: {exc}")
        raise SystemExit(1)

def cmd_providers_capacity_set(args):
    try:
        metadata = {"summary_safe": args.summary_safe}
        record = ProviderCapacityRecord.create(provider_id=args.provider_id, capacity_state=args.capacity_state, reported_by=args.reported_by, classification=args.classification, active_jobs=args.active_jobs, max_jobs=args.max_jobs, queue_depth=args.queue_depth, quota_remaining=args.quota_remaining, message=args.message, metadata=metadata)
        paths = write_capacity_record(record, force=args.force)
        print(f"Provider capacity recorded: {record.provider_id} -> {record.capacity_state}")
        if paths.get("warning"):
            print(f"Warning: {paths['warning']}")
        print(f"Record: {paths['record']}")
        print(f"Summary: {paths['summary_json']}")
    except (OSError, ValueError) as exc:
        print(f"Provider capacity set failed: {exc}")
        raise SystemExit(1)

def cmd_providers_health_summary(args):
    try:
        summary = generate_provider_health_summary(write=True)
        if getattr(args, "json", False):
            print(json.dumps(summary, indent=2, sort_keys=True))
        else:
            print(format_provider_health_summary(summary))
    except (OSError, ValueError) as exc:
        print(f"Provider health summary failed: {exc}")
        raise SystemExit(1)

def cmd_orchestrator_intake_submit(args):
    try:
        data = json.loads(Path(args.request).read_text(encoding="utf-8"))
        request = OrchestratorIntakeRequest.from_dict(data)
        status, paths = OrchestratorIntakeRuntime().submit(request)
        label = "BLOCKED" if status.state == "blocked" else "PENDING"
        print(f"Orchestrator intake {label}: {status.intake_id}")
        print(f"State: {status.state}")
        print(f"Summary: {safe_summary(status.to_dict())}")
        if status.blocked_reason:
            print(f"Blocked reason: {status.blocked_reason}")
        print(f"Artifact: {paths['artifact']}")
        print(f"Queue status: {paths['queue']}")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"Orchestrator intake submit failed: {exc}")
        raise SystemExit(1)

def cmd_orchestrator_intake_list(args):
    queue = OrchestratorIntakeRuntime().queue_state()
    if getattr(args, "json", False):
        print(json.dumps(queue, indent=2, sort_keys=True))
    else:
        print(format_queue_for_cli(queue))

def cmd_orchestrator_intake_decide(args):
    try:
        metadata = {"summary_safe": args.summary_safe}
        if args.boundary_review_completed:
            metadata["boundary_review_completed"] = True
        decision, paths = OrchestratorIntakeDecisionRuntime().decide(intake_id=args.intake_id, decision=args.decision, decided_by=args.decided_by, reason=args.reason, metadata=metadata)
        print(f"Orchestrator intake decision recorded: {decision.decision_id}")
        print(f"Intake: {decision.intake_id}")
        print(f"Decision: {decision.decision}")
        print(f"Next state: {decision.next_state}")
        print(f"Decision artifact: {paths['decision']}")
        print(f"Queue status: {paths['queue']}")
        if decision.requires_boundary_review:
            print("Boundary review required before approval can proceed.")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"Orchestrator intake decide failed: {exc}")
        raise SystemExit(1)

def cmd_orchestrator_schedule(args):
    try:
        runtime = OrchestratorScheduleRuntime()
        record, paths = runtime.schedule(
            intake_id=args.intake_id,
            request_path=Path(args.request) if args.request else None,
            scheduled_by=args.scheduled_by,
            explicit_defer=args.defer,
        )
        print(f"Orchestrator schedule {record.state.upper()}: {record.schedule_id}")
        print(f"Intake: {record.intake_id}")
        print(f"State: {record.state}")
        if record.blocked_reason:
            print(f"Blocked reason: {record.blocked_reason}")
        if (record.metadata or {}).get("deferred_reason"):
            print(f"Deferred reason: {record.metadata['deferred_reason']}")
        print(f"Artifact: {paths['artifact']}")
        print(f"Queue status: {paths['queue']}")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"Orchestrator schedule failed: {exc}")
        raise SystemExit(1)

def cmd_orchestrator_schedule_list(args):
    queue = OrchestratorScheduleRuntime().queue_state()
    if getattr(args, "json", False):
        print(json.dumps(queue, indent=2, sort_keys=True))
    else:
        print(format_schedule_queue_for_cli(queue))

def cmd_orchestrator_cycle(args):
    try:
        if args.dry_run == args.single:
            print("Specify exactly one of --dry-run or --single")
            raise SystemExit(1)
        state = OrchestratorCycleRuntime().run_cycle(dry_run=args.dry_run)
        print(format_cycle_summary(state))
        if state.errors:
            raise SystemExit(2)
    except (OSError, ValueError) as exc:
        print(f"Orchestrator cycle failed: {exc}")
        raise SystemExit(1)

def cmd_orchestrator_dispatch_list(args):
    try:
        queue = OrchestratorCycleRuntime().dispatch_queue()
        if getattr(args, "json", False):
            print(json.dumps(queue, indent=2, sort_keys=True))
        else:
            print(format_dispatch_queue(queue))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"Orchestrator dispatch list failed: {exc}")
        raise SystemExit(1)

def cmd_planning_provider_run(args):
    try:
        request_data = json.loads(Path(args.request).read_text(encoding="utf-8"))
        request = PlanningProviderRequest.from_dict(request_data)
        provider = default_planning_provider_registry().resolve(request.provider_id)
        response = provider.run(request)
        artifact_paths = PlanningProviderRuntimeWriter().write_all(request, response)
        print(f"Planning provider: {response.provider_id}")
        print(f"Request: {response.request_id}")
        print(f"Status: {response.status}")
        print(f"Summary: {response.summary}")
        print(f"Result artifact: {artifact_paths['result']}")
        if response.errors:
            print("Errors: " + "; ".join(response.errors))
        if response.status in {"blocked", "failed"}:
            raise SystemExit(2)
    except (OSError, json.JSONDecodeError, ValueError, KeyError) as exc:
        print(f"Planning provider run failed: {exc}")
        raise SystemExit(1)

def cmd_operations_event_record(args):
    try:
        event_data = json.loads(Path(args.event).read_text(encoding="utf-8"))
        event = OperationalEvent.from_dict(event_data, allow_extension_event_types=args.allow_extension_event_type)
        paths = record_operational_event(event, allow_extension_event_types=args.allow_extension_event_type)
        print(f"Operational event recorded: {event.event_id}")
        print(f"Activity state: {event.state}")
        print(f"Event log: {paths['event_log']}")
        print(f"Latest status: {paths['latest']}")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"Operational event record failed: {exc}")
        raise SystemExit(1)

def cmd_operations_status_summary(args):
    print(format_summary_for_cli())

def cmd_work_package_ranges(args):
    path = _repo_path("collaboration/work_packages/work_package_range_ledger.json")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for row in payload.get("ranges", []):
            print(f"{row.get('start')}..{row.get('end')} | {row.get('owner')} | {row.get('status')}")

def cmd_workstream(args):
    manifest = _repo_path(f"collaboration/workstreams/{args.id}/install_manifest.json")
    example = _repo_path(f"collaboration/workstreams/{args.id}/install_manifest.example.json")
    path = manifest if manifest.exists() else example
    if args.action == "inspect":
        if not path.exists():
            payload = {"work_package_id": args.id, "manifest_status": "missing", "expected_path": str(manifest.relative_to(_repo_path('.'))).replace('\\','/')}
        else:
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["manifest_status"] = "found"
            payload["manifest_path"] = str(path.relative_to(_repo_path('.'))).replace('\\','/')
    else:
        required = ["work_package_id", "workstream_mode", "staged_artifact_paths", "intended_final_install_paths", "files_expected_to_be_modified_during_install", "validation_commands", "rollback_notes", "dependency_assumptions", "conflict_risks", "authority_and_review_requirements", "staged_work_is_installed"]
        payload = {"work_package_id": args.id, "manifest_path": None, "validation_status": "failed", "missing_fields": required}
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            missing = [key for key in required if key not in data]
            payload = {"work_package_id": args.id, "manifest_path": str(path.relative_to(_repo_path('.'))).replace('\\','/'), "validation_status": "passed" if not missing and data.get("staged_work_is_installed") is False else "failed", "missing_fields": missing, "staged_work_is_installed": data.get("staged_work_is_installed")}
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(payload)

def print_table(items, fields):
    if not items:
        print("No records.")
        return
    for item in items:
        print(" | ".join(str(item.get(field, "")) for field in fields))


def cmd_model_control(args):
    from estate.model_control.cli import handle
    handle(args)

def cmd_resident_chat(args):
    if args.action == "send":
        payload = process_chat(args.resident, args.message, session_id=args.session, action=args.resident_action or "summarize")
    elif args.action == "history":
        payload = load_history(args.resident, session_id=args.session, include_forgotten=args.include_forgotten)
    else:
        payload = forget_conversation(args.session, turn_id=args.turn, memory_status=args.memory_status, reason=args.reason)
    if getattr(args, "json", False):
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))

def cmd_resident_interaction_surface(args):
    payload = resident_surface(args.resident)
    if getattr(args, "json", False):
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"{payload['resident_display_name']} ({payload['resident_id']})")
        print(f"API standard: {payload['resident_api_standard_version']}")
        print(f"Implementation: {payload['resident_implementation_version']}")
        print("Capabilities:")
        for cap in payload.get('capabilities', []):
            print(f"- {cap.get('id')} | {cap.get('implementation_status')} | {cap.get('authority_category')} | approval={cap.get('required_approval_level')}")
        print(f"Extensions: {payload['extension_mechanism']['proposal_template']}")

def cmd_alfred_llm_diagnostics(args):
    payload = alfred_llm_diagnostic(write=True)
    if getattr(args, "json", False):
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Alfred expected provider: {payload.get('expected_provider')}")
        print(f"Configuration source: {payload.get('configuration_source')}")
        print(f"Provider reachable: {payload.get('provider_reachable')}")
        print(f"Failure reason: {payload.get('failure_reason') or 'none'}")
        print(f"Recovery hint: {payload.get('recovery_hint')}")
        print(f"Diagnostic artifact: {payload.get('diagnostic_path')}")

def cmd_change(args):
    ec_id = create_change(args.title, args.summary, args.status, args.classification)
    print(f"Created {ec_id}: {args.title}")

def cmd_resident(args):
    res_id, ec_id = register_resident(
        name=args.name,
        department=args.department,
        office=args.office,
        role=args.role,
        classification=args.classification
    )
    print(f"Created {res_id}")
    print(f"Logged {ec_id}")

def cmd_status(args):
    print("Estate Core Status")
    print(f"Root: {ESTATE_ROOT}")
    print(f"Ledger: {LEDGER_PATH.exists()} - {LEDGER_PATH}")
    print(f"Devlog: {DEVLOG_PATH.exists()} - {DEVLOG_PATH}")
    print(f"Registered residents: {len(load_registry('residents'))}")
    print(f"Registered services: {len(load_registry('services'))}")
    print(f"Registered capabilities: {len(load_registry('capabilities'))}")
    print(f"Registered providers: {len(load_registry('providers'))}")

def cmd_list_residents(args):
    print_table(load_registry("residents"), ["id", "name", "department", "office"])

def cmd_services(args):
    services = list_services()
    if getattr(args, "json", False):
        import json
        print(json.dumps(services, indent=2, sort_keys=True))
    else:
        print_table(services, ["id", "name", "status", "owner", "resident"])

def cmd_capabilities(args):
    capabilities = list_capabilities()
    if getattr(args, "json", False):
        import json
        print(json.dumps(capabilities, indent=2, sort_keys=True))
    else:
        print_table(capabilities, ["id", "name", "category", "status", "location"])

def cmd_providers(args):
    print_table(list_providers(), ["id", "name", "service", "status", "location"])

def cmd_discovery_refresh(args):
    service = get_discovery_service()
    result = service.refresh()

    if getattr(args, "json", False):
        import json
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(service.format_refresh_report(result))

    if not result.get("ok"):
        raise SystemExit(1)

def cmd_discovery_catalog(args):
    service = get_discovery_service()
    catalog = service.catalog(refresh=getattr(args, "refresh", False))

    if getattr(args, "json", False):
        import json
        print(json.dumps(catalog, indent=2, sort_keys=True))
    else:
        print(service.catalog_report(refresh=False))

def cmd_discovery_status(args):
    service = get_discovery_service()
    status = service.status()

    if getattr(args, "json", False):
        import json
        print(json.dumps(status, indent=2, sort_keys=True))
    else:
        print("=========================================")
        print("Estate Discovery Status")
        print("=========================================")
        for key, value in status.items():
            print(f"{key}: {value}")

def cmd_discovery_report(args):
    if getattr(args, "json", False):
        import json
        from estate.core.paths import ESTATE_ROOT
        latest = ESTATE_ROOT / "runtime" / "discovery" / "ai_environment_latest.json"
        print(json.dumps(json.loads(latest.read_text(encoding="utf-8")), indent=2))
    else:
        print(generate_discovery_report())

def cmd_discover(args):
    result = run_discovery_cycle()

    if getattr(args, "json", False):
        import json
        print(json.dumps(result["metrics"], indent=2, sort_keys=True))
    else:
        print(format_discovery_cycle_report(result))

    if not result["ok"]:
        raise SystemExit(1)

def cmd_discover_ai(args):
    observations, out = observe_ai_environment()
    print(f"Wrote observation: {out}")
    print(f"AI_HOME exists: {observations['exists']['ai_home']}")
    print(f"Python envs: {', '.join(observations['python_envs']) if observations['python_envs'] else '(none)'}")
    print(f"TTS items: {', '.join(observations['tts_items']) if observations['tts_items'] else '(none)'}")
    print(f"Tools: {', '.join(observations['tool_items']) if observations['tool_items'] else '(none)'}")
    print(f"Model categories: {', '.join(observations['model_categories']) if observations['model_categories'] else '(none)'}")
    if observations.get("ollama", {}).get("running"):
        print("Ollama: running")
        for model in observations["ollama"].get("models", []):
            print(f"Ollama model: {model['name']} | {model['id']} | {model['size']} | {model['modified']}")



def cmd_notification_router(args):
    payload = generate_notification_router_report()
    if getattr(args, "json", False):
        import json
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(format_notification_router_report(payload))



def cmd_gotify_send_test(args):
    sample_event = {
        "id": "gotify-send-test",
        "source": "alfred",
        "event_type": "recall_candidate",
        "requested_by": "alfred",
        "alfred_validated": True,
        "recall_reason": "operational",
        "priority": "urgent",
        "action": "prepare_recall_delivery",
        "triggering_artifact": "estate.cli.main",
        "blocked_decision": "Gotify adapter validation requested.",
        "steward_only_rationale": "Dry-run validates Steward recall delivery plumbing only.",
        "options_or_recommended_next_action": "Recall Steward for decision if this were a real event.",
        "consequence_of_waiting": "No consequence during dry-run validation.",
        "continuity_assessment": "Unrelated Estate work may continue.",
        "supporting_references": ["collaboration/work_packages/pending/WP-0036_SERIES_gotify_adapter_v1.md"],
    }
    notification = route_notification_events([sample_event], write=False)["notifications"][0]
    payload = send_gotify_recall(notification, dry_run=args.dry_run)
    if getattr(args, "json", False):
        import json
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(format_gotify_delivery_report(payload))
    if not payload.get("ok"):
        raise SystemExit(1)

def cmd_estate_health(args):
    payload = estate_health_report()
    if getattr(args, "json", False):
        import json
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(format_estate_health_report(payload))


def cmd_alfred_artifacts(args):
    payload = artifact_index()
    if getattr(args, "json", False):
        import json
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(format_artifact_index(payload))


def cmd_alfred_cleanup(args):
    result = cleanup_jobs(keep=args.keep)
    if getattr(args, "json", False):
        import json
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(format_cleanup_result, artifact_index, format_artifact_index, estate_health_report, format_estate_health_report(result))


def cmd_alfred_briefing(args):
    payload = alfred_briefing()
    if getattr(args, "json", False):
        import json
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(format_alfred_briefing(payload))


def cmd_alfred_triage(args):
    payload = triage_requests()
    if getattr(args, "json", False):
        import json
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(format_request_triage(payload))


def cmd_alfred_request(args):
    request = create_request(args.goal)
    if getattr(args, "json", False):
        import json
        print(json.dumps(request, indent=2, sort_keys=True))
    else:
        print(f"Queued Alfred request: {request['id']}")


def cmd_alfred_requests(args):
    payload = list_requests()
    if getattr(args, "json", False):
        import json
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(format_requests(payload))


def cmd_alfred_promote(args):
    result = promote_request(args.request_id)
    if getattr(args, "json", False):
        import json
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        if result.get("ok"):
            print(f"Promoted {args.request_id} -> {result['job']['id']}")
        else:
            print(result.get("error"))

    if not result.get("ok"):
        raise SystemExit(1)


def cmd_alfred_status(args):
    payload = alfred_status()
    if getattr(args, "json", False):
        import json
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(format_alfred_status(payload))


def cmd_alfred_task(args):
    result = run_task(args.goal)
    if getattr(args, "json", False):
        import json
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(format_task_result(result))

    if not result.get("ok"):
        raise SystemExit(1)


def cmd_alfred_plan(args):
    plan = plan_goal(args.goal)
    if getattr(args, "json", False):
        import json
        print(json.dumps(plan, indent=2, sort_keys=True))
    else:
        print(format_plan(plan))


def cmd_alfred_run(args):
    job = create_job(args.goal)
    if getattr(args, "json", False):
        import json
        print(json.dumps(job, indent=2, sort_keys=True))
    else:
        print(format_job(job))

    if job.get("status") == "blocked":
        raise SystemExit(1)





def cmd_alfred_result(args):
    result = get_job_result(args.job_id)
    if getattr(args, "json", False):
        import json
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(format_job_result(result))

    if not result.get("ok"):
        raise SystemExit(1)

def cmd_alfred_inspect(args):
    result = inspect_job(args.job_id)
    if getattr(args, "json", False):
        import json
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(format_job_inspection(result))

    if not result.get("ok"):
        raise SystemExit(1)


def cmd_alfred_cancel(args):
    result = cancel_job(args.job_id)
    if getattr(args, "json", False):
        import json
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(format_job_inspection({"ok": result.get("ok"), "job": result.get("job", {}), "events": result.get("job", {}).get("events", [])}))

    if not result.get("ok"):
        raise SystemExit(1)


def cmd_alfred_retry(args):
    result = retry_job(args.job_id)
    if getattr(args, "json", False):
        import json
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(format_job(result.get("job", {})))

    if not result.get("ok"):
        raise SystemExit(1)


def cmd_alfred_policy(args):
    policy = get_execution_policy()
    if getattr(args, "json", False):
        import json
        print(json.dumps(policy, indent=2, sort_keys=True))
    else:
        print(format_execution_policy(policy))

def cmd_alfred_execute(args):
    result = execute_job(args.job_id)
    if getattr(args, "json", False):
        import json
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(format_execution_result(result))

    if not result.get("ok"):
        raise SystemExit(1)

def cmd_alfred_jobs(args):
    payload = list_jobs()
    if getattr(args, "json", False):
        import json
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(format_jobs(payload))

def cmd_capability_help(args):
    payload = capability_help()
    if getattr(args, "json", False):
        import json
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(format_capability_help(payload))


def cmd_service_readiness(args):
    payload = service_readiness()
    if getattr(args, "json", False):
        import json
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(format_service_readiness(payload))


def cmd_service_status(args):
    payload = service_status()
    if getattr(args, "json", False):
        import json
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(format_service_status(payload))


def cmd_service_route(args):
    payload = route_capability(args.capability)
    if getattr(args, "json", False):
        import json
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("=========================================")
        print("Estate Service Route")
        print("=========================================")
        print(f"Capability: {payload['capability']}")
        print(f"Matches: {len(payload['matches'])}")
        print(f"Available: {len(payload['available'])}")
        for service in payload["matches"]:
            mark = "AVAILABLE" if service.get("available") else "UNAVAILABLE"
            print(f"{mark} | {service['id']} | {service['name']}")


def cmd_alfred_capabilities(args):
    payload = alfred_capabilities()
    if getattr(args, "json", False):
        import json
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(format_alfred_capabilities, service_readiness, format_service_readiness, capability_help, format_capability_help(payload))

def cmd_audit_summary(args):
    summary = summarize_audit_artifact()
    if getattr(args, "json", False):
        import json
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(format_audit_summary(summary))


def cmd_collaboration_route(args):
    report = run_routing_engine()
    if getattr(args, "json", False):
        import json
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(format_routing_report(report))


def cmd_worker_inboxes(args):
    summary = watch_worker_inboxes()
    if getattr(args, "json", False):
        import json
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(format_inbox_summary(summary))


def cmd_message_ack(args):
    result = acknowledge_message(args.message_id, actor=args.actor, note=args.note)
    if getattr(args, "json", False):
        import json
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Acknowledged {args.message_id}: {result['acknowledgement_path']}")


def cmd_message_reply(args):
    result = create_reply(args.message_id, actor=args.actor, body=args.body, title=args.title)
    if getattr(args, "json", False):
        import json
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Replied to {args.message_id}: {result['reply_path']}")


def cmd_collaboration_events(args):
    summary = generate_event_summary()
    if getattr(args, "json", False):
        import json
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(format_event_summary(summary))


def cmd_operations_board(args):
    board = generate_operations_board()
    if getattr(args, "json", False):
        import json
        print(json.dumps(board, indent=2, sort_keys=True))
    else:
        print(format_operations_board_summary(board))


def cmd_daily_board(args):
    board = generate_daily_board_integration()
    if getattr(args, "json", False):
        import json
        print(json.dumps(board, indent=2, sort_keys=True))
    else:
        print(format_daily_board_integration_summary(board))


def cmd_dependency_graph(args):
    graph = generate_dependency_graph()
    if getattr(args, "json", False):
        import json
        print(json.dumps(graph, indent=2, sort_keys=True))
    else:
        print(format_dependency_graph_summary(graph))


def cmd_capability_lifecycle(args):
    report = generate_capability_lifecycle_report()
    if getattr(args, "json", False):
        import json
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(format_capability_lifecycle_summary(report))



def cmd_estate_capability_registry(args):
    registry = generate_estate_capability_registry()
    if getattr(args, "json", False):
        import json
        print(json.dumps(registry, indent=2, sort_keys=True))
    else:
        print(format_estate_capability_registry_summary(registry))


def cmd_estate_service_catalog(args):
    catalog = generate_estate_service_catalog()
    if getattr(args, "json", False):
        import json
        print(json.dumps(catalog, indent=2, sort_keys=True))
    else:
        print(format_estate_service_catalog_summary(catalog))

def cmd_service_dependency_matrix(args):
    matrix = generate_service_dependency_matrix()
    if getattr(args, "json", False):
        import json
        print(json.dumps(matrix, indent=2, sort_keys=True))
    else:
        print(format_service_dependency_matrix_summary(matrix))

def cmd_service_health_registry(args):
    registry = generate_service_health_registry()
    if getattr(args, "json", False):
        import json
        print(json.dumps(registry, indent=2, sort_keys=True))
    else:
        print(format_service_health_registry_summary(registry))

def cmd_service_status_board(args):
    board = generate_service_status_board()
    if getattr(args, "json", False):
        import json
        print(json.dumps(board, indent=2, sort_keys=True))
    else:
        print(format_service_status_board_summary(board))


def _parse_source_verbosity(items):
    parsed = {}
    for item in items or []:
        if "=" not in item:
            continue
        source, verbosity = item.split("=", 1)
        parsed[source.strip()] = verbosity.strip()
    return parsed


def cmd_operator_activity_stream(args):
    stream = generate_operator_activity_stream(
        sources=getattr(args, "source", None),
        severities=getattr(args, "severity", None),
        verbosity=getattr(args, "verbosity", None),
        limit=getattr(args, "limit", 50),
        profile=getattr(args, "profile", "default"),
        save_profile=getattr(args, "save_profile", None),
        source_verbosity=_parse_source_verbosity(getattr(args, "source_verbosity", None)),
        ui_theme=getattr(args, "ui_theme", None),
    )
    if getattr(args, "json", False):
        import json
        print(json.dumps(stream, indent=2, sort_keys=True))
    else:
        print(format_operator_activity_stream_summary(stream))


def cmd_operations_notification_center(args):
    if getattr(args, "acknowledge", None):
        result = acknowledge_operations_notification(args.acknowledge)
        if getattr(args, "json", False):
            import json
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print(f"Locally acknowledged {args.acknowledge}; authoritative source events were not mutated.")
        return
    payload = generate_operations_notification_center(sources=getattr(args, "source", None), severities=getattr(args, "severity", None), acknowledged=getattr(args, "acknowledged", None), limit=getattr(args, "limit", 100))
    if getattr(args, "json", False):
        import json
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(format_operations_notification_center_summary(payload))


def cmd_operations_center_profile(args):
    if getattr(args, "save_profile", None):
        payload = save_workspace_profile(name=args.save_profile, base_profile=args.profile, active_tab=args.active_tab)
    else:
        payload = resolve_workspace_profile(profile_name=args.profile)
    if args.json:
        import json
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        profile = payload.get("profile", {})
        print(f"Operations Center workspace profile: {payload.get('selected_profile')}")
        print(f"Active tab: {profile.get('active_tab')}")
        print(f"Tabs: {', '.join(profile.get('tab_order', []))}")

def cmd_operational_validation(args):
    report = generate_operational_validation_report()
    if getattr(args, "json", False):
        import json
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(format_operational_validation_summary(report))


def cmd_steward_dashboard(args):
    dashboard = generate_steward_dashboard()
    if getattr(args, "json", False):
        import json
        print(json.dumps(dashboard, indent=2, sort_keys=True))
    else:
        print(format_steward_dashboard_summary(dashboard))

def cmd_mailbox_index(args):
    index = generate_mailbox_index()
    if getattr(args, "json", False):
        import json
        print(json.dumps(mailbox_index_summary(index), indent=2, sort_keys=True))
    else:
        summary = mailbox_index_summary(index)
        print("Estate Mailbox Index")
        print(f"Messages: {summary['message_count']}")
        print(f"Warnings: {summary['warning_count']}")
        print(f"Open CA2 messages: {summary['open_ca2_message_count']}")
        print(f"Open CA3 messages: {summary['open_ca3_message_count']}")
        print(f"Open CA4 messages: {summary.get('open_ca4_message_count', 0)}")
        print(f"Ack-required messages: {summary.get('ack_required_message_count', 0)}")
        print(f"Threads: {summary.get('thread_count', 0)}")
        print(f"Index: {summary['index_path']}")



def cmd_personnel_resolve(args):
    resolution = resolve_personnel_identity(args.actor)
    if getattr(args, "json", False):
        import json
        print(json.dumps(resolution, indent=2, sort_keys=True))
    else:
        print(format_resolution(resolution))


def cmd_onboarding_manifest_check(args):
    report = check_onboarding_manifests()
    if getattr(args, "json", False):
        import json
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(format_onboarding_manifest_check(report))

    if not report["ok"]:
        raise SystemExit(1)



def cmd_hr_onboard(args):
    result = run_employee_onboarding(
        name=args.name,
        department=args.department,
        office=args.office,
        role=args.role,
        classification=args.classification,
        package_type=args.package_type,
        steward_authorization=args.steward_authorization,
        dry_run=args.dry_run,
    )
    if getattr(args, "json", False):
        import json
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(format_onboarding_result(result))
    if not result.get("ok"):
        raise SystemExit(1)

def cmd_work_package_handoffs(args):
    handoffs = list_pending_handoffs()
    print(format_handoff_list(handoffs))



def cmd_estate_search(args):
    root = Path(args.root) if getattr(args, "root", None) else Path.cwd()
    result = search_institutional_index(
        args.query,
        root=root,
        refresh=not getattr(args, "no_refresh", False),
    )
    if getattr(args, "json", False):
        import json
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(format_search_report(result))

def cmd_global_search(args):
    result = search_global_palette(args.query, refresh=not getattr(args, "no_refresh", False))
    if getattr(args, "json", False):
        import json
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(format_palette_report(result))


def cmd_palette_command(args):
    result = execute_registered_command(args.command_id)
    if getattr(args, "json", False):
        import json
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(result.get("message"))
    if not result.get("ok"):
        raise SystemExit(1)


def cmd_document_registry(args):
    registry = load_document_registry()
    if getattr(args, "json", False):
        import json
        print(json.dumps(registry, indent=2, sort_keys=True))
    else:
        print(format_document_registry(registry))


def cmd_check_updates(args):
    report = generate_check_updates(actor=getattr(args, "actor", None))
    if getattr(args, "json", False):
        import json
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(format_check_updates(report))

def cmd_mailbox_sync_duty(args):
    report = generate_mailbox_sync_duty(actor=getattr(args, "actor", None))
    if getattr(args, "json", False):
        import json
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(format_mailbox_sync_duty(report))




def cmd_assignment_queue(args):
    queue = generate_assignment_queue()
    if getattr(args, "json", False):
        import json
        print(json.dumps(queue, indent=2, sort_keys=True))
    else:
        print(format_assignment_queue_markdown(queue))



def cmd_autonomous_work_queue_scheduler(args):
    payload = generate_autonomous_work_queue_scheduler()
    if getattr(args, "json", False):
        import json
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(format_autonomous_work_queue_scheduler(payload))


def cmd_autonomous_operations_audit(args):
    payload = append_autonomous_operations_audit()
    if getattr(args, "json", False):
        import json
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(format_autonomous_operations_audit())


def cmd_operations_center_settings(args):
    updates = {
        "appearance__theme": getattr(args, "theme", None),
        "appearance__accent": getattr(args, "accent", None),
        "workspace__default_profile": getattr(args, "default_workspace_profile", None),
        "operator_visibility__default_verbosity_profile": getattr(args, "default_verbosity_profile", None),
        "operator_visibility__global_verbosity": getattr(args, "global_verbosity", None),
        "refresh__mode": getattr(args, "refresh_mode", None),
        "refresh__quiet_refresh_seconds": getattr(args, "quiet_refresh_seconds", None),
        "command_console__mode": getattr(args, "command_console_mode", None),
    }
    if any(value is not None for value in updates.values()):
        payload = save_operations_center_settings(**updates)
    else:
        payload = load_operations_center_settings()
    if getattr(args, "json", False):
        import json
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        settings = payload.get("settings", {})
        print("Operations Center Settings Manager")
        print(f"Version: {payload.get('ui_version')} schema={payload.get('version')}")
        print(f"Theme: {(settings.get('appearance') or {}).get('theme')}")
        print(f"Default workspace: {(settings.get('workspace') or {}).get('default_profile')}")
        print(f"Default verbosity profile: {(settings.get('operator_visibility') or {}).get('default_verbosity_profile')}")
        print(f"Warnings: {len(payload.get('warnings') or [])}")

def cmd_decision_queue(args):
    queue = generate_decision_queue()
    if getattr(args, "json", False):
        import json
        print(json.dumps(queue, indent=2, sort_keys=True))
    else:
        print(format_decision_queue_markdown(queue))



def cmd_alfred_duty(args):
    payload = run_alfred_duty()
    if getattr(args, "json", False):
        import json
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(format_alfred_duty(payload))


def cmd_helen_duty(args):
    payload = run_helen_duty()
    if getattr(args, "json", False):
        import json
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(format_helen_duty(payload))


def cmd_resident_duty(args):
    resident = (getattr(args, "resident", None) or "").lower()
    if resident == "alfred":
        cmd_alfred_duty(args)
        return
    if resident == "helen":
        cmd_helen_duty(args)
        return
    raise SystemExit("Only Alfred and Helen duty runners are implemented.")


def cmd_resident_presence(args):
    payload = filter_resident(build_resident_presence(), getattr(args, "resident", None))
    if getattr(args, "json", False):
        import json
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(format_resident_presence(payload))


def cmd_operations_center(args):
    if args.action == "start":
        payload = operations_center_start(host=args.host, port=args.port)
    elif args.action == "status":
        payload = operations_center_status()
    elif args.action == "stop":
        payload = operations_center_stop()
    else:
        raise SystemExit(f"Unsupported operations-center action: {args.action}")
    if getattr(args, "json", False):
        import json
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(format_operations_center_bootstrap(payload))

def cmd_steward_command_center(args):
    if getattr(args, "serve", False):
        server = serve_command_center(host=args.host, port=args.port)
        host, port = server.server_address
        print(f"Office of the Steward command center serving at http://{host}:{port}/")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()
        return

    payload = generate_command_center(Path.cwd())
    if getattr(args, "json", False):
        import json
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("Office of the Steward command center generated: runtime/steward/command_center.html")

def cmd_worker_heartbeat(args):
    heartbeat = create_worker_heartbeat(
        args.worker_id,
        activity=args.activity,
        status=args.status,
        last_completed_work_package=args.last_completed_work_package,
        blocking_reason=args.blocking_reason,
    )
    summary = generate_worker_runtime_summary()
    if getattr(args, "json", False):
        import json
        print(json.dumps({"heartbeat": heartbeat, "summary": summary["summary"]}, indent=2, sort_keys=True))
    else:
        print(f"Recorded heartbeat for {heartbeat['worker_id']} with status {heartbeat['status']}.")


def cmd_worker_runtime_summary(args):
    payload = generate_worker_runtime_summary(stale_after_minutes=args.stale_after_minutes)
    if getattr(args, "json", False):
        import json
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(format_worker_runtime_summary(payload))

def cmd_worker_runtime_monitor(args):
    payload = generate_worker_runtime_monitor(stale_after_minutes=args.stale_after_minutes)
    if getattr(args, "json", False):
        import json
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(format_worker_runtime_monitor(payload))


def cmd_steward_presence(args):
    payload = generate_steward_presence_state()
    if getattr(args, "json", False):
        import json
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(format_steward_presence_state(payload))


def cmd_morning_briefing(args):
    briefing = generate_morning_briefing()
    if getattr(args, "json", False):
        import json
        print(json.dumps(briefing, indent=2, sort_keys=True))
    else:
        print(format_morning_briefing(briefing))

def cmd_estate_validate_local(args):
    report = generate_local_operational_validation_run()
    if getattr(args, "json", False):
        import json
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(format_local_operational_validation_summary(report))


def cmd_audit(args):
    if getattr(args, "json", False):
        import json
        from estate.core.audit import run_audit
        report = run_audit()
        print(json.dumps(report, indent=2))
    else:
        report = print_audit_report()

    if getattr(args, "save", False):
        path = save_audit_report(report)
        if not getattr(args, "json", False):
            print(f"Saved audit report: {path}")

    if report["failed"] > 0:
        raise SystemExit(1)

def cmd_validation_production_readiness(args):
    import json
    payload = generate_production_readiness_report()
    if getattr(args, "json", False):
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(format_production_readiness_markdown(payload))



def cmd_alfred_runtime(args):
    if args.alfred_runtime_action == "event-brief":
        if args.sample:
            event = build_alfred_event(
                "manual_steward_note",
                "cli_sample",
                event_id="alfred_evt_sample",
                timestamp="2026-07-09T00:00:00+00:00",
                source_artifacts=["docs/residents/alfred/runtime/Alfred_Event_Intake_Schema_v0_1.md"],
                required_action="brief_only",
                payload={"note": "Sample non-executing Alfred runtime event."},
            )
        else:
            event = build_alfred_event(args.event_type, args.source, source_artifacts=args.source_artifact or [], payload={})
        briefing = render_alfred_briefing(event, verbosity=args.verbosity)
        if getattr(args, "json", False):
            print(json.dumps({"event": event, "briefing": briefing}, indent=2, sort_keys=True))
        else:
            print(briefing["briefing"])

def cmd_validate_work_package(args):
    import json
    payload = validate_work_package(args.id)
    if getattr(args, "json", False):
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(format_validation_markdown(payload))
    if payload.get("validation_status") in {"failed", "no_recipe"}:
        raise SystemExit(1)


def cmd_codex_bridge(args):
    import json
    request = load_bridge_request(args.request)
    result = run_codex_bridge_request(request, dry_run=args.dry_run)
    if getattr(args, "json", False):
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_codex_bridge_result(result))
    if result.status in {"failed", "policy_denied"}:
        raise SystemExit(1)



def cmd_execution_provider_adapter(args):
    import json
    try:
        if args.execution_provider_adapter_action == "validate":
            payload = validate_adapter_request_file(args.request)
        elif args.execution_provider_adapter_action == "dry-run":
            payload = run_dry_run_adapter(load_adapter_contract_request(args.request))
        else:
            raise SystemExit(f"Unknown execution-provider-adapter action: {args.execution_provider_adapter_action}")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        if getattr(args, "json", False):
            print(json.dumps({"status": "failed", "error": str(exc)}, indent=2, sort_keys=True))
        else:
            print(f"Execution provider adapter validation failed: {exc}")
        raise SystemExit(1)
    if getattr(args, "json", False):
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        status = payload.get("status") or (payload.get("validation") or {}).get("status")
        print(f"Execution provider adapter {args.execution_provider_adapter_action}: {status}")



def cmd_codex_bridge_adapter(args):
    import json
    try:
        request = load_adapter_contract_request(args.request)
        if args.codex_bridge_adapter_action == "validate":
            adapter = CodexBridgeExecutionProviderAdapter()
            payload = {"request": request.to_dict(), "validation": adapter.validate_request(request).to_dict()}
        elif args.codex_bridge_adapter_action == "dry-run":
            payload = run_codex_bridge_adapter_dry_run(request)
        else:
            raise SystemExit(f"Unknown codex-bridge-adapter action: {args.codex_bridge_adapter_action}")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        if getattr(args, "json", False):
            print(json.dumps({"status": "failed", "error": str(exc)}, indent=2, sort_keys=True))
        else:
            print(f"Codex Bridge adapter failed: {exc}")
        raise SystemExit(1)
    if getattr(args, "json", False):
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        status = payload.get("status") or (payload.get("validation") or {}).get("status")
        print(f"Codex Bridge adapter {args.codex_bridge_adapter_action}: {status}")


def cmd_execution_adapter_handoff(args):
    import json
    try:
        if args.execution_adapter_handoff_action == "inspect":
            payload = inspect_handoff(args.dispatch_id)
        elif args.execution_adapter_handoff_action == "prepare":
            payload = prepare_handoff(args.dispatch_id)
        elif args.execution_adapter_handoff_action == "validate":
            payload = validate_handoff(args.dispatch_id)
        elif args.execution_adapter_handoff_action == "dry-run":
            payload = dry_run_handoff(args.dispatch_id)
        else:
            raise SystemExit(f"Unknown execution-adapter-handoff action: {args.execution_adapter_handoff_action}")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        payload = {"status": "failed", "error": str(exc), "live_provider_called": False}
        if getattr(args, "json", False):
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(f"Execution adapter handoff failed: {exc}")
        raise SystemExit(1)
    if getattr(args, "json", False):
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Execution adapter handoff {args.execution_adapter_handoff_action}: {payload.get('status')}")
    if payload.get("errors"):
        raise SystemExit(1)



def cmd_codex_live_execution(args):
    import json
    try:
        gate = CodexLiveExecutionGate()
        action = args.codex_live_execution_action
        if action == "preview":
            payload = gate.preview(args.dispatch_id, args.authorization)
        elif action == "execute":
            payload = gate.execute(args.dispatch_id, args.authorization, confirm_live_execution=getattr(args, "confirm_live_execution", False))
        elif action == "status":
            payload = gate.status(args.dispatch_id)
        elif action == "report":
            text = gate.report(args.dispatch_id)
            if getattr(args, "json", False):
                print(json.dumps(gate.status(args.dispatch_id), indent=2, sort_keys=True))
            else:
                print(text)
            return
        else:
            raise SystemExit(f"Unknown codex-live-execution action: {action}")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        payload = {"status": "failed", "error": str(exc), "live_provider_called": False}
        if getattr(args, "json", False):
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(f"Codex live execution gate failed: {exc}")
        raise SystemExit(1)
    if getattr(args, "json", False):
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Codex live execution {action}: {payload.get('status')}")
    if payload.get("errors"):
        raise SystemExit(1)


def cmd_execution_attempt(args):
    import json
    runtime = ExecutionAttemptRuntime()
    action = args.execution_attempt_action
    try:
        if action == "status":
            payload = runtime.status(getattr(args, "dispatch_id", None))
        elif action == "cancel-request":
            payload = runtime.request_cancellation(args.dispatch_id, args.attempt_id, requested_by=getattr(args, "requested_by", "operator"), reason=args.reason, cooperative=True)
        elif action == "inspect-recovery":
            payload = runtime.inspect_recovery(args.dispatch_id)
        elif action == "release-stale":
            payload = runtime.release_stale(args.dispatch_id, args.attempt_id, confirm_stale_release=args.confirm_stale_release, released_by=getattr(args, "released_by", "operator"), reason=getattr(args, "reason", "explicit stale release"))
        elif action == "retry-eligibility":
            payload = runtime.retry_eligibility(args.dispatch_id)
        else:
            raise SystemExit(f"Unknown execution-attempt action: {action}")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        payload = {"status": "failed", "error": str(exc), "live_provider_called": False}
        if getattr(args, "json", False):
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(f"Execution attempt runtime failed: {exc}")
        raise SystemExit(1)
    if getattr(args, "json", False):
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Execution attempt {action}: {payload.get('status') or payload.get('retry_eligible')}")

def cmd_execution_result_reconciliation(args):
    import json
    try:
        if args.execution_result_reconciliation_action == "inspect":
            payload = inspect_reconciliation(args.dispatch_id)
        elif args.execution_result_reconciliation_action == "reconcile":
            payload = reconcile_result(args.dispatch_id, args.result)
        elif args.execution_result_reconciliation_action == "report":
            payload = inspect_reconciliation(args.dispatch_id)
            if payload.get("reconciliation"):
                text = format_reconciliation_report(payload["reconciliation"])
                if getattr(args, "json", False):
                    print(json.dumps(payload["reconciliation"], indent=2, sort_keys=True))
                else:
                    print(text)
                return
            raise ValueError("dispatch result has not been reconciled")
        else:
            raise SystemExit(f"Unknown execution-result-reconciliation action: {args.execution_result_reconciliation_action}")
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        payload = {"status": "failed", "error": str(exc), "live_provider_called": False, "institutional_acceptance_state": "not_granted"}
        if getattr(args, "json", False):
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(f"Execution result reconciliation failed: {exc}")
        raise SystemExit(1)
    if getattr(args, "json", False):
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Execution result reconciliation {args.execution_result_reconciliation_action}: {payload.get('status')}")

def cmd_provider_routing_recommendation(args):
    import json
    try:
        if args.provider_routing_action == "evaluate":
            payload = evaluate_recommendation_file(args.request, write=True)
            if getattr(args, "json", False):
                print(json.dumps(payload, indent=2, sort_keys=True))
            else:
                print(f"Provider routing recommendation: {payload['recommended_provider']}")
                print(f"Recommendation: {payload['recommendation_path']}")
                print(f"Report: {payload['report_path']}")
        elif args.provider_routing_action == "explain":
            request = load_recommendation_request(args.request)
            result = evaluate_provider_routing_recommendation(request)
            if getattr(args, "json", False):
                print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
            else:
                print(explain_provider_routing_recommendation(result), end="")
        else:
            raise SystemExit(f"Unknown provider routing action: {args.provider_routing_action}")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        if getattr(args, "json", False):
            print(json.dumps({"status": "failed", "error": str(exc)}, indent=2, sort_keys=True))
        else:
            print(f"Provider routing recommendation failed: {exc}")
        raise SystemExit(1)

def cmd_execution_activity(args):
    import json
    payload = generate_execution_activity_surface()
    if getattr(args, "json", False):
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(format_execution_activity_summary(payload))


def cmd_execution_activity_report(args):
    payload = generate_execution_activity_surface()
    print(format_execution_activity_report(payload))


def cmd_execution_dispatch(args):
    import json
    action = args.execution_dispatch_action
    if action == "enqueue":
        item = enqueue_dispatch_request(load_dispatch_request(args.file))
        payload = item.to_dict()
        if getattr(args, "json", False):
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(format_dispatch_item(item))
        return
    if action == "list":
        items = list_dispatch_items(state=getattr(args, "state", None))
        snapshot = generate_current_dispatch_snapshot()
        payload = {"items": [item.to_dict() for item in items], "summary": snapshot.get("summary", {}), "state_filter": getattr(args, "state", None)}
        if getattr(args, "json", False):
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(format_execution_dispatch_summary(snapshot))
        return
    if action == "inspect":
        item = inspect_dispatch_item(args.dispatch_id)
        if getattr(args, "json", False):
            print(json.dumps(item.to_dict(), indent=2, sort_keys=True))
        else:
            print(format_dispatch_item(item))
        return
    if action == "update-state":
        item = update_dispatch_state(args.dispatch_id, args.state, summary=getattr(args, "summary", None))
        if getattr(args, "json", False):
            print(json.dumps(item.to_dict(), indent=2, sort_keys=True))
        else:
            print(format_dispatch_item(item))
        return
    if action == "block":
        item = block_dispatch_item(args.dispatch_id, args.reason)
        if getattr(args, "json", False):
            print(json.dumps(item.to_dict(), indent=2, sort_keys=True))
        else:
            print(format_dispatch_item(item))
        return
    if action == "attention":
        item = mark_dispatch_attention(args.dispatch_id, attention_required=not args.clear, reason=getattr(args, "reason", None))
        if getattr(args, "json", False):
            print(json.dumps(item.to_dict(), indent=2, sort_keys=True))
        else:
            print(format_dispatch_item(item))
        return
    if action == "cancel":
        item = cancel_dispatch_item(args.dispatch_id, reason=getattr(args, "reason", None))
        if getattr(args, "json", False):
            print(json.dumps(item.to_dict(), indent=2, sort_keys=True))
        else:
            print(format_dispatch_item(item))
        return
    if action == "complete":
        item = complete_dispatch_item(args.dispatch_id, result_reference=getattr(args, "result_reference", None))
        if getattr(args, "json", False):
            print(json.dumps(item.to_dict(), indent=2, sort_keys=True))
        else:
            print(format_dispatch_item(item))
        return
    if action == "prepare-handoff":
        payload = prepare_codex_bridge_handoff(args.dispatch_id)
        if getattr(args, "json", False):
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(f"Codex Bridge dry-run handoff prepared: {payload.get('handoff_path')}")
        return
    if action == "snapshot":
        payload = generate_current_dispatch_snapshot()
        if getattr(args, "json", False):
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(format_execution_dispatch_summary(payload))
        return
    raise SystemExit(f"Unknown execution-dispatch action: {action}")


def cmd_execution_dispatch_report(args):
    payload = generate_current_dispatch_snapshot()
    print(format_execution_dispatch_report(payload))



def cmd_ai_services(args):
    import json
    from estate.ai_services.control import status, request
    from estate.ai_services.discovery import rediscover
    from estate.ai_services.reports import write_wp0131_report
    from estate.ai_services.steward_model_selector import build_steward_ai_services_panel, build_models, load_preferences, set_preference, load_assignments, set_assignment, approvals, decide_approval, refresh_status
    if args.ai_services_action == "status":
        payload = status()
    elif args.ai_services_action == "rediscover":
        payload = rediscover(actor=getattr(args, "actor", "codex"))
    elif args.ai_services_action in {"start", "stop"}:
        payload = request(args.ai_services_action, args.service, actor=getattr(args, "actor", "alfred"), approved_by=args.approved_by, dry_run=args.dry_run, health_timeout_seconds=args.health_timeout_seconds, health_interval_seconds=args.health_interval_seconds)
    elif args.ai_services_action == "load-model":
        payload = request("load_model", args.service, actor=getattr(args, "actor", "alfred"), approved_by=args.approved_by, model=args.model, dry_run=args.dry_run, health_timeout_seconds=args.health_timeout_seconds, health_interval_seconds=args.health_interval_seconds)
    elif args.ai_services_action == "models":
        payload = {"models": build_models(status()["registry"])}
    elif args.ai_services_action == "model-preferences":
        payload = load_preferences()
    elif args.ai_services_action == "set-model-preference":
        payload = set_preference(args.name, args.model_id, updated_by=args.updated_by, reason=args.reason)
    elif args.ai_services_action == "assignments":
        payload = load_assignments()
    elif args.ai_services_action == "set-assignment":
        payload = set_assignment(args.worker, args.model_id, updated_by=args.updated_by, reason=args.reason, allowed_operations=args.allowed_operation)
    elif args.ai_services_action == "approvals":
        payload = approvals()
    elif args.ai_services_action in {"approve", "deny"}:
        payload = decide_approval("approved" if args.ai_services_action == "approve" else "denied", args.operation, args.service, actor=args.actor, model=args.model, approved_by=args.approved_by, reason=args.reason)
    elif args.ai_services_action == "refresh-status":
        payload = refresh_status()
    elif args.ai_services_action == "steward-panel":
        payload = build_steward_ai_services_panel()
    elif args.ai_services_action == "write-report":
        payload = write_wp0131_report()
    else:
        payload = {"error": "unknown_action"}
    if getattr(args, "json", False):
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))

def cmd_capability_dependency_visualization(args):
    payload = generate_capability_dependency_visualization()
    if getattr(args, "json", False):
        import json
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(format_capability_dependency_visualization_summary(payload))

def cmd_capability_gap_report(args):
    payload = generate_capability_gap_report()
    if getattr(args, "json", False):
        import json
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(format_capability_gap_summary(payload))


def cmd_validation_metrics_dashboard(args):
    payload = generate_validation_metrics_dashboard()
    if getattr(args, "json", False):
        import json
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(format_validation_metrics_summary(payload))


def cmd_operational_readiness_dashboard(args):
    payload = generate_operational_readiness_dashboard()
    if getattr(args, "json", False):
        import json
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(format_operational_readiness_summary(payload))


def cmd_validation_handoff_artifact_workflow(args):
    payload = generate_validation_handoff_artifact_workflow()
    if getattr(args, "json", False):
        import json
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(format_validation_handoff_summary(payload))


def cmd_validation_observations(args):
    import json
    if getattr(args, "update_status", None):
        record = update_observation_status(args.observation_id, args.update_status, linked_follow_up_work_package=getattr(args, "follow_up_wp", None))
        payload = {"updated": record, "observations": load_observations()}
    elif getattr(args, "observation_id", None):
        record = append_observation({
            "observation_id": args.observation_id,
            "related_work_package": args.related_work_package,
            "observed_behavior": args.observed_behavior,
            "expected_behavior": args.expected_behavior,
            "source_of_observation": args.source_of_observation,
            "severity": args.severity,
            "status": args.status,
            "recommended_next_action": args.recommended_next_action,
            "linked_follow_up_work_package": args.follow_up_wp,
        })
        payload = {"created": record, "observations": load_observations()}
    else:
        payload = {"observations": load_observations()}
    if getattr(args, "json", False):
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(render_markdown_log(payload["observations"]))


def cmd_resident_authority(args):
    import json
    if args.action == "check":
        if not args.resident or not args.resident_action:
            raise SystemExit("resident-authority check requires --resident and --action")
        payload = check_authority(args.resident, args.resident_action, target=args.target, source_refs=args.source_ref or [])
    else:
        payload = list_authority(resident=getattr(args, "resident", None))
    if getattr(args, "json", False):
        print(json.dumps(payload, indent=2, sort_keys=True))
    elif args.action == "check":
        print(format_authority_decision(payload))
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))

def cmd_resident_conversation(args):
    import json
    if args.action == "start":
        if not args.resident:
            raise SystemExit("resident-conversation start requires --resident")
        payload = create_session(
            resident=args.resident,
            participant_role=args.participant_role,
            status=args.status,
            source_artifacts=args.source_artifact or [],
            prompt=args.prompt,
            response=args.response,
            operator_note=args.operator_note,
            outcome=args.outcome,
            canonical_links=args.canonical_link or [],
        )
    elif args.action == "list":
        payload = list_sessions(resident=getattr(args, "resident", None))
    else:
        if not args.session:
            raise SystemExit("resident-conversation show requires --session")
        payload = load_session(args.session)
        if payload is None:
            payload = {"error": "session_not_found", "session_id": args.session}
            if getattr(args, "json", False):
                print(json.dumps(payload, indent=2, sort_keys=True))
            else:
                print(f"Session not found: {args.session}")
            raise SystemExit(1)
    if getattr(args, "json", False):
        print(json.dumps(payload, indent=2, sort_keys=True))
    elif args.action == "list":
        print(format_session_list(payload))
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))

def cmd_sync_ollama(args):
    created, ec_id = sync_ollama_providers()
    print(f"Logged {ec_id}")
    if created:
        for provider in created:
            print(f"Created {provider['id']}: {provider['name']}")
    else:
        print("No new Ollama providers created.")

def main(argv=None):
    parser = argparse.ArgumentParser(prog="estate", description="Estate Core CLI")
    sub = parser.add_subparsers(dest="command")


    p = sub.add_parser("ai-services", help="Inspect and govern local AI services")
    ai_sub = p.add_subparsers(dest="ai_services_action", required=True)
    sp = ai_sub.add_parser("status")
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(func=cmd_ai_services)
    sp = ai_sub.add_parser("rediscover")
    sp.add_argument("--actor", default="codex")
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(func=cmd_ai_services)
    for action_name in ("start", "stop"):
        sp = ai_sub.add_parser(action_name)
        sp.add_argument("--service", required=True)
        sp.add_argument("--approved-by")
        sp.add_argument("--actor", default="alfred")
        sp.add_argument("--dry-run", action="store_true", default=False)
        sp.add_argument("--health-timeout-seconds", type=float, default=30)
        sp.add_argument("--health-interval-seconds", type=float, default=2)
        sp.add_argument("--json", action="store_true")
        sp.set_defaults(func=cmd_ai_services)
    sp = ai_sub.add_parser("load-model")
    sp.add_argument("--service", required=True)
    sp.add_argument("--model", required=True)
    sp.add_argument("--approved-by")
    sp.add_argument("--actor", default="alfred")
    sp.add_argument("--dry-run", action="store_true", default=False)
    sp.add_argument("--health-timeout-seconds", type=float, default=30)
    sp.add_argument("--health-interval-seconds", type=float, default=2)
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(func=cmd_ai_services)
    for action_name in ("models", "model-preferences", "assignments", "approvals", "refresh-status", "steward-panel"):
        sp = ai_sub.add_parser(action_name)
        sp.add_argument("--json", action="store_true")
        sp.set_defaults(func=cmd_ai_services)
    sp = ai_sub.add_parser("set-model-preference")
    sp.add_argument("--name", required=True); sp.add_argument("--model-id", required=True); sp.add_argument("--updated-by", default="steward"); sp.add_argument("--reason", default=""); sp.add_argument("--json", action="store_true"); sp.set_defaults(func=cmd_ai_services)
    sp = ai_sub.add_parser("set-assignment")
    sp.add_argument("--worker", required=True); sp.add_argument("--model-id", required=True); sp.add_argument("--updated-by", default="steward"); sp.add_argument("--reason", default=""); sp.add_argument("--allowed-operation", action="append"); sp.add_argument("--json", action="store_true"); sp.set_defaults(func=cmd_ai_services)
    for action_name in ("approve", "deny"):
        sp = ai_sub.add_parser(action_name)
        sp.add_argument("--operation", required=True); sp.add_argument("--service", required=True); sp.add_argument("--actor", default="alfred"); sp.add_argument("--model"); sp.add_argument("--approved-by", default="steward"); sp.add_argument("--reason", default=""); sp.add_argument("--json", action="store_true"); sp.set_defaults(func=cmd_ai_services)
    sp = ai_sub.add_parser("write-report")
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(func=cmd_ai_services)

    p = sub.add_parser("change")
    p.add_argument("--title", required=True)
    p.add_argument("--summary", required=True)
    p.add_argument("--status", default="Draft")
    p.add_argument("--classification", default="Estate Internal")
    p.set_defaults(func=cmd_change)

    p = sub.add_parser("resident")
    p.add_argument("--name", required=True)
    p.add_argument("--department", required=True)
    p.add_argument("--office", required=True)
    p.add_argument("--role", required=True)
    p.add_argument("--classification", default="Estate Internal")
    p.set_defaults(func=cmd_resident)

    p = sub.add_parser("model-control", help="Estate model control plane")
    mc = p.add_subparsers(dest="model_control_action", required=True)
    q = mc.add_parser("rediscover"); q.add_argument("--fetch-runtime", action="store_true"); q.add_argument("--json", action="store_true"); q.set_defaults(func=cmd_model_control)
    q = mc.add_parser("list-models"); q.add_argument("--json", action="store_true"); q.set_defaults(func=cmd_model_control)
    q = mc.add_parser("assignments"); q.add_argument("--json", action="store_true"); q.set_defaults(func=cmd_model_control)
    q = mc.add_parser("set-default"); q.add_argument("--capability", required=True); q.add_argument("--model", required=True); q.add_argument("--approved-by", required=True); q.add_argument("--json", action="store_true"); q.set_defaults(func=cmd_model_control)
    q = mc.add_parser("assign"); q.add_argument("--actor", required=True); q.add_argument("--capability", required=True); q.add_argument("--model", required=True); q.add_argument("--approved-by", required=True); q.add_argument("--json", action="store_true"); q.set_defaults(func=cmd_model_control)
    q = mc.add_parser("validate-assignments"); q.add_argument("--json", action="store_true"); q.set_defaults(func=cmd_model_control)

    p = sub.add_parser("alfred-llm-diagnostics")
    p.add_argument("--json", action="store_true", help="Print Alfred LLM connection diagnostic JSON")
    p.set_defaults(func=cmd_alfred_llm_diagnostics)

    p = sub.add_parser("status")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("list-residents")
    p.set_defaults(func=cmd_list_residents)

    p = sub.add_parser("services")
    p.add_argument("--json", action="store_true", help="Print registered services JSON")
    p.set_defaults(func=cmd_services)

    p = sub.add_parser("capabilities")
    p.add_argument("--json", action="store_true", help="Print registered capabilities JSON")
    p.set_defaults(func=cmd_capabilities)

    p = sub.add_parser("providers")
    p.set_defaults(func=cmd_providers)

    p = sub.add_parser("discover")
    p.add_argument("--json", action="store_true", help="Run full Discovery cycle and print metrics JSON")
    p.set_defaults(func=cmd_discover)

    p = sub.add_parser("discover-ai")
    p.set_defaults(func=cmd_discover_ai)

    p = sub.add_parser("discovery-report")
    p.add_argument("--json", action="store_true", help="Print latest Discovery observation JSON")
    p.set_defaults(func=cmd_discovery_report)

    p = sub.add_parser("discovery-status")
    p.add_argument("--json", action="store_true", help="Print concise Discovery status JSON")
    p.set_defaults(func=cmd_discovery_status)

    p = sub.add_parser("discovery-catalog")
    p.add_argument("--json", action="store_true", help="Print Discovery catalog JSON")
    p.add_argument("--refresh", action="store_true", help="Refresh catalog from latest observation before printing")
    p.set_defaults(func=cmd_discovery_catalog)

    p = sub.add_parser("discovery-refresh")
    p.add_argument("--json", action="store_true", help="Run Discovery service refresh and print JSON")
    p.set_defaults(func=cmd_discovery_refresh)

    p = sub.add_parser("sync-ollama")
    p.set_defaults(func=cmd_sync_ollama)


    p = sub.add_parser("collaboration-route")
    p.add_argument("--json", action="store_true", help="Run Alfred routing engine and print JSON")
    p.set_defaults(func=cmd_collaboration_route)

    p = sub.add_parser("worker-inboxes")
    p.add_argument("--json", action="store_true", help="Run worker inbox watcher and print JSON")
    p.set_defaults(func=cmd_worker_inboxes)

    p = sub.add_parser("message-ack")
    p.add_argument("message_id", help="Message id to acknowledge")
    p.add_argument("--actor", default="Alfred", help="Actor creating the acknowledgement")
    p.add_argument("--note", default="Acknowledged.", help="Acknowledgement note")
    p.add_argument("--json", action="store_true", help="Print acknowledgement result JSON")
    p.set_defaults(func=cmd_message_ack)

    p = sub.add_parser("message-reply")
    p.add_argument("message_id", help="Message id to reply to")
    p.add_argument("--actor", default="Alfred", help="Actor creating the reply")
    p.add_argument("--title", default=None, help="Reply title")
    p.add_argument("--body", default="", help="Reply body/summary")
    p.add_argument("--json", action="store_true", help="Print reply result JSON")
    p.set_defaults(func=cmd_message_reply)

    p = sub.add_parser("collaboration-events")
    p.add_argument("--json", action="store_true", help="Summarize Collaboration Layer events and print JSON")
    p.set_defaults(func=cmd_collaboration_events)


    p = sub.add_parser("operations-board")
    p.add_argument("--json", action="store_true", help="Generate Operations Board and print snapshot JSON")
    p.set_defaults(func=cmd_operations_board)

    p = sub.add_parser("daily-board")
    p.add_argument("--json", action="store_true", help="Generate Daily Board integration and print JSON")
    p.set_defaults(func=cmd_daily_board)


    p = sub.add_parser("dependency-graph")
    p.add_argument("--json", action="store_true", help="Generate dependency graph and print JSON")
    p.set_defaults(func=cmd_dependency_graph)

    p = sub.add_parser("capability-lifecycle")
    p.add_argument("--json", action="store_true", help="Generate capability lifecycle report and print JSON")
    p.set_defaults(func=cmd_capability_lifecycle)

    p = sub.add_parser("estate-capability-registry", help="Generate the read-only Estate capability registry aggregation")
    p.add_argument("--json", action="store_true", help="Generate Estate capability registry and print JSON")
    p.set_defaults(func=cmd_estate_capability_registry)


    p = sub.add_parser("estate-service-catalog", help="Generate the read-only Estate service catalog aggregation")
    p.add_argument("--json", action="store_true", help="Generate Estate service catalog and print JSON")
    p.set_defaults(func=cmd_estate_service_catalog)

    p = sub.add_parser("service-dependency-matrix", help="Generate the read-only service dependency matrix")
    p.add_argument("--json", action="store_true", help="Generate service dependency matrix and print JSON")
    p.set_defaults(func=cmd_service_dependency_matrix)

    p = sub.add_parser("service-health-registry", help="Generate the read-only service health registry")
    p.add_argument("--json", action="store_true", help="Generate service health registry and print JSON")
    p.set_defaults(func=cmd_service_health_registry)

    p = sub.add_parser("service-status-board", help="Generate the Operations Center service status board")
    p.add_argument("--json", action="store_true", help="Generate service status board and print JSON")
    p.set_defaults(func=cmd_service_status_board)


    p = sub.add_parser("operations-center-profile", help="Resolve or save an Operations Center workspace profile")
    p.add_argument("--json", action="store_true", help="Print resolved workspace profile JSON")
    p.add_argument("--profile", default="mission-control", help="Named workspace profile to load")
    p.add_argument("--save-profile", help="Persist a local profile derived from --profile")
    p.add_argument("--active-tab", help="Active tab for a saved profile")
    p.set_defaults(func=cmd_operations_center_profile)

    p = sub.add_parser("operator-activity-stream", help="Generate the read-only Operator Activity Stream")
    p.add_argument("--json", action="store_true", help="Generate Operator Activity Stream and print JSON")
    p.add_argument("--source", action="append", help="Limit to a source such as validation, workers, mailboxes, service_health")
    p.add_argument("--severity", action="append", help="Limit to a severity such as error, warning, missing, info")
    p.add_argument("--verbosity", choices=["quiet", "normal", "detailed", "diagnostic"], help="Global verbosity level")
    p.add_argument("--profile", default="default", help="Named viewing profile to load")
    p.add_argument("--save-profile", help="Persist the selected filters and verbosity as this named profile")
    p.add_argument("--source-verbosity", action="append", help="Per-source verbosity override, for example workers=detailed")
    p.add_argument("--ui-theme", choices=["system", "light", "dark"], help="Future UI theme preference stored with saved profiles")
    p.add_argument("--limit", type=int, default=50, help="Maximum events to show")
    p.set_defaults(func=cmd_operator_activity_stream)

    p = sub.add_parser("operations-notification-center", help="Generate the read-only Operations Center Notification Center")
    p.add_argument("--json", action="store_true", help="Generate Notification Center and print JSON")
    p.add_argument("--source", action="append", help="Limit to a source such as validation, workers, mailboxes, service_health")
    p.add_argument("--severity", action="append", help="Limit to a severity such as error, warning, missing, info")
    p.add_argument("--acknowledged", action="store_true", default=None, help="Show locally acknowledged notifications only")
    p.add_argument("--acknowledge", help="Record a local-only acknowledgement for a notification id")
    p.add_argument("--limit", type=int, default=100, help="Maximum notifications to show")
    p.set_defaults(func=cmd_operations_notification_center)

    p = sub.add_parser("capability-dependency-visualization", help="Generate capability dependency visualization for Mission Control")
    p.add_argument("--json", action="store_true", help="Generate capability dependency visualization and print JSON")
    p.set_defaults(func=cmd_capability_dependency_visualization)

    p = sub.add_parser("capability-gap-report", help="Generate the read-only capability gap report")
    p.add_argument("--json", action="store_true", help="Generate capability gap report and print JSON")
    p.set_defaults(func=cmd_capability_gap_report)

    p = sub.add_parser("validation-observations", help="List, add, or update validation observations")
    p.add_argument("--json", action="store_true", help="Print validation observations JSON")
    p.add_argument("--observation-id", default=None, help="Observation id to create or update")
    p.add_argument("--related-work-package", default=None, help="Related work package id")
    p.add_argument("--observed-behavior", default="", help="Observed behavior to record")
    p.add_argument("--expected-behavior", default=None, help="Expected behavior, if known")
    p.add_argument("--source-of-observation", default="", help="Source of the observation")
    p.add_argument("--severity", default="follow-up", help="Severity: info, follow-up, defect-candidate, confirmed-defect")
    p.add_argument("--status", default="open", help="Initial status")
    p.add_argument("--recommended-next-action", default="Review in a future validation pass.", help="Recommended next action")
    p.add_argument("--follow-up-wp", default=None, help="Linked follow-up work package, if one exists")
    p.add_argument("--update-status", default=None, help="Update an existing observation to this status")
    p.set_defaults(func=cmd_validation_observations)




    p = sub.add_parser("operations-event-record", help="Record a shared operational lifecycle event")
    p.add_argument("--event", required=True, help="Path to operational event JSON")
    p.add_argument("--allow-extension-event-type", action="store_true", help="Allow non-standard event_type while preserving the event envelope")
    p.set_defaults(func=cmd_operations_event_record)

    p = sub.add_parser("operations-status-summary", help="Summarize active and recent operational activity")
    p.set_defaults(func=cmd_operations_status_summary)

    p = sub.add_parser("work-package-ranges", help="Inspect local-first work package range allocations")
    p.add_argument("--json", action="store_true", help="Print range ledger JSON")
    p.set_defaults(func=cmd_work_package_ranges)

    p = sub.add_parser("workstream", help="Inspect or validate a staged workstream install manifest")
    p.add_argument("action", choices=["inspect", "validate"], help="Workstream action")
    p.add_argument("--id", required=True, help="Work package id, such as WP-0112")
    p.add_argument("--json", action="store_true", help="Print JSON output")
    p.set_defaults(func=cmd_workstream)

    p = sub.add_parser("validation-production-readiness", help="Generate production readiness validation report")
    p.add_argument("--json", action="store_true", help="Print production readiness report JSON")
    p.set_defaults(func=cmd_validation_production_readiness)


    p = sub.add_parser("alfred-runtime", help="Build read-only Alfred runtime event briefings")
    ar_sub = p.add_subparsers(dest="alfred_runtime_action", required=True)
    q = ar_sub.add_parser("event-brief", help="Render a deterministic non-executing Alfred event briefing")
    q.add_argument("--sample", action="store_true", help="Use a deterministic sample event")
    q.add_argument("--event-type", default="manual_steward_note", help="Event type when not using --sample")
    q.add_argument("--source", default="manual", help="Event source when not using --sample")
    q.add_argument("--source-artifact", action="append", help="Source artifact for non-sample event")
    q.add_argument("--verbosity", default="standard", choices=["brief", "standard", "mid", "detailed", "forensic"], help="Briefing verbosity")
    q.add_argument("--json", action="store_true", help="Print event and briefing JSON")
    q.set_defaults(func=cmd_alfred_runtime)

    p = sub.add_parser("validate-work-package", help="Run a registered work-package validation recipe")
    p.add_argument("--id", required=True, help="Work package id, such as WP-0058")
    p.add_argument("--json", action="store_true", help="Print validation report JSON")
    p.set_defaults(func=cmd_validate_work_package)

    p = sub.add_parser("codex-bridge", help="Run a bounded local Codex Bridge request")
    p.add_argument("--request", required=True, help="Path to Codex Bridge request JSON")
    p.add_argument("--dry-run", action="store_true", help="Validate and emit visibility artifacts without invoking Codex")
    p.add_argument("--json", action="store_true", help="Print Codex Bridge result JSON")
    p.set_defaults(func=cmd_codex_bridge)


    p = sub.add_parser("codex-bridge-adapter", help="Validate and dry-run Codex Bridge adapter requests without live provider calls")
    cba_sub = p.add_subparsers(dest="codex_bridge_adapter_action", required=True)
    q = cba_sub.add_parser("validate", help="Validate a Codex Bridge adapter request JSON file")
    q.add_argument("--request", required=True, help="Path to adapter request JSON")
    q.add_argument("--json", action="store_true", help="Print adapter validation JSON")
    q.set_defaults(func=cmd_codex_bridge_adapter)
    q = cba_sub.add_parser("dry-run", help="Run Codex Bridge adapter dry-run and write artifacts")
    q.add_argument("--request", required=True, help="Path to adapter request JSON")
    q.add_argument("--json", action="store_true", help="Print dry-run result JSON")
    q.set_defaults(func=cmd_codex_bridge_adapter)


    p = sub.add_parser("execution-provider-adapter", help="Validate provider-neutral adapter requests and deterministic dry runs")
    adapter_sub = p.add_subparsers(dest="execution_provider_adapter_action", required=True)
    q = adapter_sub.add_parser("validate", help="Validate an adapter request JSON file")
    q.add_argument("--request", required=True, help="Path to adapter request JSON")
    q.add_argument("--json", action="store_true", help="Print adapter validation JSON")
    q.set_defaults(func=cmd_execution_provider_adapter)
    q = adapter_sub.add_parser("dry-run", help="Run the deterministic dry-run adapter and write artifacts")
    q.add_argument("--request", required=True, help="Path to adapter request JSON")
    q.add_argument("--json", action="store_true", help="Print dry-run result JSON")
    q.set_defaults(func=cmd_execution_provider_adapter)


    p = sub.add_parser("execution-adapter-handoff", help="Prepare and validate dispatch-to-adapter handoffs without live provider calls")
    handoff_sub = p.add_subparsers(dest="execution_adapter_handoff_action", required=True)
    for action in ("prepare", "inspect", "validate", "dry-run"):
        q = handoff_sub.add_parser(action, help=f"{action} a dispatch-to-adapter handoff")
        q.add_argument("--dispatch-id", required=True, help="Execution dispatch item id")
        q.add_argument("--json", action="store_true", help="Print handoff JSON")
        q.set_defaults(func=cmd_execution_adapter_handoff)


    p = sub.add_parser("codex-live-execution", help="Preview or execute Steward-authorized local Codex execution")
    live_sub = p.add_subparsers(dest="codex_live_execution_action", required=True)
    for action in ("preview", "execute"):
        q = live_sub.add_parser(action, help=f"{action} a Steward-authorized live Codex execution")
        q.add_argument("--dispatch-id", required=True, help="Execution dispatch item id")
        q.add_argument("--authorization", required=True, help="Path to live execution authorization JSON")
        if action == "execute":
            q.add_argument("--confirm-live-execution", action="store_true", help="Deliberate operator confirmation required for provider call")
        q.add_argument("--json", action="store_true", help="Print live execution JSON")
        q.set_defaults(func=cmd_codex_live_execution)
    for action in ("status", "report"):
        q = live_sub.add_parser(action, help=f"{action} live execution state")
        q.add_argument("--dispatch-id", required=True, help="Execution dispatch item id")
        q.add_argument("--json", action="store_true", help="Print live execution JSON")
        q.set_defaults(func=cmd_codex_live_execution)




    p = sub.add_parser("execution-attempt", help="Inspect execution attempt leases, cancellation, recovery, and retry evidence")
    attempt_sub = p.add_subparsers(dest="execution_attempt_action", required=True)
    q = attempt_sub.add_parser("status", help="Show execution attempt status")
    q.add_argument("--dispatch-id", help="Execution dispatch item id")
    q.add_argument("--json", action="store_true", help="Print attempt status JSON")
    q.set_defaults(func=cmd_execution_attempt)
    q = attempt_sub.add_parser("cancel-request", help="Record a cancellation request and use cooperative process-control seam")
    q.add_argument("--dispatch-id", required=True)
    q.add_argument("--attempt-id", required=True)
    q.add_argument("--reason", required=True)
    q.add_argument("--requested-by", default="operator")
    q.add_argument("--json", action="store_true")
    q.set_defaults(func=cmd_execution_attempt)
    q = attempt_sub.add_parser("inspect-recovery", help="Classify active execution attempt recovery state")
    q.add_argument("--dispatch-id", required=True)
    q.add_argument("--json", action="store_true")
    q.set_defaults(func=cmd_execution_attempt)
    q = attempt_sub.add_parser("release-stale", help="Explicitly release a proven stale execution lease")
    q.add_argument("--dispatch-id", required=True)
    q.add_argument("--attempt-id", required=True)
    q.add_argument("--confirm-stale-release", action="store_true")
    q.add_argument("--released-by", default="operator")
    q.add_argument("--reason", default="explicit stale release")
    q.add_argument("--json", action="store_true")
    q.set_defaults(func=cmd_execution_attempt)
    q = attempt_sub.add_parser("retry-eligibility", help="Generate retry eligibility evidence without starting retry")
    q.add_argument("--dispatch-id", required=True)
    q.add_argument("--json", action="store_true")
    q.set_defaults(func=cmd_execution_attempt)

    p = sub.add_parser("execution-result-reconciliation", help="Inspect and reconcile provider adapter results back into dispatch lifecycle")
    recon_sub = p.add_subparsers(dest="execution_result_reconciliation_action", required=True)
    q = recon_sub.add_parser("inspect", help="Inspect reconciliation state for a dispatch item")
    q.add_argument("--dispatch-id", required=True, help="Execution dispatch item id")
    q.add_argument("--json", action="store_true", help="Print reconciliation JSON")
    q.set_defaults(func=cmd_execution_result_reconciliation)
    q = recon_sub.add_parser("reconcile", help="Reconcile an adapter result JSON file")
    q.add_argument("--dispatch-id", required=True, help="Execution dispatch item id")
    q.add_argument("--result", required=True, help="Path to adapter result JSON")
    q.add_argument("--json", action="store_true", help="Print reconciliation JSON")
    q.set_defaults(func=cmd_execution_result_reconciliation)
    q = recon_sub.add_parser("report", help="Render a reconciliation report")
    q.add_argument("--dispatch-id", required=True, help="Execution dispatch item id")
    q.add_argument("--json", action="store_true", help="Print reconciliation JSON instead of Markdown")
    q.set_defaults(func=cmd_execution_result_reconciliation)

    p = sub.add_parser("execution-activity", help="Generate the shared local execution activity snapshot")
    p.add_argument("--json", action="store_true", help="Print execution activity current snapshot JSON")
    p.set_defaults(func=cmd_execution_activity)

    p = sub.add_parser("execution-activity-report", help="Generate the shared local execution activity report")
    p.set_defaults(func=cmd_execution_activity_report)

    p = sub.add_parser("execution-dispatch", help="Manage the local provider-agnostic execution dispatch queue")
    dispatch_sub = p.add_subparsers(dest="execution_dispatch_action", required=True)

    q = dispatch_sub.add_parser("enqueue", help="Enqueue a dispatch request JSON file")
    q.add_argument("--file", required=True, help="Path to dispatch request JSON")
    q.add_argument("--json", action="store_true", help="Print enqueued dispatch item JSON")
    q.set_defaults(func=cmd_execution_dispatch)

    q = dispatch_sub.add_parser("list", help="List dispatch queue items")
    q.add_argument("--state", help="Optional state filter")
    q.add_argument("--json", action="store_true", help="Print dispatch queue JSON")
    q.set_defaults(func=cmd_execution_dispatch)

    q = dispatch_sub.add_parser("inspect", help="Inspect one dispatch item")
    q.add_argument("dispatch_id")
    q.add_argument("--json", action="store_true", help="Print dispatch item JSON")
    q.set_defaults(func=cmd_execution_dispatch)

    q = dispatch_sub.add_parser("update-state", help="Update a dispatch item state")
    q.add_argument("dispatch_id")
    q.add_argument("--state", required=True, choices=sorted({"Queued", "Waiting", "Ready", "Running", "Blocked", "Awaiting Approval", "Validation", "Completed", "Failed", "Cancelled"}))
    q.add_argument("--summary", help="Optional event summary")
    q.add_argument("--json", action="store_true", help="Print dispatch item JSON")
    q.set_defaults(func=cmd_execution_dispatch)

    q = dispatch_sub.add_parser("block", help="Mark a dispatch item blocked with a reason")
    q.add_argument("dispatch_id")
    q.add_argument("--reason", required=True)
    q.add_argument("--json", action="store_true", help="Print dispatch item JSON")
    q.set_defaults(func=cmd_execution_dispatch)

    q = dispatch_sub.add_parser("attention", help="Mark or clear Steward attention on a dispatch item")
    q.add_argument("dispatch_id")
    q.add_argument("--reason")
    q.add_argument("--clear", action="store_true", help="Clear the attention flag")
    q.add_argument("--json", action="store_true", help="Print dispatch item JSON")
    q.set_defaults(func=cmd_execution_dispatch)

    q = dispatch_sub.add_parser("cancel", help="Cancel a dispatch item")
    q.add_argument("dispatch_id")
    q.add_argument("--reason")
    q.add_argument("--json", action="store_true", help="Print dispatch item JSON")
    q.set_defaults(func=cmd_execution_dispatch)

    q = dispatch_sub.add_parser("complete", help="Complete a dispatch item")
    q.add_argument("dispatch_id")
    q.add_argument("--result-reference")
    q.add_argument("--json", action="store_true", help="Print dispatch item JSON")
    q.set_defaults(func=cmd_execution_dispatch)

    q = dispatch_sub.add_parser("prepare-handoff", help="Write a Codex Bridge dry-run handoff request")
    q.add_argument("dispatch_id")
    q.add_argument("--json", action="store_true", help="Print handoff request JSON")
    q.set_defaults(func=cmd_execution_dispatch)

    q = dispatch_sub.add_parser("snapshot", help="Generate the current dispatch queue snapshot")
    q.add_argument("--json", action="store_true", help="Print current dispatch snapshot JSON")
    q.set_defaults(func=cmd_execution_dispatch)

    p = sub.add_parser("execution-dispatch-report", help="Generate the local execution dispatch queue report")
    p.set_defaults(func=cmd_execution_dispatch_report)

    p = sub.add_parser("validation-metrics-dashboard", help="Generate Validation Metrics Dashboard")
    p.add_argument("--json", action="store_true", help="Print validation metrics dashboard JSON")
    p.set_defaults(func=cmd_validation_metrics_dashboard)

    p = sub.add_parser("operational-readiness-dashboard", help="Generate Operational Readiness Dashboard")
    p.add_argument("--json", action="store_true", help="Print operational readiness dashboard JSON")
    p.set_defaults(func=cmd_operational_readiness_dashboard)

    p = sub.add_parser("validation-handoff-artifact-workflow", help="Generate Validation Handoff Artifact Workflow packet")
    p.add_argument("--json", action="store_true", help="Print validation handoff workflow JSON")
    p.set_defaults(func=cmd_validation_handoff_artifact_workflow)

    p = sub.add_parser("operational-validation")
    p.add_argument("--json", action="store_true", help="Generate operational validation report and print JSON")
    p.set_defaults(func=cmd_operational_validation)

    p = sub.add_parser("steward-dashboard")
    p.add_argument("--json", action="store_true", help="Generate Steward dashboard and print JSON")
    p.set_defaults(func=cmd_steward_dashboard)

    p = sub.add_parser("mailbox-index")
    p.add_argument("--json", action="store_true", help="Generate mailbox index and print JSON summary")
    p.set_defaults(func=cmd_mailbox_index)

    p = sub.add_parser("personnel-resolve")
    p.add_argument("--actor", required=True, help="Actor, employee id, mailbox id, office alias, resident, or worker to resolve")
    p.add_argument("--json", action="store_true", help="Print resolver output as JSON")
    p.set_defaults(func=cmd_personnel_resolve)

    p = sub.add_parser("audit")
    p.add_argument("--json", action="store_true", help="Print machine-readable audit report JSON")
    p.add_argument("--save", action="store_true", help="Save latest audit report to runtime/audit/latest.json")
    p.set_defaults(func=cmd_audit)



    p = sub.add_parser("notification-router")
    p.add_argument("--json", action="store_true", help="Generate notification router report and print JSON")
    p.set_defaults(func=cmd_notification_router)


    p = sub.add_parser("gotify-send-test")
    p.add_argument("--dry-run", action="store_true", help="Validate Gotify payload without contacting Gotify")
    p.add_argument("--json", action="store_true", help="Print Gotify delivery report JSON")
    p.set_defaults(func=cmd_gotify_send_test)

    p = sub.add_parser("estate-health")
    p.add_argument("--json", action="store_true", help="Print Estate health report JSON")
    p.set_defaults(func=cmd_estate_health)

    p = sub.add_parser("alfred-artifacts")
    p.add_argument("--json", action="store_true", help="Print Alfred artifact index JSON")
    p.set_defaults(func=cmd_alfred_artifacts)

    p = sub.add_parser("alfred-cleanup")
    p.add_argument("--keep", type=int, default=100, help="Number of most recent jobs to keep")
    p.add_argument("--json", action="store_true", help="Print Alfred cleanup result JSON")
    p.set_defaults(func=cmd_alfred_cleanup)

    p = sub.add_parser("alfred-briefing")
    p.add_argument("--json", action="store_true", help="Print Alfred operator briefing JSON")
    p.set_defaults(func=cmd_alfred_briefing)

    p = sub.add_parser("alfred-operational-briefing")
    p.add_argument("--json", action="store_true", help="Generate Alfred operational briefing and print JSON")
    p.set_defaults(func=cmd_alfred_briefing)

    p = sub.add_parser("alfred")
    p.add_argument("--json", action="store_true", help="Print Alfred operator briefing JSON")
    p.set_defaults(func=cmd_alfred_briefing)

    p = sub.add_parser("alfred-triage")
    p.add_argument("--json", action="store_true", help="Print Alfred request triage JSON")
    p.set_defaults(func=cmd_alfred_triage)

    p = sub.add_parser("alfred-request")
    p.add_argument("goal", help="Goal to queue as an Alfred request")
    p.add_argument("--json", action="store_true", help="Print Alfred request JSON")
    p.set_defaults(func=cmd_alfred_request)

    p = sub.add_parser("alfred-requests")
    p.add_argument("--json", action="store_true", help="Print queued Alfred requests JSON")
    p.set_defaults(func=cmd_alfred_requests)

    p = sub.add_parser("alfred-promote")
    p.add_argument("request_id", help="Alfred request id to promote into a job")
    p.add_argument("--json", action="store_true", help="Print promotion result JSON")
    p.set_defaults(func=cmd_alfred_promote)

    p = sub.add_parser("alfred-status")
    p.add_argument("--json", action="store_true", help="Print Alfred operator status JSON")
    p.set_defaults(func=cmd_alfred_status)

    p = sub.add_parser("alfred-task")
    p.add_argument("goal", help="Goal for Alfred to complete as one task")
    p.add_argument("--json", action="store_true", help="Print Alfred task result JSON")
    p.set_defaults(func=cmd_alfred_task)

    p = sub.add_parser("ask-alfred")
    p.add_argument("goal", help="Goal for Alfred to complete as one task")
    p.add_argument("--json", action="store_true", help="Print Alfred task result JSON")
    p.set_defaults(func=cmd_alfred_task)

    p = sub.add_parser("alfred-plan")
    p.add_argument("goal", help="Goal for Alfred to plan")
    p.add_argument("--json", action="store_true", help="Print Alfred plan JSON")
    p.set_defaults(func=cmd_alfred_plan)

    p = sub.add_parser("alfred-run")
    p.add_argument("goal", help="Goal for Alfred to prepare as a runtime job")
    p.add_argument("--json", action="store_true", help="Print Alfred job JSON")
    p.set_defaults(func=cmd_alfred_run)




    p = sub.add_parser("alfred-result")
    p.add_argument("job_id", help="Runtime Alfred job id")
    p.add_argument("--json", action="store_true", help="Print Alfred job result JSON")
    p.set_defaults(func=cmd_alfred_result)

    p = sub.add_parser("alfred-inspect")
    p.add_argument("job_id", help="Runtime Alfred job id")
    p.add_argument("--json", action="store_true", help="Print Alfred job inspection JSON")
    p.set_defaults(func=cmd_alfred_inspect)

    p = sub.add_parser("alfred-cancel")
    p.add_argument("job_id", help="Runtime Alfred job id")
    p.add_argument("--json", action="store_true", help="Print Alfred cancel result JSON")
    p.set_defaults(func=cmd_alfred_cancel)

    p = sub.add_parser("alfred-retry")
    p.add_argument("job_id", help="Runtime Alfred job id")
    p.add_argument("--json", action="store_true", help="Print Alfred retry result JSON")
    p.set_defaults(func=cmd_alfred_retry)

    p = sub.add_parser("alfred-policy")
    p.add_argument("--json", action="store_true", help="Print Alfred execution policy JSON")
    p.set_defaults(func=cmd_alfred_policy)

    p = sub.add_parser("alfred-execute")
    p.add_argument("job_id", help="Runtime Alfred job id")
    p.add_argument("--json", action="store_true", help="Print Alfred execution result JSON")
    p.set_defaults(func=cmd_alfred_execute)

    p = sub.add_parser("alfred-jobs")
    p.add_argument("--json", action="store_true", help="Print Alfred runtime jobs JSON")
    p.set_defaults(func=cmd_alfred_jobs)

    p = sub.add_parser("capability-help")
    p.add_argument("--json", action="store_true", help="Print Estate capability help JSON")
    p.set_defaults(func=cmd_capability_help)

    p = sub.add_parser("service-readiness")
    p.add_argument("--json", action="store_true", help="Print Estate service readiness JSON")
    p.set_defaults(func=cmd_service_readiness)

    p = sub.add_parser("service-status")
    p.add_argument("--json", action="store_true", help="Print Estate service status JSON")
    p.set_defaults(func=cmd_service_status)

    p = sub.add_parser("service-route")
    p.add_argument("capability", help="Capability to route, such as image.generate or code.write")
    p.add_argument("--json", action="store_true", help="Print service route JSON")
    p.set_defaults(func=cmd_service_route)

    p = sub.add_parser("alfred-capabilities")
    p.add_argument("--json", action="store_true", help="Print Alfred capability surface JSON")
    p.set_defaults(func=cmd_alfred_capabilities)


    p = sub.add_parser("planning-provider-run", help="Run an Estate planning provider request from JSON")
    p.add_argument("--request", required=True, help="Path to planning provider request JSON")
    p.set_defaults(func=cmd_planning_provider_run)



    p = sub.add_parser("orchestrator-cycle", help="Run one bounded Orchestrator cycle without provider execution")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true", help="Evaluate work and status without writing dispatch records")
    group.add_argument("--single", action="store_true", help="Run one cycle and write dispatch records")
    p.set_defaults(func=cmd_orchestrator_cycle)

    p = sub.add_parser("orchestrator-dispatch-list", help="List Orchestrator dispatch queue records")
    p.add_argument("--json", action="store_true", help="Print dispatch queue JSON")
    p.set_defaults(func=cmd_orchestrator_dispatch_list)

    p = sub.add_parser("orchestrator-schedule", help="Schedule eligible approved Orchestrator intake without executing providers")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--intake-id", help="Approved intake id to schedule")
    group.add_argument("--request", help="Path to schedule request/intake JSON")
    p.add_argument("--scheduled-by", default="orchestrator", help="Actor recording the schedule")
    p.add_argument("--defer", action="store_true", help="Explicitly defer otherwise eligible scheduling")
    p.set_defaults(func=cmd_orchestrator_schedule)

    p = sub.add_parser("orchestrator-schedule-list", help="List Orchestrator schedule queue state")
    p.add_argument("--json", action="store_true", help="Print schedule queue JSON")
    p.set_defaults(func=cmd_orchestrator_schedule_list)

    p = sub.add_parser("orchestrator-intake-submit", help="Submit an Orchestrator intake request from JSON")
    p.add_argument("--request", required=True, help="Path to Orchestrator intake request JSON")
    p.set_defaults(func=cmd_orchestrator_intake_submit)

    p = sub.add_parser("orchestrator-intake-list", help="List Orchestrator intake queue state")
    p.add_argument("--json", action="store_true", help="Print queue state JSON")
    p.set_defaults(func=cmd_orchestrator_intake_list)

    p = sub.add_parser("orchestrator-intake-decide", help="Record a governed decision for a pending or blocked Orchestrator intake item")
    p.add_argument("--intake-id", required=True, help="Pending or blocked intake id")
    p.add_argument("--decision", required=True, choices=["approve", "reject", "defer", "request_boundary_review", "mark_needs_revision"], help="Allowed intake decision")
    p.add_argument("--decided-by", required=True, help="Person or office recording the decision")
    p.add_argument("--reason", default=None, help="Optional governed decision reason")
    p.add_argument("--summary-safe", action="store_true", help="Mark the decision summary safe for Office display")
    p.add_argument("--boundary-review-completed", action="store_true", help="Indicate required boundary review was completed before approval")
    p.set_defaults(func=cmd_orchestrator_intake_decide)

    p = sub.add_parser("onboarding-manifest-check")
    p.add_argument("--json", action="store_true", help="Validate onboarding manifest required paths and print JSON")
    p.set_defaults(func=cmd_onboarding_manifest_check)


    p = sub.add_parser("hr-onboard", help="Run Helen HR employee onboarding orchestration")
    p.add_argument("--name", required=True)
    p.add_argument("--department", required=True)
    p.add_argument("--office", required=True)
    p.add_argument("--role", required=True)
    p.add_argument("--classification", required=True)
    p.add_argument("--package-type", default="worker", choices=["worker", "chief_architect", "standard"])
    p.add_argument("--steward-authorization", required=True, help="Steward authorization evidence or reference")
    p.add_argument("--dry-run", action="store_true", help="Validate and report without writing artifacts")
    p.add_argument("--json", action="store_true", help="Print onboarding result JSON")
    p.set_defaults(func=cmd_hr_onboard)

    p = sub.add_parser("helen-onboard", help="Alias for Helen HR employee onboarding orchestration")
    p.add_argument("--name", required=True)
    p.add_argument("--department", required=True)
    p.add_argument("--office", required=True)
    p.add_argument("--role", required=True)
    p.add_argument("--classification", required=True)
    p.add_argument("--package-type", default="worker", choices=["worker", "chief_architect", "standard"])
    p.add_argument("--steward-authorization", required=True, help="Steward authorization evidence or reference")
    p.add_argument("--dry-run", action="store_true", help="Validate and report without writing artifacts")
    p.add_argument("--json", action="store_true", help="Print onboarding result JSON")
    p.set_defaults(func=cmd_hr_onboard)

    p = sub.add_parser("work-package-handoffs", help="List pending work packages and copy-ready Codex launch commands")
    p.set_defaults(func=cmd_work_package_handoffs)

    p = sub.add_parser("estate-search", help="Search local institutional Estate artifacts")
    p.add_argument("query", help="Keyword query to search for")
    p.add_argument("--json", action="store_true", help="Print search results JSON")
    p.add_argument("--root", help="Estate root path to search; defaults to the current working directory")
    p.add_argument("--no-refresh", action="store_true", help="Use existing runtime search index if present")
    p.set_defaults(func=cmd_estate_search)

    p = sub.add_parser("global-search", help="Search artifacts and registered command palette entries")
    p.add_argument("query", nargs="?", default="", help="Keyword query to search for")
    p.add_argument("--json", action="store_true", help="Print global search results JSON")
    p.add_argument("--no-refresh", action="store_true", help="Use existing runtime palette index if present")
    p.set_defaults(func=cmd_global_search)

    p = sub.add_parser("palette-command", help="Look up a registered command palette command")
    p.add_argument("command_id", help="Registered command id")
    p.add_argument("--json", action="store_true", help="Print command lookup JSON")
    p.set_defaults(func=cmd_palette_command)

    p = sub.add_parser("document-registry", help="Print the stable Estate document registry")
    p.add_argument("--json", action="store_true", help="Print document registry JSON")
    p.set_defaults(func=cmd_document_registry)

    p = sub.add_parser("check-updates")
    p.add_argument("--actor", default=None, help="Actor requesting the update briefing")
    p.add_argument("--json", action="store_true", help="Print Check for Updates report JSON")
    p.set_defaults(func=cmd_check_updates)

    p = sub.add_parser("mailbox-sync-duty")
    p.add_argument("--actor", default=None, help="Actor whose mailbox synchronization duty should be checked")
    p.add_argument("--json", action="store_true", help="Print mailbox synchronization duty report JSON")
    p.set_defaults(func=cmd_mailbox_sync_duty)


    p = sub.add_parser("assignment-queue", help="Generate Estate work package assignment queue")
    p.add_argument("--json", action="store_true", help="Print assignment queue JSON")
    p.set_defaults(func=cmd_assignment_queue)


    p = sub.add_parser("autonomous-work-queue-scheduler", help="Generate the local advisory autonomous work queue scheduler")
    p.add_argument("--json", action="store_true", help="Print scheduler JSON")
    p.set_defaults(func=cmd_autonomous_work_queue_scheduler)


    p = sub.add_parser("autonomous-operations-audit", help="Append an Autonomous Operations Audit Trail record")
    p.add_argument("--json", action="store_true", help="Print appended audit record JSON")
    p.set_defaults(func=cmd_autonomous_operations_audit)

    p = sub.add_parser("decision-queue", help="Generate the local Steward Decision Queue panel")
    p.add_argument("--json", action="store_true", help="Print decision queue JSON")
    p.set_defaults(func=cmd_decision_queue)


    p = sub.add_parser("operations-center-settings", help="Inspect or update local Operations Center UI settings")
    p.add_argument("--json", action="store_true", help="Print Settings Manager JSON")
    p.add_argument("--theme", choices=["light", "dark", "system"], help="Set appearance theme")
    p.add_argument("--accent", choices=["estate-gold", "blue", "green", "neutral"], help="Set accent theme")
    p.add_argument("--default-workspace-profile", help="Set default workspace profile")
    p.add_argument("--default-verbosity-profile", help="Set default operator verbosity profile")
    p.add_argument("--global-verbosity", choices=["quiet", "normal", "detailed", "diagnostic"], help="Set global operator verbosity")
    p.add_argument("--refresh-mode", choices=["quiet", "manual"], help="Set refresh mode")
    p.add_argument("--quiet-refresh-seconds", type=int, help="Set quiet refresh interval")
    p.add_argument("--command-console-mode", choices=["inline", "collapsed"], help="Set command console mode")
    p.set_defaults(func=cmd_operations_center_settings)


    p = sub.add_parser("alfred-duty", help="Run Alfred local bounded duty runner")
    p.add_argument("--json", action="store_true", help="Print Alfred duty JSON")
    p.set_defaults(func=cmd_alfred_duty)

    p = sub.add_parser("helen-duty", help="Run Helen local bounded duty runner")
    p.add_argument("--json", action="store_true", help="Print Helen duty JSON")
    p.set_defaults(func=cmd_helen_duty)

    p = sub.add_parser("resident-duty", help="Run resident duty runner where implemented")
    p.add_argument("--resident", required=True, help="Resident name")
    p.add_argument("--json", action="store_true", help="Print resident duty JSON")
    p.set_defaults(func=cmd_resident_duty)

    p = sub.add_parser("resident-presence", help="Inspect local resident runtime presence")
    p.add_argument("--resident", help="Filter by resident name or id")
    p.add_argument("--json", action="store_true", help="Print resident presence JSON")
    p.set_defaults(func=cmd_resident_presence)


    p = sub.add_parser("resident-authority", help="Check or list resident action authority boundaries")
    p.add_argument("action", choices=["check", "list"], help="Authority action")
    p.add_argument("--resident", help="Resident name")
    p.add_argument("--action", dest="resident_action", help="Requested resident action category")
    p.add_argument("--target", help="Action target or artifact path")
    p.add_argument("--source-ref", action="append", help="Additional source artifact reference")
    p.add_argument("--json", action="store_true", help="Print resident authority JSON")
    p.set_defaults(func=cmd_resident_authority)

    p = sub.add_parser("resident-conversation", help="Create and inspect local resident conversation session audit records")
    p.add_argument("action", choices=["start", "list", "show"], help="Conversation session action")
    p.add_argument("--resident", help="Resident name for start/list")
    p.add_argument("--session", help="Session id for show")
    p.add_argument("--participant-role", default="operator", help="Participant role for a started session")
    p.add_argument("--status", default="open", help="Session status")
    p.add_argument("--source-artifact", action="append", help="Source artifact reference used during the session")
    p.add_argument("--prompt", help="Prompt or operator question to record")
    p.add_argument("--response", help="Resident response to record")
    p.add_argument("--operator-note", help="Operator note or session event to record")
    p.add_argument("--outcome", default="informational", choices=["informational", "needs_steward", "work_package_candidate", "decision_candidate", "validation_follow_up", "no_action"], help="Non-authoritative session outcome label")
    p.add_argument("--canonical-link", action="append", help="Canonical follow-up artifact link")
    p.add_argument("--json", action="store_true", help="Print resident conversation JSON")
    p.set_defaults(func=cmd_resident_conversation)


    p = sub.add_parser("resident-chat", help="Send, list, or forget local resident interaction chat")
    p.add_argument("action", choices=["send", "history", "forget"], help="Chat action")
    p.add_argument("--resident", default="alfred", help="Resident id or name")
    p.add_argument("--message", default="", help="Steward message for send")
    p.add_argument("--session", help="Resident interaction session id")
    p.add_argument("--turn", help="Turn id to forget/redact")
    p.add_argument("--memory-status", default="forgotten", choices=["forgotten", "redacted"], help="Forget/redaction marker")
    p.add_argument("--reason", default="Steward-directed forget/redaction", help="Audit reason")
    p.add_argument("--action", dest="resident_action", help="Requested resident action category")
    p.add_argument("--include-forgotten", action="store_true", help="Include forgotten/redacted content placeholders in history")
    p.add_argument("--json", action="store_true", help="Print resident chat JSON")
    p.set_defaults(func=cmd_resident_chat)

    p = sub.add_parser("resident-interaction-surface", help="Inspect resident API/surface")
    p.add_argument("--resident", required=True, help="Resident id or name")
    p.add_argument("--json", action="store_true", help="Print surface JSON")
    p.set_defaults(func=cmd_resident_interaction_surface)

    p = sub.add_parser("operations-center", help="Start, inspect, or stop the local Operations Center server")
    p.add_argument("action", choices=["start", "status", "stop"], help="Server lifecycle action")
    p.add_argument("--json", action="store_true", help="Print bootstrap status JSON")
    p.add_argument("--host", default="127.0.0.1", help="Local bind host for start")
    p.add_argument("--port", type=int, default=8765, help="Local bind port for start/status URL")
    p.set_defaults(func=cmd_operations_center)

    p = sub.add_parser("steward-command-center", help="Generate or serve the local Office of the Steward command center")
    p.add_argument("--json", action="store_true", help="Print command center payload JSON")
    p.add_argument("--serve", action="store_true", help="Serve the dashboard locally over HTTP")
    p.add_argument("--host", default="127.0.0.1", help="Local bind host for --serve")
    p.add_argument("--port", type=int, default=8765, help="Local bind port for --serve")
    p.set_defaults(func=cmd_steward_command_center)

    p = sub.add_parser("worker-heartbeat", help="Record a local Estate worker runtime heartbeat")
    p.add_argument("worker_id", help="Worker identity or route id")
    p.add_argument("--activity", required=True, help="Current worker activity reported in this heartbeat")
    p.add_argument("--status", required=True, choices=["idle", "active", "blocked", "offline"], help="Reported worker status")
    p.add_argument("--last-completed-work-package", default=None, help="Most recent completed work package id")
    p.add_argument("--blocking-reason", default=None, help="Required when status is blocked")
    p.add_argument("--json", action="store_true", help="Print heartbeat result JSON")
    p.set_defaults(func=cmd_worker_heartbeat)

    p = sub.add_parser("worker-runtime-summary", help="Generate Worker Runtime Heartbeat summary")
    p.add_argument("--stale-after-minutes", type=int, default=60, help="Flag heartbeats older than this as stale")
    p.add_argument("--json", action="store_true", help="Print runtime summary JSON")
    p.set_defaults(func=cmd_worker_runtime_summary)

    p = sub.add_parser("worker-runtime-monitor", help="Generate Worker Runtime Monitor summary")
    p.add_argument("--stale-after-minutes", type=int, default=60, help="Flag worker heartbeats older than this as stale")
    p.add_argument("--json", action="store_true", help="Print runtime monitor JSON")
    p.set_defaults(func=cmd_worker_runtime_monitor)

    p = sub.add_parser("steward-presence", help="Generate Steward Presence and Recall state report")
    p.add_argument("--json", action="store_true", help="Print Steward presence state JSON")
    p.set_defaults(func=cmd_steward_presence)

    p = sub.add_parser("morning-briefing")
    p.add_argument("--json", action="store_true", help="Generate Morning Briefing v1 and print JSON")
    p.set_defaults(func=cmd_morning_briefing)

    p = sub.add_parser("estate-validate-local")
    p.add_argument("--json", action="store_true", help="Run local operational validation and print JSON")
    p.set_defaults(func=cmd_estate_validate_local)






    p = sub.add_parser("operational-targets", help="List and control Background Operations operational targets")
    ot = p.add_subparsers(dest="operational_targets_action", required=True)
    for name in ["list", "status"]:
        q = ot.add_parser(name); q.add_argument("--json", action="store_true"); q.set_defaults(func=cmd_operational_targets)
    q = ot.add_parser("show"); q.add_argument("--target", required=True); q.add_argument("--json", action="store_true"); q.set_defaults(func=cmd_operational_targets)
    q = ot.add_parser("resolve"); q.add_argument("--target", required=True); q.add_argument("--json", action="store_true"); q.set_defaults(func=cmd_operational_targets)
    q = ot.add_parser("binding"); q.add_argument("--target", required=True); q.add_argument("--json", action="store_true"); q.set_defaults(func=cmd_operational_targets)
    q = ot.add_parser("aliases"); q.add_argument("--json", action="store_true"); q.set_defaults(func=cmd_operational_targets)
    for name in ["enable", "pause", "resume", "disable", "retire", "import-candidate"]:
        q = ot.add_parser(name); q.add_argument("--target", required=True); q.add_argument("--json", action="store_true"); q.set_defaults(func=cmd_operational_targets)

    p = sub.add_parser("background-operations", help="Evaluate and inspect event-driven background operation requests")
    bo = p.add_subparsers(dest="background_operations_action", required=True)
    q = bo.add_parser("cycle", help="Run one deterministic background operations evaluation cycle")
    q.add_argument("--json", action="store_true")
    q.set_defaults(func=cmd_background_operations)
    q = bo.add_parser("watches", help="List background operation watches")
    q.add_argument("--json", action="store_true")
    q.set_defaults(func=cmd_background_operations)
    q = bo.add_parser("requests", help="List generated background operation requests")
    q.add_argument("--json", action="store_true")
    q.set_defaults(func=cmd_background_operations)
    q = bo.add_parser("status", help="Show background operations status")
    q.add_argument("--json", action="store_true")
    q.set_defaults(func=cmd_background_operations)
    q = bo.add_parser("report", help="Render background operations markdown report")
    q.set_defaults(func=cmd_background_operations)


    p = sub.add_parser("merge-discovery", help="Discover local merges/promotions and create post-merge audit requests")
    md = p.add_subparsers(dest="merge_discovery_action", required=True)
    for name in ["scan", "status", "candidates", "replay"]:
        q = md.add_parser(name)
        q.add_argument("--target", default="estate-main")
        q.add_argument("--max-commits", type=int, default=50 if name == "replay" else 100)
        q.add_argument("--json", action="store_true")
        q.set_defaults(func=cmd_merge_discovery)

    p = sub.add_parser("post-merge-audit", help="Process pending automatic post-merge audit requests")
    pma = p.add_subparsers(dest="post_merge_audit_action", required=True)
    q = pma.add_parser("process-next", help="Claim and process one pending audit request")
    q.add_argument("--json", action="store_true")
    q.set_defaults(func=cmd_post_merge_audit)
    q = pma.add_parser("process-all", help="Process pending audit requests")
    q.add_argument("--max", type=int, default=10)
    q.add_argument("--json", action="store_true")
    q.set_defaults(func=cmd_post_merge_audit)
    q = pma.add_parser("demonstrate", help="Create and process a demonstration audit request")
    q.add_argument("--work-package", required=True)
    q.add_argument("--pr")
    q.add_argument("--json", action="store_true")
    q.set_defaults(func=cmd_post_merge_audit)
    q = pma.add_parser("status", help="Show post-merge audit processor status")
    q.add_argument("--json", action="store_true")
    q.set_defaults(func=cmd_post_merge_audit)

    p = sub.add_parser("operations-runtime", help="Run and inspect the bounded Operations Runtime service loop")
    ort = p.add_subparsers(dest="operations_runtime_action", required=True)
    q = ort.add_parser("run-once", help="Run one Operations Runtime cycle")
    q.add_argument("--json", action="store_true")
    q.add_argument("--dry-run", action="store_true")
    q.add_argument("--process-audits", action="store_true")
    q.add_argument("--process-audits-and-ring2", action="store_true")
    q.add_argument("--discover-merges", action="store_true")
    q.set_defaults(func=cmd_operations_runtime)
    q = ort.add_parser("start", help="Run a bounded Operations Runtime loop")
    q.add_argument("--max-cycles", type=int, default=1)
    q.add_argument("--interval-seconds", type=float, default=30.0)
    q.add_argument("--json", action="store_true")
    q.add_argument("--dry-run", action="store_true")
    q.add_argument("--process-audits", action="store_true")
    q.add_argument("--process-audits-and-ring2", action="store_true")
    q.add_argument("--discover-merges", action="store_true")
    q.set_defaults(func=cmd_operations_runtime)
    q = ort.add_parser("status", help="Show Operations Runtime status")
    q.add_argument("--json", action="store_true")
    q.set_defaults(func=cmd_operations_runtime)
    q = ort.add_parser("request-stop", help="Request the bounded loop to stop")
    q.add_argument("--json", action="store_true")
    q.set_defaults(func=cmd_operations_runtime)
    q = ort.add_parser("report", help="Render Operations Runtime report")
    q.set_defaults(func=cmd_operations_runtime)

    p = sub.add_parser("provider-routing-recommendation", help="Evaluate or explain provider routing recommendations without dispatch or provider calls")
    p.add_argument("provider_routing_action", choices=["evaluate", "explain"], help="Recommendation action")
    p.add_argument("--request", required=True, help="Path to provider routing recommendation request JSON")
    p.add_argument("--json", action="store_true", help="Print recommendation JSON")
    p.set_defaults(func=cmd_provider_routing_recommendation)

    p = sub.add_parser("providers-list", help="List registered provider descriptors")
    p.add_argument("--json", action="store_true", help="Print provider catalog status JSON")
    p.set_defaults(func=cmd_providers_list)

    p = sub.add_parser("providers-show", help="Inspect one registered provider descriptor")
    p.add_argument("--provider-id", required=True, help="Provider ID to inspect")
    p.add_argument("--json", action="store_true", help="Print provider descriptor JSON")
    p.set_defaults(func=cmd_providers_show)

    p = sub.add_parser("providers-find", help="Find providers by capability ID")
    p.add_argument("--capability", required=True, help="Capability ID to match")
    p.add_argument("--json", action="store_true", help="Print matching providers JSON")
    p.set_defaults(func=cmd_providers_find)


    p = sub.add_parser("providers-health-set", help="Record manual provider health")
    p.add_argument("--provider-id", required=True)
    p.add_argument("--status", required=True, choices=["available", "degraded", "saturated", "out_of_quota", "blocked", "offline", "unknown"])
    p.add_argument("--reported-by", required=True)
    p.add_argument("--message", required=True)
    p.add_argument("--classification", default="Estate Internal", choices=["Public", "Estate Internal", "Restricted", "Steward Only", "Local Only"])
    p.add_argument("--source", default="manual")
    p.add_argument("--summary-safe", action="store_true")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_providers_health_set)

    p = sub.add_parser("providers-capacity-set", help="Record manual provider capacity")
    p.add_argument("--provider-id", required=True)
    p.add_argument("--capacity-state", required=True, choices=["idle", "available", "busy", "saturated", "quota_limited", "unknown"])
    p.add_argument("--reported-by", required=True)
    p.add_argument("--classification", default="Estate Internal", choices=["Public", "Estate Internal", "Restricted", "Steward Only", "Local Only"])
    p.add_argument("--active-jobs", type=int, default=0)
    p.add_argument("--max-jobs", type=int)
    p.add_argument("--queue-depth", type=int, default=0)
    p.add_argument("--quota-remaining")
    p.add_argument("--message")
    p.add_argument("--summary-safe", action="store_true")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_providers_capacity_set)

    p = sub.add_parser("providers-health-summary", help="Summarize provider health and capacity")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_providers_health_summary)


    p = sub.add_parser("worker-assignment-create", help="Create a file-backed worker assignment record")
    p.add_argument("--assigned-to", required=True)
    p.add_argument("--assigned-by", required=True)
    p.add_argument("--mission", required=True)
    p.add_argument("--summary")
    p.add_argument("--work-package-id")
    p.add_argument("--work-package-path")
    p.add_argument("--assignment-label")
    p.add_argument("--worker-id")
    p.add_argument("--worker-role")
    p.add_argument("--provider-id")
    p.add_argument("--provider-type")
    p.add_argument("--seat-id")
    p.add_argument("--profile-id")
    p.add_argument("--intake-id")
    p.add_argument("--schedule-id")
    p.add_argument("--classification", default="Estate Internal", choices=["Public", "Estate Internal", "Restricted", "Steward Only", "Local Only"])
    p.add_argument("--priority", default="normal", choices=["low", "normal", "high", "urgent"])
    p.add_argument("--state", default="assigned", choices=["assigned", "accepted", "running", "blocked", "awaiting_approval", "reviewing", "validation", "completed", "failed", "cancelled", "deferred"])
    p.add_argument("--expected-output", action="append")
    p.add_argument("--no-validation-required", action="store_true")
    p.add_argument("--requires-attention", action="store_true")
    p.add_argument("--blocked-reason")
    p.add_argument("--summary-safe", action="store_true")
    p.set_defaults(func=cmd_worker_assignment_create)

    p = sub.add_parser("worker-assignment-update", help="Update a worker assignment state")
    p.add_argument("--assignment-id", required=True)
    p.add_argument("--state", required=True, choices=["assigned", "accepted", "running", "blocked", "awaiting_approval", "reviewing", "validation", "completed", "failed", "cancelled", "deferred"])
    p.add_argument("--blocked-reason")
    p.add_argument("--requires-attention", action="store_true")
    p.add_argument("--summary-safe", action="store_true")
    p.set_defaults(func=cmd_worker_assignment_update)

    p = sub.add_parser("worker-assignment-list", help="List worker assignments and refresh board artifacts")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_worker_assignment_list)


    p = sub.add_parser("operations-review", help="Generate Traffic Controller / Operations Manager review")
    p.add_argument("--classification", default="Estate Internal", choices=["Public", "Estate Internal", "Restricted", "Steward Only", "Local Only"])
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_operations_review)

    p = sub.add_parser("operations-decide", help="Record an operations control decision")
    p.add_argument("--decision-type", required=True, choices=["assign", "reprioritize", "hold", "release", "defer", "cancel", "escalate", "request_boundary_review", "request_revision", "request_validation"])
    p.add_argument("--target-type", required=True, choices=["intake", "schedule", "dispatch", "assignment", "provider", "work_package", "system"])
    p.add_argument("--target-id")
    p.add_argument("--classification", default="Estate Internal", choices=["Public", "Estate Internal", "Restricted", "Steward Only", "Local Only"])
    p.add_argument("--priority", default="normal", choices=["low", "normal", "high", "urgent"])
    p.add_argument("--decided-by", required=True)
    p.add_argument("--reason", required=True)
    p.add_argument("--next-state")
    p.add_argument("--assignment-label")
    p.add_argument("--provider-id")
    p.add_argument("--worker-id")
    p.add_argument("--seat-id")
    p.add_argument("--requires-boundary-review", action="store_true")
    p.add_argument("--requires-steward-attention", action="store_true")
    p.add_argument("--summary-safe", action="store_true")
    p.set_defaults(func=cmd_operations_decide)

    p = sub.add_parser("operations-decisions-list", help="List recorded operations decisions")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_operations_decisions_list)

    p = sub.add_parser("audit-summary")
    p.add_argument("--json", action="store_true", help="Print saved audit summary JSON")
    p.set_defaults(func=cmd_audit_summary)

    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return
    args.func(args)

if __name__ == "__main__":
    main()
