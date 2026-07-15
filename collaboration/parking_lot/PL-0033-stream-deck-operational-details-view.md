# PL-0033 — Stream Deck Operational Details View

Status: Captured
Priority: Normal
Category: Stream Deck / Operational Observability
Originator: Pat / Steward
Date Captured: 2026-07-15
Target Milestone: Post operational-control stabilization

## Idea

Extend Estate Stream Deck service controls with a future details view that can display richer operational information for a selected service, such as PID, uptime, listening port, health state, current model, VRAM usage, queue depth, resident count, Git commit, latency, recent errors, and last restart time.

Candidate interaction options may include a future gesture, context action, dedicated details button, or another mechanism supported reliably by Stream Deck hardware and the plugin runtime.

## Why It Is Parked

The current Stream Deck work package is focused on reliable operational control semantics: single tap to start, double tap to start and open the UI, long press to stop, and accurate independent health indication. A richer details interface would expand scope into observability and presentation before the launcher and health model have fully stabilized.

## Promotion Condition

Promote this idea only after:

1. Core and optional service start/stop/restart behavior is stable and validated.
2. Service ownership and runtime-state semantics are authoritative.
3. The health/status API exposes enough structured data to support a details view without machine-wide process guessing.
4. A reliable Stream Deck interaction for opening details is intentionally selected.

## Explicit Non-Action

Do not implement a details panel, add new gestures, redesign the plugin, or expand service telemetry merely because this item has been captured. Promotion requires an explicit decision by the Steward and a governed work package.

## Related Evidence

- Current Estate Stream Deck interaction model:
  - Single tap: ensure service is running.
  - Double tap: ensure service is running and open its web interface.
  - Long press: stop the intended service.
  - Button state: display current operational health.
- Candidate details discussed during Estate Stream Deck operational workflow engineering included PID, uptime, ports, VRAM, queue depth, active models, resident count, Git commit, latency, memory/CPU utilization, recent errors, and last restart time.
- Canonical Parking Lot process: `AI_COMMUNICATION_HINTS.md`.
