# WP-0663 — EOC/CME Architectural Investigation and Current-State Reuse Map

Status: Pending  
Priority: High  
Owner: Chief Architect  
Execution lane: Codex  
Change class: Architecture and planning only  
Campaign: EOC-CME-ARCH-01  

## Objective

Perform a repository-grounded architectural investigation for the accepted Estate Operations Center (EOC) and Continuous Momentum Engine (CME) initiative, identify every existing Estate mechanism that must be reused, and produce the controlling current-state architecture and reuse map for the remaining campaign packages.

The accepted authority basis is:

`docs/architecture/estate_operations_center_continuous_momentum_engine_architectural_charter.md`

## Required Inputs

Read completely before changing files:

- `AI_HINTS.md`
- `AI_COMMUNICATION_HINTS.md`
- `docs/architecture/estate_operations_center_continuous_momentum_engine_architectural_charter.md`
- `docs/architecture/estate_ptm_specification_acceptance.md`
- `docs/architecture/estate_project_task_management_governance_acceptance.md`
- `docs/operations/Operational_Readiness_Closure_Controller_v1.md`
- `src/estate/core/grace_operations_runtime.py`
- `src/estate/core/office_command_surface.py`
- `src/estate/core/operations_runtime.py`
- `src/estate/core/operations_runtime_service.py`
- `src/estate/core/operational_readiness_closure.py`
- current staffing, routing, dispatch, validation, notification, registry, queue, ledger, and campaign contracts discovered in the repository.

## Scope

### 1. Current-state inventory

Identify and document the canonical existing components for:

- PTM campaign, task, dependency, readiness, scheduling, and utilization state;
- Grace operational coordination and command surfaces;
- Helen staffing, personnel, worker capability, availability, replacement, and capacity state;
- Alfred routing and repository-backed communication;
- provider dispatch and execution evidence;
- validation, reconciliation, verdict, and operational-readiness closure;
- notifications, acknowledgements, escalation, and Steward-facing status;
- canonical registries, queues, ledgers, event records, and runtime-state roots.

For every component record:

- authoritative path;
- owner;
- input contract;
- output contract;
- mutable state location;
- invocation surface;
- current limitations;
- relationship to EOC/CME.

### 2. Reuse map

Create a mandatory reuse matrix classifying each required EOC/CME capability as:

- reuse unchanged;
- reuse through adapter;
- extend existing contract;
- missing capability requiring a new bounded component;
- prohibited duplicate.

Every proposed new component must include evidence that no canonical existing component can absorb the responsibility.

### 3. Architectural gap analysis

Identify:

- missing observation seams;
- missing state joins;
- missing authority evidence;
- missing transition explanations;
- missing operational recovery controls;
- conflicting ownership;
- duplicate or overlapping systems;
- stale assumptions in the accepted charter.

Do not resolve gaps by inventing a second scheduler, queue, registry, event bus, validator, dispatcher, or acceptance path.

## Required Deliverables

Create:

1. `docs/architecture/eoc_cme_current_state_architecture.md`
2. `docs/architecture/eoc_cme_existing_mechanism_reuse_map.md`
3. `docs/architecture/eoc_cme_gap_and_overlap_analysis.md`
4. `collaboration/work_packages/completions/WP-0663_completion_receipt.md`

The current-state architecture must include a repository-path-level system map and a clear distinction between governance, operational coordination, policy evaluation, scheduling, dispatch, validation, and acceptance.

## Non-Goals

- no production implementation;
- no new runtime loop;
- no new scheduler or dispatch queue;
- no change to constitutional office authority;
- no automatic campaign transition;
- no speculative APIs before current-state seams are verified.

## Validation

Verify programmatically or by explicit repository inspection that:

- every cited path exists;
- every claimed canonical mechanism has supporting code or documentation;
- no proposed reuse target is merely inferred from a filename;
- missing and ambiguous evidence are explicitly marked;
- the reuse map covers every capability named in the accepted charter;
- the worktree is clean except for intended files.

## Acceptance Criteria

- A fresh architect can understand the present operational architecture without rediscovering it from conversation history.
- Every downstream EOC/CME package has a reliable reuse baseline.
- The analysis explicitly prevents parallel schedulers, queues, registries, dispatchers, validators, and governance authorities.
- All claims are tied to current repository evidence.

## Delivery

Open a pull request for Chief Architect review. Do not merge it. Do not begin EOC/CME implementation.