# Estate Bounded Consultation Closure and Steward Escalation

## Decision

When the fixed autonomous evidence budget is exhausted, the consultation
does not become resolved. The Estate records `STEWARD_DECISION_REQUIRED`
and stores a bounded escalation package in authoritative SQLite memory.

For live root `5.00`, the three read-only acquisitions remain durable and
no fourth provider request exists. Turn `5.08` records the unresolved
post-budget reasoning result. Root `5.00` is not closed or resolved.

## Escalation package

The package contains the root/current turn, objective, bounded compact
understanding, recommendations, execution and acquisition summaries,
remaining unknowns, why no defensible conclusion was reached, the exact
decision/evidence needed from the Steward, PTM references, and durable
references. Full logs and secrets are excluded.

Grace-facing wording is equivalent to:

> ChatGPT has exhausted the permitted autonomous evidence budget and still
> cannot reach a defensible conclusion. Here is what we know, what remains
> unknown, and the decision/evidence I need from you.

## Reframe and resume

`REFRAME_AS_NEW_CONSULTATION` is a proposal only. It retains predecessor
lineage and a handoff summary but allocates no new root. Explicit Steward
input may resume the same root with its next ordered continuation. Neither
operation creates provider work during escalation itself.

## Projection and activation

The existing consultation projection is updated idempotently and remains
non-blocking. GitHub cannot overwrite SQL truth.

- **REQUIRED:** canonical mailbox-worker relaunch after deployment. Verify
  its state file reports `STEWARD_DECISION_REQUIRED` for the turn.
- **REQUIRED when long-lived:** Grace Gateway restart/relaunch if its owner
  loads the changed escalation integration; verify it can read the package.
- **CONDITIONAL:** consultation-worker relaunch if separately supervised;
  execution router/provider relaunch only after later authorized work.
- **NOT REQUIRED:** Codex provider, Open WebUI, Comms8, MCP adapter, Runtime
  Host, ChatGPT reconnect, dedicated browser, or workstation restart.

Smallest order: deploy, relaunch the canonical mailbox worker, then
relaunch Grace only if its long-lived owner needs the new module.

## Instrumentation continuation

The escalation is now also a first-class `escalation_id` record with an
immutable decision-time knowledge snapshot. It itemizes evidence-backed
fact, conclusion, and action confidence, explicit unknowns, real options,
and the system recommendation only when supportable. Separate durable
records capture Steward decisions, `STEWARD_SUPPLIED_EVIDENCE`, and later
validated outcomes. This instrumentation does not change the root’s
unresolved status or autonomously expand authority.
