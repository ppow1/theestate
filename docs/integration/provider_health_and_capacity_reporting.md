# Provider Health and Capacity Reporting

Status: Implemented  
Classification: Estate Internal

## Purpose

This layer records manually supplied provider health and capacity so future scheduling can inspect provider availability before assigning work. It does not execute providers, scrape accounts, or perform live quota checks.

## Health Model

Health records are represented by `ProviderHealthRecord` with provider identity, check timestamp, reporter, status, classification, message, source, optional expiration, capability availability lists, attention flag, and metadata. Allowed statuses are `available`, `degraded`, `saturated`, `out_of_quota`, `blocked`, `offline`, and `unknown`.

## Capacity Model

Capacity records are represented by `ProviderCapacityRecord` with provider identity, check timestamp, reporter, capacity state, active jobs, optional maximum jobs, queue depth, optional quota fields, classification, message, and metadata. Allowed capacity states are `idle`, `available`, `busy`, `saturated`, `quota_limited`, and `unknown`.

## Runtime Artifacts

The runtime surface is written under:

- `runtime/providers/health/records/`
- `runtime/providers/health/status/latest.json`
- `runtime/providers/health/status/latest_capacity.json`
- `runtime/providers/health/status/summary.json`
- `runtime/providers/health/status/summary.md`

## CLI Examples

```powershell
Clear-Host
cd A:\theestate
.\estate.bat providers-health-set --provider-id codex.execution.cli --status available --reported-by Steward --message "C2 available"
.\estate.bat providers-capacity-set --provider-id codex.execution.cli --capacity-state busy --active-jobs 1 --reported-by Steward
.\estate.bat providers-health-summary
```

Use `--summary-safe` only when the message is safe for Office-readable summaries. Use `--force` to record unknown, deprecated, or blocked catalog providers intentionally.

## Provider Catalog Integration

When `config/providers/catalog.json` is available, CLI and writer helpers validate provider IDs, enrich summaries with display name and provider type, and block records for deprecated or blocked providers unless `--force` is supplied. If the catalog is unavailable, manual recording is allowed with a clear warning.

## Operational Event Integration

Health records for `degraded`, `saturated`, `out_of_quota`, `blocked`, and `offline` emit compatible operational events through the existing event/status layer. This gives future Office and Orchestrator surfaces a bridge without requiring scheduler changes.

## Office Consumption Notes

Office-readable summaries should consume `runtime/providers/health/status/summary.json` or `summary.md`. Structural fields such as provider ID, health state, capacity state, active jobs, and queue depth are safe to display by default.

## Boundary Behavior

Messages classified `Restricted`, `Steward Only`, or `Local Only` are redacted from summaries unless metadata contains `summary_safe: true`. Provider summaries must not contain secrets, tokens, raw account identifiers, private prompts, or personal data.

## Future Probe Notes

Future packages may add provider-specific probes that create the same health and capacity records. Those probes should not bypass classification, redaction, catalog validation, or operational event hooks.
