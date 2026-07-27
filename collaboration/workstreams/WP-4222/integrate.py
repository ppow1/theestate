#!/usr/bin/env python3
"""Offline command for the WP-4222 staged integration evidence."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dashboard_integration import IntegrationError, compose_dashboard, load_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="WP-4222 staged dashboard integration")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = compose_dashboard(load_manifest(args.manifest))
        rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
        if args.output:
            destination = args.output.resolve()
            sources = {p.path for p in load_manifest(args.manifest).discover()}
            if destination in sources or any(source.parent == destination for source in sources):
                raise IntegrationError("output overlaps a registered provider")
            destination.parent.mkdir(parents=True, exist_ok=True)
            temporary = destination.with_suffix(destination.suffix + ".tmp")
            temporary.write_text(rendered, encoding="utf-8")
            temporary.replace(destination)
        else:
            print(rendered, end="")
        return 0
    except IntegrationError as exc:
        print(f"integration error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
