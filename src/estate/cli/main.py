import argparse
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
from estate.core.operational_readiness_dashboard import generate_operational_readiness_dashboard, format_operational_readiness_summary
from estate.core.steward_presence import generate_steward_presence_state, format_steward_presence_state
from estate.core.assignment_queue import generate_assignment_queue, format_assignment_queue_markdown
from estate.core.autonomous_work_queue_scheduler import generate_autonomous_work_queue_scheduler, format_autonomous_work_queue_scheduler
from estate.core.autonomous_operations_audit import append_autonomous_operations_audit, format_autonomous_operations_audit
from estate.core.steward_command_center import generate_command_center, serve_command_center
from estate.core.operations_center_bootstrap import operations_center_start, operations_center_status, operations_center_stop, format_operations_center_bootstrap
from estate.core.operations_center_workspace_profiles import resolve_workspace_profile, save_workspace_profile
from estate.core.operations_center_settings import load_operations_center_settings, save_operations_center_settings
from estate.core.decision_queue import generate_decision_queue, format_decision_queue_markdown
from estate.core.resident_presence import build_resident_presence, filter_resident, format_resident_presence
from estate.core.alfred_duty import run_alfred_duty, format_alfred_duty
from estate.core.paths import ESTATE_ROOT, LEDGER_PATH, DEVLOG_PATH

def print_table(items, fields):
    if not items:
        print("No records.")
        return
    for item in items:
        print(" | ".join(str(item.get(field, "")) for field in fields))

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
    result = search_institutional_index(args.query, refresh=not getattr(args, "no_refresh", False))
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


def cmd_resident_duty(args):
    resident = getattr(args, "resident", None)
    if resident and resident.lower() != "alfred":
        raise SystemExit("Only Alfred duty is implemented by WP-0107.")
    cmd_alfred_duty(args)


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

    payload = generate_command_center()
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


def cmd_validate_work_package(args):
    import json
    payload = validate_work_package(args.id)
    if getattr(args, "json", False):
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(format_validation_markdown(payload))
    if payload.get("validation_status") in {"failed", "no_recipe"}:
        raise SystemExit(1)


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

def cmd_sync_ollama(args):
    created, ec_id = sync_ollama_providers()
    print(f"Logged {ec_id}")
    if created:
        for provider in created:
            print(f"Created {provider['id']}: {provider['name']}")
    else:
        print("No new Ollama providers created.")

def main():
    parser = argparse.ArgumentParser(prog="estate", description="Estate Core CLI")
    sub = parser.add_subparsers(dest="command")

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


    p = sub.add_parser("validation-production-readiness", help="Generate production readiness validation report")
    p.add_argument("--json", action="store_true", help="Print production readiness report JSON")
    p.set_defaults(func=cmd_validation_production_readiness)

    p = sub.add_parser("validate-work-package", help="Run a registered work-package validation recipe")
    p.add_argument("--id", required=True, help="Work package id, such as WP-0058")
    p.add_argument("--json", action="store_true", help="Print validation report JSON")
    p.set_defaults(func=cmd_validate_work_package)

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

    p = sub.add_parser("resident-duty", help="Run resident duty runner where implemented")
    p.add_argument("--resident", required=True, help="Resident name")
    p.add_argument("--json", action="store_true", help="Print resident duty JSON")
    p.set_defaults(func=cmd_resident_duty)

    p = sub.add_parser("resident-presence", help="Inspect local resident runtime presence")
    p.add_argument("--resident", help="Filter by resident name or id")
    p.add_argument("--json", action="store_true", help="Print resident presence JSON")
    p.set_defaults(func=cmd_resident_presence)

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

    p = sub.add_parser("audit-summary")
    p.add_argument("--json", action="store_true", help="Print saved audit summary JSON")
    p.set_defaults(func=cmd_audit_summary)

    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        return
    args.func(args)

if __name__ == "__main__":
    main()

