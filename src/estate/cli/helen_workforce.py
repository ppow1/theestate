"""Standalone CLI for Helen workforce-development records.

Invoke with:
    python -m estate.cli.helen_workforce <action> [options]

This keeps Helen's first implementation local-first and avoids coupling the
workforce artifact store to the large Estate CLI parser until the interface is
validated in use.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from estate.core.helen_workforce import (
    HelenWorkforceStore,
    WorkforceAssessment,
    WorkforceRequest,
)


def _load_json(path: str) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object in {path}")
    return payload


def _print(payload: dict, *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return

    kind = payload.get("kind")
    if kind == "request_created":
        print(f"Helen workforce request created: {payload['request']['request_id']}")
        print(f"Type: {payload['request']['request_type']}")
        print(f"Subject: {payload['request']['subject_type']}:{payload['request']['subject_id']}")
        print(f"Status: {payload['request']['status']}")
        print(f"Boundary review required: {payload['request']['requires_boundary_review']}")
        print(f"Artifact: {payload['path']}")
    elif kind == "assessment_created":
        print(f"Helen workforce assessment created: {payload['assessment']['assessment_id']}")
        print(f"Request: {payload['assessment']['request_id']}")
        print(f"Subject: {payload['assessment']['subject_id']}")
        print(f"Status: {payload['request_status']}")
        print(f"Recommendations: {', '.join(payload['assessment']['recommendations']) or 'none'}")
        print(f"Artifact: {payload['path']}")
    elif kind == "status":
        summary = payload["status"]["summary"]
        print("Helen Workforce Development")
        print(f"Open requests: {summary['open_requests']}")
        print(f"In review: {summary['in_review_requests']}")
        print(f"Ready for action: {summary['ready_for_action_requests']}")
        print(f"Boundary reviews: {summary['boundary_review_count']}")
        print(f"Steward attention: {summary['steward_attention_count']}")
        print(f"Assessments: {summary['assessment_count']}")
    elif kind == "request":
        request = payload["request"]
        print(f"Request: {request['request_id']}")
        print(f"Type: {request['request_type']}")
        print(f"Subject: {request['subject_type']}:{request['subject_id']}")
        print(f"Status: {request['status']}")
        print(f"Summary: {request['summary']}")
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="estate-helen-workforce",
        description="Create and inspect governed Helen workforce artifacts.",
    )
    parser.add_argument(
        "--root",
        help="Estate repository root. Defaults to the configured Estate root or current directory.",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    sub = parser.add_subparsers(dest="action", required=True)

    create_request = sub.add_parser("request-create", help="Create a workforce request from JSON.")
    create_request.add_argument("--file", required=True, help="Path to a WorkforceRequest JSON object.")

    create_assessment = sub.add_parser("assessment-create", help="Create an assessment from JSON.")
    create_assessment.add_argument("--file", required=True, help="Path to a WorkforceAssessment JSON object.")

    show_request = sub.add_parser("request-show", help="Show one workforce request.")
    show_request.add_argument("--request-id", required=True)

    sub.add_parser("requests-list", help="List all workforce requests.")
    sub.add_parser("assessments-list", help="List all workforce assessments.")
    sub.add_parser("status", help="Generate and display workforce status.")
    return parser


def run(argv: Sequence[str] | None = None) -> dict:
    args = build_parser().parse_args(argv)
    root = Path(args.root).resolve() if args.root else None
    store = HelenWorkforceStore(root)

    if args.action == "request-create":
        request = WorkforceRequest.from_dict(_load_json(args.file))
        path = store.save_request(request)
        payload = {
            "kind": "request_created",
            "request": request.to_dict(),
            "path": str(path),
            "operational_queue_control_performed": False,
            "provider_execution_performed": False,
            "constitutional_authority_granted": False,
        }
    elif args.action == "assessment-create":
        assessment = WorkforceAssessment.from_dict(_load_json(args.file))
        path = store.save_assessment(assessment)
        request = store.load_request(assessment.request_id)
        payload = {
            "kind": "assessment_created",
            "assessment": assessment.to_dict(),
            "request_status": request.status,
            "path": str(path),
            "operational_queue_control_performed": False,
            "provider_execution_performed": False,
            "constitutional_authority_granted": False,
        }
    elif args.action == "request-show":
        request = store.load_request(args.request_id)
        payload = {"kind": "request", "request": request.to_dict()}
    elif args.action == "requests-list":
        payload = {
            "kind": "requests",
            "requests": [request.to_dict() for request in store.list_requests()],
        }
    elif args.action == "assessments-list":
        payload = {
            "kind": "assessments",
            "assessments": [assessment.to_dict() for assessment in store.list_assessments()],
        }
    elif args.action == "status":
        payload = {"kind": "status", "status": store.write_status()}
    else:  # pragma: no cover - argparse prevents this branch
        raise ValueError(f"unknown action: {args.action}")

    _print(payload, as_json=args.json)
    return payload


def main() -> None:
    try:
        run()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Helen workforce command failed: {exc}") from exc


if __name__ == "__main__":
    main()
