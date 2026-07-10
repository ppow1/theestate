from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from estate.core.institutional_learning import InstitutionalLearningStore, InstitutionalLesson


def _load_json(path: str) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object in {path}")
    return data


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="estate-institutional-learning")
    parser.add_argument("--root")
    parser.add_argument("--json", action="store_true")
    sub = parser.add_subparsers(dest="action", required=True)
    p = sub.add_parser("intake")
    p.add_argument("--file", required=True)
    p = sub.add_parser("close")
    p.add_argument("--lesson-id", required=True)
    p.add_argument("--closure-summary", required=True)
    p = sub.add_parser("show")
    p.add_argument("--lesson-id", required=True)
    sub.add_parser("list")
    sub.add_parser("status")
    return parser


def _print(payload: dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return
    if payload["kind"] == "intake":
        lesson = payload["lesson"]
        print(f"Institutional lesson accepted: {lesson['lesson_id']} ({lesson['status']})")
        print(f"Owner: {lesson['recommended_owner']}")
        print(f"Checkpoint: {lesson['follow_up_checkpoint']}")
    elif payload["kind"] == "status":
        summary = payload["status"]["summary"]
        print(f"Institutional lessons: {summary['lesson_count']}")
        print(f"Duplicates: {summary['duplicate_count']}")
        print(f"Closed: {summary['closed_count']}")
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))


def run(argv: Sequence[str] | None = None) -> dict:
    args = build_parser().parse_args(argv)
    store = InstitutionalLearningStore(Path(args.root).resolve() if args.root else None)
    if args.action == "intake":
        lesson = InstitutionalLesson.create(**_load_json(args.file))
        path = store.intake(lesson)
        payload = {"kind": "intake", "lesson": lesson.to_dict(), "path": str(path)}
    elif args.action == "close":
        lesson = store.close(args.lesson_id, args.closure_summary)
        payload = {"kind": "closed", "lesson": lesson.to_dict()}
    elif args.action == "show":
        payload = {"kind": "lesson", "lesson": store.load(args.lesson_id).to_dict()}
    elif args.action == "list":
        payload = {"kind": "lessons", "lessons": [l.to_dict() for l in store.list_lessons()]}
    elif args.action == "status":
        payload = {"kind": "status", "status": store.write_status()}
    else:
        raise ValueError(args.action)
    _print(payload, args.json)
    return payload


def main() -> None:
    try:
        run()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Institutional learning command failed: {exc}") from exc

if __name__ == "__main__":
    main()
