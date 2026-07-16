# WP-0665 — EOC/CME Authority, Office Interaction, and Interface Contracts

Status: Pending  
Priority: High  
Owner: Chief Architect  
Execution lane: Codex  
Change class: Architecture and planning only  
Campaign: EOC-CME-ARCH-01  
Depends on: WP-0663, WP-0664

## Objective

Define the constitutional authority matrix and the stable interaction contracts by which the Estate Operations Center and Continuous Momentum Engine observe, recommend, and invoke existing Estate offices without creating new authority, duplicate routing, or parallel execution mechanisms.

## Required Inputs

- `docs/architecture/estate_operations_center_continuous_momentum_engine_architectural_charter.md`
- all WP-0663 and WP-0664 deliverables;
- personnel and mailbox registries;
- Grace operations runtime and command surfaces;
- Helen staffing and workforce capability records;
- Alfred routing and repository-backed communication contracts;
- PTM campaign, readiness, dependency, and scheduling contracts;
- dispatch, validation, operational readiness, and Steward command surfaces.

## Required Work

### 1. Authority matrix

Create a complete matrix covering at minimum:

- observation;
- recommendation;
- scheduling request;
- staffing request;
- routing request;
- dispatch request;
- pause, resume, hold, and retry;
- validation request;
- blocker acknowledgment and classification;
- escalation;
- architectural approval;
- budget and privacy decisions;
- final campaign acceptance;
- archival.

For each action identify:

- requesting actor;
- deciding authority;
- executing mechanism;
- required evidence;
- delegated-policy basis;
- protected approval boundary;
- notification recipient;
- prohibited substitutions.

### 2. Grace operational interface

Specify stable observation, evaluation, and control interfaces for Grace, including:

```text
status
readiness
blockers
critical-path
staffing-demand
operational-health
evaluate
reevaluate
explain-recommendation
rebuild-momentum
resume
pause
hold
retry
request-staffing
request-validation
escalate
acknowledge-blocker
```

Every operation must define request schema, response schema, evidence references, authority checks, idempotency, failure modes, audit trail, and canonical mechanism invoked.

Grace must not directly edit PTM authority state, assign engineering architecture, grant acceptance, or create a private queue.

### 3. Helen staffing interface

Define the staffing-demand contract from Grace/CME to Helen and the staffing-supply response from Helen.

The contract must distinguish:

- requested capability;
- required office or role;
- minimum qualification;
- capacity and timing need;
- duration or bounded assignment;
- replacement urgency;
- conflicts and unavailable capacity;
- supplied worker or explicit shortage;
- evidence and expiration.

Helen supplies staffing truth; she does not choose initiative priority or technical design.

### 4. Alfred routing interface

Define how EOC/CME requests cross-office routing through Alfred using existing repository-backed messages and mailbox discovery. Specify:

- destination resolution;
- message type and priority;
- acknowledgment requirements;
- routing evidence;
- stale or unresolved routing handling;
- escalation when a destination cannot be resolved;
- prohibition on bypassing canonical communication mechanisms.

### 5. Chief Architect and Steward interfaces

Define the protected interfaces for:

- architecture-change requests;
- campaign replan requests;
- strategic priority conflicts;
- constitutional or privacy decisions;
- budget decisions;
- final acceptance packages.

The CME may package evidence and recommend; it may not approve.

### 6. Existing-mechanism invocation map

Create an explicit reuse map identifying, for every proposed operation, the current Estate service, registry, ledger, command, queue, or office surface that must be invoked. Any missing seam must be labeled as a proposed adapter, not silently implemented as a replacement system.

## Deliverables

Create:

1. `docs/architecture/eoc_cme_authority_matrix.md`
2. `docs/architecture/eoc_cme_office_interaction_model.md`
3. `docs/architecture/eoc_cme_grace_operational_interface.md`
4. `docs/architecture/eoc_cme_helen_staffing_interface.md`
5. `docs/architecture/eoc_cme_alfred_routing_interface.md`
6. `docs/architecture/eoc_cme_protected_authority_interfaces.md`
7. `docs/architecture/eoc_cme_existing_mechanism_reuse_map.md`
8. `collaboration/work_packages/completions/WP-0665_completion_receipt.md`

## Non-Goals

- no runtime implementation;
- no new office creation;
- no direct worker assignment by CME;
- no replacement of Alfred routing;
- no replacement of Helen staffing;
- no transfer of engineering authority to Grace;
- no automatic Steward decisions.

## Validation

- every operation names a deciding authority and executing mechanism;
- every interface is fail-closed when authority or evidence is missing;
- no interface creates a second queue, scheduler, registry, message store, validator, or acceptance path;
- every cross-office action uses canonical routing;
- every protected decision remains explicitly protected;
- every proposed adapter has a bounded purpose and named underlying canonical mechanism.

## Acceptance Criteria

A fresh implementation team must be able to determine exactly who may request, decide, execute, observe, acknowledge, and escalate every EOC/CME action without inferring authority.

## Delivery

Open a pull request for Chief Architect review. Do not merge. Do not implement runtime behavior.