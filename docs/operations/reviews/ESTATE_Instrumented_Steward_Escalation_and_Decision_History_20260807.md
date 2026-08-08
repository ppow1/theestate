# Instrumented Steward Escalation and Decision History

## Scope and decision

Steward escalation is now a first-class durable record layered onto the
existing consultation escalation. It does not change consultation
numbering, evidence limits, Comms8, provider authority, or Grace’s
continuation rules. It records why autonomous reasoning stopped and what
happened after an explicit Steward decision.

The existing root `5.00` escalation is instrumented in place. Its stable
escalation identity, current turn, root, and bounded snapshot are stored in
SQLite. No new consultation, evidence acquisition, or provider request was
created.

## Immutable snapshot

The snapshot is created once per escalation/current turn and is never
regenerated when later decisions or outcomes arrive. It contains:

- known facts with operational confidence, confidence class, basis,
  evidence references, and observed/derived classification;
- working interpretations with conclusion confidence, supporting and
  conflicting evidence, and uncertainty basis;
- explicit unknowns with impact, prior attempts, unresolved confidence,
  and confidence-reducing evidence;
- real decision-boundary options, risks, reversibility, authority, and
  uncertainty;
- system recommendation and recommendation confidence when one exists;
- what would materially increase confidence;
- PTM and durable consultation references.

Confidence values are operational evidence-strength signals, not calibrated
probabilities. Bands are: high `0.80–1.00`, medium `0.60–0.79`, weak
`0.40–0.59`, and speculative below `0.40`. Every numeric score has a
bounded provenance basis. Fact, conclusion, and action confidence remain
separate. For 5.00, no engineering recommendation is forced because the
available evidence does not justify one.

## Decision and evidence records

`escalation_decisions` stores a separate Steward decision with stable
decision ID, selected option, exact decision text, optional supplied
rationale, actor, and timestamp. Rationale is absent when the Steward did
not supply one.

`escalation_steward_evidence` stores new Steward facts separately as
`STEWARD_SUPPLIED_EVIDENCE`, with provenance and impact. It never overwrites
the snapshot.

`escalation_outcomes` stores later execution/validation outcome separately,
correlated to the decision. Allowed classifications are `SUCCESS`,
`FAILED`, `PARTIAL`, `NEW_CONSTRAINT_DISCOVERED`, `ABANDONED`, and
`UNKNOWN`. Unvalidated work is not marked successful.

The existing resume path can continue the same consultation after Steward
input. A materially different objective may use the existing reframe
proposal; no new root is silently created.

## Queryability and projection

The store supports bounded escalation lookup by PTM project, tag, reason,
and operational confidence band, plus decision/outcome lookup by stable
correlation. The existing consultation projection renders a compact
escalation section idempotently. GitHub remains non-authoritative and
non-blocking.

The corpus may later identify recurring missing evidence, avoidable
escalations, calibration issues, and automation candidates. It must not
expand autonomous authority automatically; any policy or authority change
requires a separate governed decision.

## Activation

- **REQUIRED:** Grace Gateway restart/relaunch when its long-lived owner
  must load the instrumented escalation code. Verify it can read the
  escalation ID and Grace decision packet.
- **CONDITIONAL:** canonical mailbox-worker relaunch if deploying the
  worker integration; consultation-worker relaunch if separately
  supervised; execution router/provider relaunch only for later authorized
  work.
- **NOT REQUIRED:** Open WebUI, Comms8, MCP adapter, Runtime Host,
  ChatGPT reconnect, dedicated browser, or workstation restart.

Smallest activation is deployment plus the affected Grace owner; no
transport or browser restart is needed.
