# WP-4225 Engineering Campaign Effectiveness Analytics

This staged, deterministic subsystem measures historical outcomes from the published WP-4220 queue, WP-4221 dashboard, WP-4222 integration snapshot, WP-4223 recommendations, and WP-4224 decision ledger. It does not regenerate those sources and has no operational authority, writers, repository adapters, scheduler, dispatcher, or worker assignment facilities.

## Preflight and classification

The supplied local base is merge commit `6006e37`: WP-4220 (#474), WP-4221 (#475), WP-4222 (#476), WP-4223 (#478), and WP-4224 (#479) are present. This checkout has no configured remote, so `main` synchronization and push are unavailable; the merged local base was reconciled without changing authoritative state. Searches for engineering/campaign/recommendation/decision analytics, metrics, history, reporting, and trends found the dashboard metrics model and WP-4224's disposition-count query, but no historical effectiveness analytics subsystem. Classification: `partially_implemented`; published projections, hashes, and decision records are reused, while historical calculations are implemented here.

## Use

```bash
python analytics_cli.py analytics fixtures/healthy_campaign.json --generated-at 2026-07-02T00:00:00Z
python analytics_cli.py summary SNAPSHOT.json
python analytics_cli.py trend HISTORY.json weekly
python analytics_cli.py compare LEFT.json RIGHT.json
python analytics_cli.py history SNAPSHOTS.json
python analytics_cli.py validate SNAPSHOT.json
python analytics_cli.py explain SNAPSHOT.json --metric acceptance_rate
```

All commands are read-only and emit JSON to stdout. Timestamps are caller supplied. Canonical JSON (sorted keys, compact separators, UTF-8, trailing newline) is SHA-256 hashed, making replay byte-for-byte deterministic for identical inputs.
