# Engineering Provider Health Runtime

WP-0535 adds `estate.core.engineering_provider_health_runtime`, an advisory-only runtime that normalizes provider health evidence for `codex_cloud_web`, `codex_cli_openai`, `local_ollama_gpu`, and `local_gpu_runtime`.

## Schema

Each provider record includes schema/version identifiers, provider identity, observation times, last success/failure, availability, authentication, runtime, capability-registry and capacity states, latency, recent success/failure counters, failure rate, consecutive failures, queue depth, active jobs, provider version, discovery/capacity timestamps, staleness, normalized health state, reasons, warnings, evidence references, and dispatch recommendation eligibility.

## Evidence Sources

The runtime reads only local evidence: manual provider health records, provider capacity records, Codex capability/polling-policy artifacts when present, and non-billable executable visibility checks. It never submits prompts, starts jobs, or dispatches work.

## Evaluation Thresholds

Health states are `healthy`, `degraded`, `offline`, `maintenance`, and `unknown`. Offline/manual-disabled/authentication-invalid providers are not eligible. Degraded reasons include stale evidence, saturated/quota-limited capacity, elevated failure rate, three or more consecutive failures, high latency, and queue pressure.

## Freshness Rules

Records carry `stale_after_seconds`; missing or older capacity/capability evidence is stale. Stale evidence blocks healthy classification and dispatch eligibility.

## Routing Integration

Engineering provider routing loads `runtime/provider_health/current.json` through the runtime and combines health with base capability policy and Engineering Capacity evidence. Offline, maintenance, unauthenticated, stale, saturated, or explicitly disabled providers are excluded. Degraded providers are surfaced with explicit reasons and are advisory only.

## WP-0534 Polling Compliance

Remote Codex health does not perform automatic live polling unless polling policy evidence explicitly allows it. Unknown probe cost blocks live polling. Local checks are limited to read-only executable discovery or prompt-free command metadata.

## Failure and Recovery

Malformed or missing evidence yields `unknown` or `degraded` records with warnings instead of crashing collection. Recovery is evidence-driven: refresh capability discovery, record capacity snapshots, resolve authentication, or record successful operations.

## Extension Process

Add a provider id/type entry, implement a prompt-free evidence adapter, preserve evidence references, add tests for healthy/degraded/offline/stale/auth/failure/saturation behavior, and update Office/report documentation.
