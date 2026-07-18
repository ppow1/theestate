# CAMPAIGN-0681 bounded Continuous Momentum Engine

WP-0700 provides one deterministic cycle over canonical projections and existing
action adapters. The stages are observe, reconcile, classify, propose, authorize,
act, verify, and record. The engine is not an office, scheduler, dispatcher,
reviewer, validator, or acceptance authority.

Inputs are current health, campaign momentum, blockers, office coordination,
Engineering, readiness, and recovery/control projections. Each must explicitly
deny action authority and link canonical evidence. Missing, stale, contradictory,
or protected evidence holds or escalates the cycle.

Candidates are classified as recommendation, preauthorized, delegated, protected,
or prohibited. Priority is deterministic, followed by stable action identity.
Actionable candidates require source evidence, an idempotency key, canonical
mechanism, and—for preauthorized/delegated actions—explicit authority evidence.
Protected and prohibited actions never execute.

Simulation and dry-run modes never invoke an adapter. Live mode can invoke only a
caller-supplied existing canonical adapter, and the outcome must return a canonical
evidence reference. The engine itself writes no canonical state. Duplicate keys,
active cooldowns, missing adapters, and exhausted evidence result in safe idle.

Every cycle records normalized stage evidence, input and candidate digests,
selection, authorization problems, holds, warnings, cooldown, deduplication,
attempt and verification result, evidence references, and a final record digest.
The same inputs reproduce the same decision.
