# PTM Production Dependency and Readiness Resolver

Status: Implementation of the first bounded PTM production-authority work package; downstream consumers are intentionally not wired.

## Authority

`estate.core.ptm_production_readiness.PtmProductionReadinessResolver` is owned by PTM/orchestrator. Grace, Helen, Engineering, Dispatch, provider catalogs, and execution providers do not calculate or override its result.

The resolver reads the canonical PTM event ledger under `runtime/ptm/ledger/events/`. Planning manifests, `runtime/dependencies/dependency_graph.json`, provider availability, Helen evidence, and repository file presence are not readiness authority.

## Persistence

Events use the CORE-PTM-002A envelope and SHA-256 hash chain. Events are immutable create-once JSON records at:

```text
runtime/ptm/ledger/events/<stream>/<sequence>_<event_id>.json
```

Readiness resolutions are immutable derived records at:

```text
runtime/ptm/readiness/<resolution_id>.json
```

No prior event or resolution is overwritten. The resolver uses an idempotency key derived from the canonical inputs, policy, schema, and source high-watermark. Repeating the same request returns the existing equivalent resolution; changed source state requires a new resolution.

## Decision rules

Dependency states are `unsatisfied`, `satisfied`, `waived`, and `unknown`. Gate states are `pass`, `fail`, `waived`, and `unknown`. Readiness states are `not_ready`, `ready`, `blocked`, `waived`, and `unknown`.

Unknown, stale, expired, contradictory, cyclic, mismatched, or digest-drifted evidence fails closed. A waiver is only accepted when its authority, scope, reason, timestamps, source reference, and source digest are valid. The resolver validates waivers but never creates them.

The record preserves source references and digests, evaluator identity, high-watermark, expiry, conflicts, warnings, failure reason, ledger event reference, and projection digest. Readiness is evidence for later consumers; it is not Dispatch authorization, Engineering completion, merge authority, or institutional acceptance.

## CLI

The bounded CLI supports only resolving from existing PTM ledger evidence, reading an immutable resolution, and validating a record:

```text
PYTHONPATH=src python -m estate.cli.main ptm-readiness resolve ...
PYTHONPATH=src python -m estate.cli.main ptm-readiness read --resolution-id res_...
PYTHONPATH=src python -m estate.cli.main ptm-readiness validate --record runtime/ptm/readiness/res_....json
```

There is no always-ready option and no CLI operation that manually grants readiness.

## Boundary

This package establishes PTM authority only. Grace commission gating, Dispatch revalidation, provider selection, Engineering completion, and live Qwen validation belong to the separately authorized integration work package.
