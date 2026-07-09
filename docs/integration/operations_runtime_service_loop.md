# Operations Runtime Service Loop

The Operations Runtime is a bounded local service loop for development sessions. It observes Operational Targets, evaluates Background Operations watches, creates governed requests such as post-merge audit or Ring 2 review requests, publishes Office status, writes a heartbeat, and exits or sleeps for the next bounded cycle.

## Commands

```bash
python -m estate.cli.main operations-runtime run-once --json
python -m estate.cli.main operations-runtime start --max-cycles 5 --interval-seconds 30 --json
python -m estate.cli.main operations-runtime status --json
python -m estate.cli.main operations-runtime request-stop --json
python -m estate.cli.main operations-runtime report
```

## Artifacts

- `runtime/operations_runtime/status/latest.json`
- `runtime/operations_runtime/status/summary.json`
- `runtime/operations_runtime/heartbeat.json`
- `runtime/operations_runtime/lock.json`
- `runtime/operations_runtime/reports/latest.md`
- `runtime/operations_runtime/cycles/<cycle_id>.json`

## Authority Boundary

The runtime may observe, evaluate, request, and report. It does not execute providers, dispatch work, approve changes, accept merges, repair code, stash active tree dirtiness, or create institutional truth.

## Development Session Use

Start the loop at the beginning of a working session with a small `--max-cycles` and `--interval-seconds 0` for deterministic local validation, or a larger interval for live local monitoring. Use `request-stop` to ask a repeated loop to stop at the next safe boundary.
