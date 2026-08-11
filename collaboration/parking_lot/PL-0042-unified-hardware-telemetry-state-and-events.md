# PL-0042 — Unified Hardware Telemetry State and Events

Status: Captured
Priority: High
Category: Operational Observability / Hardware Telemetry / Event Integration
Originator: Pat / Steward
Date Captured: 2026-08-10
Target Milestone: After current Stream Deck / GPU stabilization and P100 recovery work are complete

## Idea

Move GPU and future hardware-health observation away from being implicitly owned by the Office of the Steward refresh loop and toward one Estate-owned normalized hardware-state producer that runs independently of whether Office is open.

The goal is to avoid multiple consumers each collecting or interpreting hardware state differently. Office, Stream Deck, Grace, CME, and future alerting should consume the same normalized current state and the same health-transition semantics.

The preferred direction is:

```text
one hardware collector / normalization path
    -> one authoritative runtime state
    -> one transition/event path
    -> many consumers
         Office of the Steward
         Stream Deck
         Grace / residents
         CME
         attention / notification path
```

Collection once, normalization once, event generation once, presentation many times.

## Current Trigger

WP-0535 GPU observability demonstrated that live GPU detail in Office works well, but the current GPU refresh behavior is coupled to the Office/Operations Center being up. When Office is not running, the Estate does not continuously refresh the same GPU state.

That coupling is acceptable for the current bounded implementation but is not a good long-term ownership model for hardware health.

The recent Tesla P100 incident also demonstrated the operational value of durable state transitions:

- GPU2 was previously observed as `LOST / CUDA_UNAVAILABLE`.
- After a cold boot, the same P100 UUID recovered and was again visible through Windows, NVIDIA-SMI, and NVML.
- The Estate should eventually be able to treat `healthy -> lost` and `lost -> recovered` as first-class operational transitions rather than requiring the Steward to discover them by watching a dashboard.

## Intended Architecture Direction

When promoted, first inspect existing `compute_resources` collection, Operations Center refresh behavior, Stream Deck status publication, CME event ingestion, and the existing Estate attention-event path.

Prefer extending an existing Estate-owned periodic/runtime execution path rather than creating another watcher or daemon.

The normalized state should be independent of Office presentation lifecycle and should preserve at least:

- stable hardware identity;
- device presence/availability;
- health classification;
- diagnostic reason/error evidence;
- utilization;
- memory/VRAM usage where applicable;
- temperature and thermal state;
- power state where available;
- observed_at / freshness;
- last valid observation and current collection failure semantics.

GPU is the first concrete target. CPU, memory, and disk health may later reuse the same pattern only where that can be absorbed cleanly without turning this item into a broad hardware-monitoring rewrite.

## Event Semantics

Hardware telemetry should emit meaningful state-transition events into the existing Estate/CME event path rather than generating repetitive events every polling interval.

Candidate transitions include:

- `gpu.lost`
- `gpu.recovered`
- `gpu.health.degraded`
- `gpu.temperature.warning`
- `gpu.temperature.critical`
- `gpu.telemetry.stale`

Exact event names and severity policy should follow existing Estate conventions discovered at promotion time.

A GPU that remains lost for ten refresh cycles should not create ten identical new events. Emit on meaningful transition and use existing reminder/escalation policy if one already exists.

The collector detects and reports state. CME decides what the state means operationally and whether it warrants escalation, attention, or notification.

## Consumer Responsibilities

### Office of the Steward

Detailed operational presentation and history. Office should consume current normalized hardware state; Office should not be required to run in order for that state to remain current.

### Stream Deck

Compact exception-aware status. Normal/healthy should remain quiet. Lost, degraded, thermal, stale, or unavailable states should visibly demand attention according to existing severity conventions.

### CME

Consume hardware-health transition events through the existing event mechanism. CME may correlate the event with active work, allocation, service health, or other operational context.

### Grace / Residents

Where authorized, residents should read normalized current hardware state rather than independently invoking hardware collectors and creating another interpretation layer.

### Attention / Notification

If CME or existing policy classifies the transition as requiring Steward attention, reuse the existing Estate attention-notification path rather than building GPU-specific notification machinery.

## Cohesion Rule

Do not allow Office, Stream Deck, CME, and residents to become separate hardware-monitoring implementations.

The architectural rule for this item is:

**collection once, normalization once, event generation once, presentation many times.**

## Promotion Condition

Promote this item when:

1. current WP-0535 Stream Deck/GPU repairs are stable and accepted;
2. the P100 recovery incident has enough evidence to characterize the current lost/recovered behavior;
3. the existing CME/event and attention paths can be identified clearly;
4. an existing Estate-owned runtime cadence can be shown to absorb hardware collection without creating another parallel watcher;
5. the Steward intentionally authorizes the integration.

## Explicit Non-Action

This item is parked.

Do not interrupt current Stream Deck stabilization or P100 recovery work to implement it.

Do not create a new hardware department, event bus, scheduler, daemon, registry, or telemetry database solely for this item.

Do not broaden immediately into full CPU/memory/disk monitoring. GPU is the proving case; expand only where existing subsystems can absorb the responsibility cleanly.

Do not move hardware-health policy into presentation code.

## Related Evidence

- WP-0535 GPU Operational Telemetry / Office / Stream Deck work.
- GPU2 Tesla P100 `LOST / CUDA_UNAVAILABLE` observation and subsequent cold-boot recovery.
- Existing `compute_resources` GPU collection path.
- Existing Office quiet/live refresh behavior.
- Existing CME event-driven processing and Estate attention-notification direction.
- PL-0033 Stream Deck Operational Details View.
