# Engineering Capacity Runtime

The Engineering Capacity Runtime combines provider health/capacity evidence with local worker runtime evidence into an Office-readable dashboard. Engineering Provider Capacity is an advisory provider-availability index. It is not physical GPU utilization, GPU capacity, or an Estate-wide composite resource percentage; RTX 4090 and Tesla P100 records are outside this calculation.

## Artifacts

- `runtime/engineering_capacity/dashboard.json` - machine-readable dashboard.
- `runtime/engineering_capacity/dashboard.md` - runtime Markdown dashboard.
- `operations/engineering_capacity/runtime_dashboard.md` - staged Office install handoff.

## Command

```bash
python -m estate.cli.main engineering-capacity-dashboard
```

The runtime is advisory only. It does not launch workers, consume cloud Codex seats, or schedule work.

Provider freshness is evaluated from the latest provider health/capacity observation (`last_checked_at`). The default threshold is 30 minutes through `stale_after_minutes`; older evidence is shown as `stale`, while missing or invalid observation time is `unknown`. A stale numeric index remains visible with its stale state; missing evidence remains unknown rather than becoming 0. Each provider is rendered separately. When both are available, `quota_remaining / max_jobs` overrides the state mapping.

## Verified Codex Seat-Capacity Evidence — 2026-07-12

Evidence source: repeated Steward observation across three actively monitored Codex business seats, including refreshed Codex Analytics pages.

Verified facts:

- Codex usage quota is tracked independently per business seat.
- Three seats are currently being monitored through separate Chrome profiles for this workflow.
- Additional local browser identities exist, but they are not part of the three-seat monitoring method described here.
- After refresh, the current Codex Analytics interface exposes a weekly usage limit for each observed seat.
- The previously visible five-hour usage card disappears after refresh.
- Each observed seat has its own weekly remaining percentage and reset timestamp.

Current evidence classification:

- `weekly_quota_visible`: verified current provider-UI evidence.
- `quota_scope`: verified per-seat through repeated Steward observation.
- `five_hour_quota_visible`: false in the refreshed current UI.
- `five_hour_backend_enforcement`: unknown; absence from the UI is not evidence of removal from backend policy.
- `active_monitored_seat_count`: 3.

## Modeling Requirement

Capacity must be modeled at the execution-seat level whenever the provider meters seats independently.

Canonical hierarchy:

```text
Provider
  -> Seat
      -> Worker or execution context
          -> Assignment
```

Provider-level capacity is an aggregate derived from seat-level evidence. It must not replace seat-level scheduling evidence.

Each Codex seat record should support:

- stable Estate seat identifier;
- provider account reference without exposing credentials;
- observation timestamp;
- weekly remaining percentage;
- weekly reset timestamp;
- current assignment or reservation;
- queue depth;
- health and authentication state;
- evidence source and confidence;
- UI-schema version or observed field set;
- stale/unknown indicators;
- short-window throttle state as `unknown`, `observed`, or `enforced` rather than assuming a five-hour meter exists.

The dashboard should present three currently monitored Codex seats individually and aggregate them only as a secondary provider summary. It must not infer that the total number of Chrome profiles equals the number of active Codex seats.
