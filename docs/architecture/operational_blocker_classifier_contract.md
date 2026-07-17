# Operational blocker and escalation classifier contract

## Boundary

`estate.core.operational_blocker_classifier` is a pure, read-only projection over canonical campaign, work-package, health, readiness, validation, evidence, staffing, provider, communication, execution, and authority facts. Classification is observation and recommendation only. It creates no blocker registry or escalation queue, writes no PTM/Dispatch/mailbox record, and never assigns, dispatches, approves, accepts, merges, deploys, closes, or waives a gate.

## Input and evidence contract

Each fact names a condition or explicit supported blocker class, state, explanation, and one or more canonical evidence references. The affected campaign or package is mandatory. Missing evidence adds an evidence/validation blocker. Missing or ambiguous authority adds the highest-priority unknown-authority blocker. Contradiction and staleness fail closed. Inputs are copied and never mutated.

Canonical producers remain authoritative: campaign manifests and receipts for topology/state; WP-0691 health projections for resident/service/provider facts; WP-0692 momentum projections for dependency/momentum facts; readiness and validation records for their gates; Helen for workforce workflow; Engineering and Dispatch for execution/provider recovery; repository messages and mailboxes for communication/acknowledgement; Chief Architect for architecture; and Steward for Steward-reserved decisions.

## Classification and routing

Rules are deterministic and independent of fact order. Safety priority is unknown authority, contradiction, Steward decision, stale evidence, acceptance, architecture, validation/evidence, health, provider, staffing, readiness, dependency, communication, recoverable failure, then transient failure. Every result contains the affected item, facts and references, primary/additional classes, severity, continuation result and basis, responsible lane, next action, escalation destination, acknowledgement requirement, reevaluation trigger, uncertainty reason, and explicit non-authority flags.

Grace may consume and coordinate the result, but the named destination retains authority. Helen, Alfred, Engineering, Chief Architect, and Steward keep their accepted lanes. Escalation and acknowledgement must use accepted mailbox/repository-message mechanisms rather than a new queue.

## Continuation, reevaluation, and declassification

The affected lane stops. An unaffected lane may continue only when the caller supplies both canonical parallel-dependency permission and a clear collision check; protected decisions stop progression despite those flags. A classification never becomes execution permission.

New current canonical evidence, a canonical acknowledgement, a recovered execution result, or the protected decision triggers reevaluation. `declassification_ready` only reports that reevaluation evidence is structurally ready: each replacement fact must be current/clear, referenced, and explicitly name evidence it clears. It neither declassifies automatically nor mutates authoritative state. The caller must rebuild the projection and use the relevant canonical authority/state transition.
