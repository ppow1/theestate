"""Canonical WP-4228 inspection and fixture-proof CLI."""
import argparse
import json
from pathlib import Path

from estate.core.engineering_campaign_operations import CampaignStore, EngineeringCampaignOperations


def run(argv=None):
    parser = argparse.ArgumentParser(prog="estate-engineering-campaign")
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--sources", type=Path)
    parser.add_argument("--action", choices=["inspect", "proof"], default="inspect")
    parser.add_argument("--classification", default="create_Grace_operational_objective")
    args = parser.parse_args(argv)
    operations = EngineeringCampaignOperations(CampaignStore(args.store))
    if args.action == "inspect":
        result = operations.inspect()
    else:
        sources = json.loads(args.sources.read_text(encoding="utf-8")) if args.sources else []
        snapshot = operations.reconcile(sources)
        recommendation = operations.recommend(snapshot, args.classification)
        decision = operations.decide(recommendation, "accepted", "Engineering", "Fixture proof authorization")
        translation = operations.translate(recommendation, decision)
        operations.fixture_execute(translation)
        result = operations.inspect()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
