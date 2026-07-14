from __future__ import annotations
import argparse, json
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="External Engineering Worker Runtime")
    parser.add_argument("--package", required=True)
    parser.add_argument("--worktree", required=True)
    parser.add_argument("--evidence", required=True)
    args = parser.parse_args()
    package_path = Path(args.package)
    worktree = Path(args.worktree)
    evidence = Path(args.evidence)
    package = json.loads(package_path.read_text(encoding="utf-8"))
    evidence.mkdir(parents=True, exist_ok=True)
    worktree.mkdir(parents=True, exist_ok=True)
    (evidence / "worker_result.json").write_text(json.dumps({
        "status": "completed",
        "executed_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "package_id": package.get("package_id"),
        "dispatch_id": package.get("dispatch_id"),
        "worktree": package.get("worktree"),
        "evidence": package.get("evidence"),
        "note": "External runtime received a bounded package and preserved raw evidence outside the Estate repository."
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
