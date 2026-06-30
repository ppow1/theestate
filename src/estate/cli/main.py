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
from estate.core.service_layer import service_status, route_capability, alfred_capabilities, format_service_status, format_alfred_capabilities
from estate.core.alfred import plan_goal, create_job, list_jobs, format_plan, format_job, format_jobs, execute_job, format_execution_result, inspect_job, cancel_job, retry_job, get_execution_policy, format_job_inspection, format_execution_policy, get_job_result, format_job_result, run_task, format_task_result, alfred_status, format_alfred_status, create_request, list_requests, promote_request, format_requests, alfred_briefing, format_alfred_briefing, get_job_result, format_job_result, run_task, format_task_result, alfred_status, format_alfred_status, create_request, list_requests, promote_request, format_requests, alfred_briefing, format_alfred_briefing
from estate.core.audit import print_audit_report
from estate.core.audit_runtime import save_audit_report, summarize_audit_artifact, format_audit_summary
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
    print_table(list_services(), ["id", "name", "status", "owner", "resident"])

def cmd_capabilities(args):
    print_table(list_capabilities(), ["id", "name", "category", "status", "location"])

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



def cmd_alfred_briefing(args):
    payload = alfred_briefing()
    if getattr(args, "json", False):
        import json
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(format_alfred_briefing(payload))


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
        print(format_alfred_capabilities(payload))

def cmd_audit_summary(args):
    summary = summarize_audit_artifact()
    if getattr(args, "json", False):
        import json
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(format_audit_summary(summary))

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
    p.set_defaults(func=cmd_services)

    p = sub.add_parser("capabilities")
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

    p = sub.add_parser("audit")
    p.add_argument("--json", action="store_true", help="Print machine-readable audit report JSON")
    p.add_argument("--save", action="store_true", help="Save latest audit report to runtime/audit/latest.json")
    p.set_defaults(func=cmd_audit)



    p = sub.add_parser("alfred-briefing")
    p.add_argument("--json", action="store_true", help="Print Alfred operator briefing JSON")
    p.set_defaults(func=cmd_alfred_briefing)

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


