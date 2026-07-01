# Steward Dashboard Runtime View

Status: Implemented runtime view  
Audience: Steward-facing operators, Alfred-adjacent workers, Chief Architect sessions

## Purpose

The Steward Dashboard is a concise, human-facing runtime view of current Estate operational status. It summarizes existing artifacts rather than creating new governance, new lifecycle states, or a replacement for the Operations Board.

## Command

Generate the dashboard with:

```bash
python -m estate.cli.main steward-dashboard
```

For machine-readable output:

```bash
python -m estate.cli.main steward-dashboard --json
```

## Inputs

The generator uses these existing artifacts when present:

- `runtime/operations/operations_board.json`
- `operations/board/latest.md`
- `runtime/capabilities/capability_lifecycle_report.json`
- `collaboration/status/worker_inbox_summary.json`
- `runtime/audit/latest.json`
- `collaboration/audit/results/*.json`

Missing artifacts are reported as warnings and do not stop dashboard generation. Malformed JSON artifacts are also reported as warnings.

## Outputs

The command writes:

- `runtime/steward/dashboard.json`
- `operations/steward/dashboard.md`

## Dashboard Sections

The generated dashboard includes:

- Current operational summary
- Active, blocked, and review-pending work when known from available artifacts
- Audit status
- Worker inbox status
- Capability lifecycle summary
- Warnings requiring Steward attention
- Items not requiring Steward action

## Boundaries

This runtime view does not directly edit the ledger or devlog. It does not redefine Alfred, redesign the Operations Board, create governance, or introduce lifecycle states beyond the Estate lifecycle standard.
