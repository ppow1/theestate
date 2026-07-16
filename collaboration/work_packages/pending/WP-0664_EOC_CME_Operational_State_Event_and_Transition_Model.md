# WP-0664 — EOC/CME Operational State, Event, and Transition Model

Status: Pending  
Priority: High  
Owner: Chief Architect  
Execution lane: Codex  
Change class: Architecture and planning only  
Campaign: EOC-CME-ARCH-01  
Depends on: WP-0663

## Objective

Define the canonical operational state model, institutional event taxonomy, campaign lifecycle, and legal transition system required for continuous momentum without creating a second scheduler or granting new authority.

## Required Inputs

- accepted EOC/CME architectural charter;
- all WP-0663 deliverables;
- PTM contracts and manifests;
- Grace operations runtime state;
- validation reconciliation and operational-readiness closure contracts;
- worker availability and staffing evidence;
- current notification and blocker records.

## Required Work

### Operational state catalog

Define canonical states for:

- initiatives;
- campaigns;
- work packages;
- dependencies;
- readiness gates;
- staffing demand;
- workers and capacity;
- dispatch;
- validation;
- integration;
- operational readiness;
- blockers;
- escalations;
- notifications;
- services and operational health.

For every state define authoritative evidence, owner, entry conditions, exit conditions, legal next states, terminality, retryability, and stale-state reconciliation.

### Event taxonomy

Define normalized event classes including:

- task completed;
- dependency cleared or regressed;
- worker available or unavailable;
- staffing supplied or denied;
- dispatch accepted, started, failed, or completed;
- validation requested, failed, passed, blocked, or missing recipe;
- blocker created, reclassified, acknowledged, resolved, or escalated;
- service degraded or recovered;
- campaign stalled or completed;
- Steward present or unavailable;
- protected approval granted or denied.

Every event must include identity, source, occurred time, observed time, evidence link, authority context, idempotency key, and reconciliation status.

### Transition model

Define transitions across:

Idea -> Discovery -> Planning -> Approval -> Campaign Activation -> Staffing -> Execution -> Validation -> Integration -> Operational Readiness -> Final Acceptance -> Archive.

For each transition specify:

- required evidence;
- responsible office;
- authority source;
- readiness gates;
- allowed operational action;
- prohibited inference;
- rollback or recovery path;
- notification requirement;
- terminal or reevaluation outcome.

### Reconciliation

Define how event-driven reevaluation is supplemented by bounded periodic reconciliation without creating a competing scheduler.

## Deliverables

Create:

1. `docs/architecture/eoc_cme_operational_state_catalog.md`
2. `docs/architecture/eoc_cme_institutional_event_taxonomy.md`
3. `docs/architecture/eoc_cme_campaign_lifecycle_and_transition_specification.md`
4. `docs/architecture/eoc_cme_state_reconciliation_model.md`
5. `collaboration/work_packages/completions/WP-0664_completion_receipt.md`

## Non-Goals

- no runtime implementation;
- no queue creation;
- no event bus creation;
- no automatic approvals;
- no replacement of PTM state;
- no invented readiness.

## Validation

- every state maps to current or explicitly proposed evidence;
- every transition names an office and authority source;
- every event has idempotency and evidence requirements;
- no transition bypasses protected approval;
- no duplicate campaign state machine is introduced where PTM already owns state;
- ambiguous or unsupported transitions fail closed.

## Acceptance Criteria

The resulting model must allow a fresh implementation team to determine exactly what changed, what state is current, which transitions are legal, and why a transition may or may not proceed.

## Delivery

Open a pull request for Chief Architect review. Do not merge. Do not implement runtime behavior.