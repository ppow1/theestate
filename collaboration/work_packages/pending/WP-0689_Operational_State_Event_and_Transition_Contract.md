# WP-0689 — Operational State, Event, and Transition Contract

Status: Pending  
Priority: High  
Owner: Chief Architect  
Execution lane: Codex  
Primary campaign: CAMPAIGN-0681 — Estate Operationalization  
Depends on: WP-0688  
Gate: G1 — Canonical and authority freeze

## Objective

Define and implement the canonical operational state, event, and transition contract that allows existing Estate systems to describe operational truth consistently without creating a duplicate registry, queue, scheduler, or authority model.

This package must build on the canonical-reuse and authority map produced by WP-0688. It may extend existing state and event seams, but it may not invent an independent Operations Center source of truth.

## Required Inputs

- CAMPAIGN-0681 charter and manifest
- WP-0688 completion receipt and all required deliverables
- canonical campaign, work-package, PTM, Dispatch, resident, service-health, validation, readiness, evidence, mailbox, message, reflection, and continuity specifications
- CAMPAIGN-0670 and CAMPAIGN-0680 accepted artifacts where state or decision-support concepts overlap

## Required Work

### 1. Operational entity model

Define the minimum normalized operational representation for existing entities such as:

- campaigns;
- work packages;
- residents;
- services;
- offices;
- workers and providers;
- validation runs;
- evidence packages;
- staffing requests;
- messages and escalations;
- protected decisions.

The model must reference canonical IDs and paths rather than duplicating authoritative records.

### 2. Operational state vocabulary

Define bounded states sufficient to represent operational progress and health. At minimum distinguish:

- observed;
- pending;
- not ready;
- ready;
- eligible;
- coordinating;
- executing;
- waiting for evidence;
- waiting for authority;
- blocked;
- degraded;
- failed;
- paused;
- recovering;
- review required;
- complete;
- accepted;
- cancelled or superseded.

Do not collapse technical completion, validation, review, and acceptance into one state.

### 3. Event contract

Define normalized events that point back to canonical evidence. Each event must include at minimum:

- event ID;
- event type;
- source system and source record;
- subject type and canonical subject ID;
- observed time and effective time;
- prior state and proposed new state where applicable;
- actor or emitting mechanism;
- authority classification;
- evidence references;
- correlation and causation IDs;
- severity;
- idempotency key;
- schema version.

Events are observations or requests unless canonical authority says otherwise. Event emission alone must not grant permission or acceptance.

### 4. Transition rules

Define machine-checkable transition rules that:

- reject impossible or unauthorized state changes;
- require dependency, readiness, health, evidence, staffing, and authority prerequisites where applicable;
- preserve protected stop gates;
- distinguish recommendation from action;
- distinguish completion from acceptance;
- fail closed on stale, conflicting, or incomplete evidence;
- support deterministic replay and resume.

### 5. Storage and integration seam

Use the canonical seam identified by WP-0688. Define how normalized operational state is derived, cached, or projected without becoming a competing source of truth.

Any materialized view must be rebuildable from canonical records and events.

### 6. Schema and validation

Provide versioned schemas, validators, fixtures, and transition tests. Include valid and invalid examples, stale-event handling, duplicate-event handling, out-of-order events, protected transitions, and replay behavior.

## Required Deliverables

1. operational state schema and documentation in the nearest canonical architecture or schema location
2. operational event schema and documentation
3. transition rule specification and validator
4. projection or materialized-view contract, if required
5. fixtures and automated tests
6. compatibility notes for CAMPAIGN-0670, CAMPAIGN-0680, and WP-0678
7. `collaboration/work_packages/completions/WP-0689_completion_receipt.md`

## Explicit Non-Goals

Do not:

- implement Grace coordination behavior;
- implement the Continuous Momentum Engine;
- dispatch work;
- create a new authoritative registry or queue;
- grant authority through events;
- automatically merge, deploy, validate, accept, or close work;
- replace domain-specific canonical states;
- mark G1 passed.

## Required Validation

Prove that:

- normalized entities reference canonical identities;
- state projections are rebuildable and non-authoritative;
- invalid and unauthorized transitions fail closed;
- recommendation, action, completion, review, and acceptance remain distinct;
- duplicate, stale, and out-of-order events are handled deterministically;
- protected gates cannot be bypassed;
- no duplicate registry, queue, scheduler, or acceptance path was created;
- automated tests pass.

## Acceptance Criteria

WP-0689 is complete when later CAMPAIGN-0681 packages can consume one consistent, versioned operational state and event language while canonical domain systems and institutional authorities remain unchanged.

## Delivery

Do not execute until WP-0688 is complete and CAMPAIGN-0681 is formally launched through the accepted WP-0678 capability. Do not merge or accept.