import argparse
from estate.core.ledger import create_change
from estate.core.residents import register_resident
from estate.core.registry import load_registry
from estate.core.services import list_services, list_capabilities, list_providers
from estate.core.discovery import observe_ai_environment
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

def cmd_discover_ai(args):
    observations, out = observe_ai_environment()
    print(f"Wrote observation: {out}")
    print(f"AI_HOME exists: {observations['exists']['ai_home']}")
    print(f"Python envs: {', '.join(observations['python_envs']) if observations['python_envs'] else '(none)'}")
    print(f"TTS items: {', '.join(observations['tts_items']) if observations['tts_items'] else '(none)'}")
    print(f"Tools: {', '.join(observations['tool_items']) if observations['tool_items'] else '(none)'}")
    print(f"Model categories: {', '.join(observations['model_categories']) if observations['model_categories'] else '(none)'}")

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

    p = sub.add_parser("discover-ai")
    p.set_defaults(func=cmd_discover_ai)

    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        return
    args.func(args)

if __name__ == "__main__":
    main()
