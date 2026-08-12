# PL-0049 — Estate Operations CPU Telemetry Correction

Status: Captured
Priority: Normal
Category: Estate Operations / Telemetry / UI
Originator: Pat / Steward
Date Captured: 2026-08-12
Target Milestone: After current Grace/Open WebUI acceptance work

## Idea

Investigate and correct the Estate Operations CPU gauge, which is materially disagreeing with Windows host-wide CPU utilization.

Operator screenshots captured during current Grace/Open WebUI work show the Estate Operations CPU tile reporting values including 100% and approximately 49% while Windows Task Manager, observed at essentially the same time, reports low single-digit aggregate CPU utilization. The discrepancy is large enough that the Estate gauge should not currently be treated as trustworthy host CPU telemetry.

The desired result is a CPU metric whose meaning is explicit and whose displayed utilization reasonably tracks Windows host-wide CPU utilization over a documented sampling interval.

## Why It Is Parked

The defect is real but is not part of the current Grace/Open WebUI acceptance objective. Investigating it now would interrupt active acceptance work and expand scope unnecessarily.

It should be handled later as a focused telemetry investigation rather than folded into the current Grace/Open WebUI campaign.

## Promotion Condition

Promote when the current Grace/Open WebUI acceptance work is complete or when incorrect CPU telemetry materially interferes with an active Estate operational decision.

When promoted:

1. Identify the exact CPU metric/provider used by Estate Operations.
2. Trace the value from backend measurement through API/telemetry payload and frontend normalization to the displayed gauge.
3. Determine whether the current value is one logical processor, one process, instantaneous scheduler load, cumulative CPU time, a stale/cached sample, an incorrectly normalized multicore counter, or another metric.
4. Capture Estate and Windows CPU samples concurrently over controlled idle, moderate-load, and high-load intervals.
5. Correct the metric or normalization at its actual source.
6. Add deterministic tests for low, moderate, and high aggregate CPU utilization and ensure the intended gauge range remains 0–100%.
7. Verify behavior against an independent Windows host-wide CPU counter and document the expected sampling tolerance.
8. Do not modify GPU or RAM telemetry unless evidence demonstrates a shared defect.

## Explicit Non-Action

Do not investigate or fix this as part of the current Grace/Open WebUI acceptance work.

Do not assume the defect is frontend-only, backend-only, or a normalization error until the full measurement path is traced.

Do not change GPU or RAM telemetry merely because CPU telemetry is incorrect.

## Related Evidence

- Steward screenshots captured 2026-08-12 showing Estate Operations CPU values materially above simultaneous Windows Task Manager aggregate CPU values.
- Estate Operations v0.3 plugin CPU gauge.
- Windows Task Manager host CPU display used as the operator-visible comparison reference.
- Canonical Parking Lot process: `AI_COMMUNICATION_HINTS.md`.
