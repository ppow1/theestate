# Engineering Campaign Operations — Operator Guide

Use `PYTHONPATH=src python -m estate.cli.engineering_campaign_operations --store <path> --action inspect` for read-only status. Fixture proof additionally requires `--action proof --sources <json>`. Confirm `ledger_valid: true`; stop on low confidence, hash mismatch, unknown authority, or missing conditions. Do not use the proof as live-provider authorization.
