# PL-0043 — Codex Model Escalation and Throughput Policy

Status: Captured
Priority: High
Category: Codex Capacity / Execution Economics / Model Routing
Originator: Pat / Steward
Date Captured: 2026-08-10
Target Milestone: After current multi-seat Codex workspace and Grace execution routing are stable

## Idea

Define a deliberate Codex model-escalation curve so the Estate does not spend high-cost model capacity on routine work by default.

Use the least expensive model tier that is competent for the task, and escalate only when evidence shows the current tier is insufficient.

The initial conceptual curve is:

```text
GPT-5.4 economy / throttle tier
        ->
Luna default working tier
        ->
Terra deliberate escalation
        ->
Sol highest-cost / hardest-problem escalation
```

The exact model identifiers and availability should be resolved from current approved Codex configuration when this item is promoted. Do not hardcode assumptions from this parking-lot note into runtime behavior.

## Motivation

Pat previously used a manual throttling script that dropped cloud work to GPT-5.4 when appropriate. In that prior operating experience, cheaper iterations materially increased weekly throughput — more than doubling practical throughput in some periods because each iteration consumed less capacity.

With C1/C2/C3 now becoming independently observable Codex seats, the same principle may have significantly greater leverage:

- reserve expensive models for work that benefits from them;
- keep routine execution on cheaper tiers;
- reduce seat-fuel burn per iteration;
- extend weekly usable throughput across all seats;
- allow Grace or future routing policy to escalate based on task evidence rather than defaulting upward.

This is an economics/capacity policy, not merely a model preference.

## Intended Policy Direction

When promoted, first inspect existing Codex model selection, per-seat telemetry, execution-provider routing, Grace planning logic, and any older throttling scripts or configuration that already encode part of this behavior.

Prefer extending existing routing/capacity policy rather than creating a new model-selection subsystem.

Candidate operating behavior:

1. Start routine Codex work on the configured low-cost/default tier.
2. Observe whether the task is progressing successfully.
3. Escalate only when there is evidence of insufficient capability, repeated failure, unacceptable uncertainty, or task-critical complexity.
4. Prefer the smallest escalation necessary.
5. Record why escalation occurred so future routing can learn from actual task classes.
6. Do not automatically de-escalate in the middle of fragile work without a safe boundary.

## Candidate Escalation Curve

Conceptually:

- **GPT-5.4** — economy / throttle tier for bounded, repetitive, low-risk, well-specified work where it remains competent.
- **Luna** — normal default Codex worker for general Estate engineering work.
- **Terra** — deliberate escalation for harder debugging, architecture, ambiguity, or tasks where Luna is not converging.
- **Sol** — highest-cost escalation for the hardest reasoning, recovery, or high-value work where lower tiers are demonstrably insufficient.

This hierarchy is a starting hypothesis, not a permanent doctrine. Promotion should validate real cost, quality, latency, and completion behavior under current Codex product rules.

## Throughput Objective

The purpose is to maximize useful completed work per weekly seat-capacity budget, not simply minimize token cost.

When promoted, measure at least:

- task completion rate;
- rework rate;
- average iterations to completion;
- token/credit/fuel consumption;
- wall-clock latency;
- escalation frequency;
- failures requiring human intervention;
- effective completed-work throughput per seat per week.

A cheaper model that requires substantially more retries may not be cheaper in practice. Conversely, Pat's prior manual experience suggests GPT-5.4 throttling can materially extend weekly throughput on suitable work.

## Grace / Routing Opportunity

Once Grace is allocating work across C1/C2/C3, she may eventually use both:

- **seat fuel availability**, and
- **model tier economics/capability**

when recommending or dispatching work.

Conceptually:

```text
task characteristics
+ seat capacity
+ recent model performance evidence
+ urgency / risk
        ->
choose seat
+ choose starting model tier
+ escalate only if justified
```

Do not grant Grace broader execution authority merely because this policy exists. Existing dispatch/authorization boundaries still apply.

## Guardrails

Do not implement naive automatic escalation based solely on one failed command.

Do not silently promote every task to Sol when uncertainty appears.

Do not optimize only for cheapest tokens at the expense of repeated failure or corrupted work.

Do not assume model names, pricing, quotas, or availability are permanent; those must be read from current approved configuration/product evidence when implemented.

Do not rewrite active work history when switching models. Escalation should occur at explicit, recoverable task boundaries.

## Promotion Condition

Promote when:

1. C1/C2/C3 seat isolation and fuel telemetry are stable;
2. the Codex Desk / multi-seat operating surface is working;
3. Grace or another Estate routing layer can inspect seat capacity reliably;
4. current approved model IDs/cost relationships can be verified;
5. representative Estate task classes can be benchmarked across at least two tiers;
6. the Steward intentionally authorizes automated or semi-automated model escalation.

## Explicit Non-Action

This item is parked.

Do not interrupt current Stream Deck, Office, GPU, or Codex workspace stabilization to implement it.

Do not create a new scheduler, registry, routing engine, or policy department solely for this idea.

Do not change current seat model defaults from this note alone.

When promoted, first look for the old manual throttling logic and determine whether an existing execution-routing subsystem can absorb the policy with small targeted changes.

## Related Evidence

- Existing C1/C2/C3 Codex seat isolation and weekly fuel telemetry.
- Grace read-only Codex seat fuel capability.
- Current plan to default interactive seat launches to Luna.
- Pat's prior manual GPT-5.4 throttling experience, which materially increased weekly usable throughput.
- Future Codex Desk / multi-seat workspace launcher.
