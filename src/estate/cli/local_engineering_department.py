from __future__ import annotations
import argparse, json
from pathlib import Path
from estate.core.local_engineering_department import LocalEngineeringDepartment, format_closed_loop_result

def main(argv=None):
    parser = argparse.ArgumentParser(description="Estate local engineering department runtime")
    sub = parser.add_subparsers(dest="cmd", required=True)
    run = sub.add_parser("run-closed-loop")
    run.add_argument("--root", type=Path)
    run.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if args.cmd == "run-closed-loop":
        result = LocalEngineeringDepartment(root=args.root).run_closed_loop()
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True) if args.json else format_closed_loop_result(result))

if __name__ == "__main__":
    main()
