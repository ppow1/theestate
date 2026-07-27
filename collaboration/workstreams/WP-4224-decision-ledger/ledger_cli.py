#!/usr/bin/env python3
"""Read-only diagnostics for a previously materialized WP-4224 ledger."""
import argparse
import json
from pathlib import Path
from decision_ledger.ledger import LedgerError, query, validate_ledger


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ledger", type=Path)
    parser.add_argument("command", choices=("recommendations", "history", "show", "compare", "lineage", "validate", "explain"))
    parser.add_argument("identifiers", nargs="*")
    args = parser.parse_args(argv)
    try:
        ledger = json.loads(args.ledger.read_text(encoding="utf-8"))
        if args.command == "validate": result = {"valid": not validate_ledger(ledger)}
        elif args.command == "recommendations": result = query(ledger, "current")
        elif args.command == "history": result = query(ledger, "history", args.identifiers[0] if args.identifiers else None)
        elif args.command == "lineage": result = query(ledger, "lineage", args.identifiers[0] if args.identifiers else None)
        elif args.command in ("show", "explain"):
            if len(args.identifiers) != 1: raise LedgerError(f"{args.command} requires one identifier")
            rows = query(ledger, "current", args.identifiers[0])
            if not rows: raise LedgerError("unknown recommendation")
            result = rows[0] if args.command == "show" else {"recommendation": rows[0], "history": query(ledger, "history", args.identifiers[0])}
        else:
            if len(args.identifiers) != 2: raise LedgerError("compare requires two identifiers")
            rows = [query(ledger, "current", identifier) for identifier in args.identifiers]
            if any(not row for row in rows): raise LedgerError("unknown recommendation")
            result = {"left": rows[0][0], "right": rows[1][0], "score_delta_left_minus_right": rows[0][0]["score"] - rows[1][0]["score"]}
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (OSError, json.JSONDecodeError, LedgerError) as error:
        parser.exit(2, f"error: {error}\n")


if __name__ == "__main__": raise SystemExit(main())
