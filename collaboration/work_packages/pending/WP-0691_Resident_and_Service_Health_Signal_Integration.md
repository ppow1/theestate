# WP-0691 — Resident and Service Health Signal Integration

Status: Pending  
Priority: High  
Owner: Chief Architect  
Execution lane: Codex  
Primary campaign: CAMPAIGN-0681 — Estate Operationalization  
Depends on: WP-0688, WP-0689  
Integration gate: G2 — Observation Truth

## Objective

Integrate existing resident and service health evidence into the CAMPAIGN-0681 operational state model so campaign readiness, degraded-service truth, blocker classification, escalation, and bounded next-action selection can rely on canonical health signals without creating a second health system.

WP-0691 is an integration package. It shall discover, normalize, and expose authoritative health evidence through the operational-state contract established by WP-0689. It shall not replace the Estate service health registry, resident lifecycle system, worker heartbeat mechanisms, service status board, operational readiness mechanisms, validation system, or office authority model.

## Constitutional Precedence

Accepted Estate governance, campaign, work-package, resident, service, readiness, validation, evidence, communication, mailbox, PTM, Dispatch, acceptance, and office-authority artifacts remain authoritative.

If this package conflicts with an accepted canonical artifact, the accepted canonical artifact prevails.

A moved, renamed, or partially indexed path is not permission to invent a replacement. Codex must discover the canonical successor through repository evidence and record that discovery in the completion receipt.

## Required Inputs and Canonical Seams

Before implementation, discover and read the canonical successors of at least:

- CAMPAIGN-0681, its execution manifest, and its launch handoff;
- WP-0688 and WP-0689 deliverables and completion evidence;
- WP-0678 and its protected acceptance record;
- the accepted service health registry and its completion evidence;
- the accepted service status board and its completion evidence;
- resident lifecycle and resident interaction state;
- worker runtime heartbeat and operations runtime evidence;
- operational readiness, validation, failure, retry, and recovery evidence;
- current Steward command-center or dashboard health surfaces;
- canonical repository-message and mailbox mechanisms;
- canonical office and protected-authority definitions.

Expected existing implementation seams include, where still canonical:

- `src/estate/core/service_health_registry.py`;
- `src/estate/core/service_status_board.py`;
- `src/estate/core/resident_lifecycle.py`;
- `src/estate/core/resident_interaction.py`;
- `src/estate/core/worker_runtime_heartbeat.py`;
- `src/estate/core/operations_runtime.py`;
- `src/estate/core/work_package_validation.py`;
- `src/estate/core/steward_command_center.py`.

These paths are discovery hints, not permission to duplicate or bypass a canonical successor.

## Scope

Implement or extend canonical seams needed to provide:

1. discovery of current resident-health and service-health evidence;
2. normalization of heterogeneous health evidence into the WP-0689 operational-state contract;
3. explicit source provenance and evidence references for every normalized signal;
4. freshness, observation time, and expiry or staleness handling;
5. differentiation among healthy, degraded, unavailable, failed, unknown, stale, and contradictory conditions;
6. separation of resident health, service health, worker/runtime health, provider/environment health, and validation health;
7. deterministic aggregation rules that do not conceal degraded or conflicting evidence;
8. dependency-aware health impact suitable for WP-0692 campaign observation;
9. blocker-ready health facts suitable for WP-0693 classification;
10. concise human-readable explanations suitable for Grace, Engineering, the Chief Architect, and the Steward;
11. machine-readable output suitable for later CAMPAIGN-0681 packages;
12. tests covering normal, degraded, missing, stale, contradictory, partial, failed, and recovered health conditions.

## Required Normalized Health Contract

The normalized health representation shall include at least:

- subject type and stable subject identifier;
- health domain;
- normalized state;
- severity;
- observed timestamp;
- source timestamp, when available;
- freshness or staleness result;
- canonical evidence references;
- dependency or campaign impact, when determinable;
- explanation;
- uncertainty or contradiction warnings;
- responsible operational or authority lane;
- reevaluation trigger;
- whether the signal permits observation only, blocks progression, or requires protected review.

The implementation must preserve the difference between an observed condition and an authorized action.

## Evidence Precedence and Reconciliation

The implementation shall define and test deterministic evidence precedence.

At minimum:

1. explicit current failure, shutdown, refusal, pause, or unavailability evidence outranks optimistic inferred health;
2. accepted canonical registries and schema-valid receipts outrank dashboards, summaries, or transient UI state;
3. repository-backed authoritative evidence outranks unverified runtime claims when the two cannot be reconciled;
4. current direct observations may supplement repository evidence but may not silently overwrite durable authoritative state;
5. stale evidence shall not be reported as current health;
6. contradictory evidence shall produce an explicit contradictory or indeterminate result;
7. missing evidence shall produce unknown or indeterminate health, not assumed health;
8. recovery shall require evidence that the failed or degraded condition has actually cleared;
9. a healthy aggregate shall not conceal a critical degraded dependency.

Every derived state must identify the evidence and rule that produced it.

## Resident Health Requirements

Resident-health integration shall:

- use canonical resident lifecycle and interaction evidence;
- distinguish resident availability, readiness, degraded capability, paused state, failed state, and unknown state;
- avoid treating conversational responsiveness alone as operational readiness;
- avoid treating a resident profile or configuration file as proof that the resident is currently healthy;
- preserve resident identity and office boundaries;
- expose health facts without granting staffing, dispatch, acceptance, architectural, or protected authority;
- permit Grace to receive operational coordination information without inheriting another office's authority.

## Service and Runtime Health Requirements

Service-health integration shall:

- reuse the canonical service health registry and status-board models;
- account for service dependencies where canonical dependency evidence exists;
- distinguish process existence from functional readiness;
- distinguish Estate-owned process state from unrelated external or automatically restarted processes;
- preserve explicit service identity and instance ownership;
- include worker heartbeat and operations-runtime evidence where relevant;
- expose provider or environment degradation without creating a new provider registry;
- avoid mutating service state merely because a normalized observation was calculated.

## Campaign Impact Rules

Health signals may affect campaign momentum only through explicit, deterministic rules.

The integration shall:

- identify the campaign or work package affected, when determinable;
- distinguish a local degradation from a campaign-wide blocker;
- avoid blocking unrelated collision-free work unless canonical dependency or safety rules require it;
- fail closed when a required dependency's health is unknown, stale, contradictory, or failed;
- preserve review and protected-decision boundaries;
- provide facts and recommended destinations without dispatching, accepting, merging, deploying, staffing, spending, or disclosing protected information.

## Required Outputs

Provide:

1. a reusable health-normalization implementation in the canonical repository seam;
2. a documented machine-readable health contract or documented reuse of an existing accepted contract;
3. deterministic reconciliation and precedence rules;
4. resident-health adapters using canonical resident evidence;
5. service/runtime-health adapters using canonical service and runtime evidence;
6. campaign-impact mapping suitable for WP-0692;
7. blocker-ready facts suitable for WP-0693;
8. human-readable health explanations;
9. automated tests and fixtures;
10. a conflict/reuse report listing every canonical system extended and every duplicate system deliberately avoided;
11. a completion receipt with changed paths, validation commands, outputs, limitations, and unresolved blockers;
12. G2 observation-truth evidence contribution.

## Owned Paths and Change Boundaries

Codex may modify existing canonical implementation, schema, documentation, test, fixture, and completion-receipt paths required to satisfy this package.

Codex shall not create a new persistent health database, registry, queue, scheduler, office, mailbox system, dashboard authority, or campaign-state store unless an already accepted architectural artifact explicitly requires it.

Any new module must be a bounded adapter or normalization component inside the existing canonical architecture and must be justified in the conflict/reuse report.

## Non-Goals and Protected Surfaces

WP-0691 shall not:

- create a second resident-health or service-health registry;
- replace resident lifecycle, service health registry, service status board, worker heartbeat, operations runtime, readiness, validation, PTM, Dispatch, mailbox, or acceptance systems;
- dispatch, assign, start, pause, resume, retry, merge, deploy, accept, close, cancel, or supersede work;
- infer health from file existence alone;
- infer service readiness from process existence alone;
- infer resident readiness from conversational availability alone;
- infer authority from technical capability;
- convert Grace, Alfred, or any resident into execution or protected authority;
- conceal stale, missing, partial, or contradictory evidence;
- mutate canonical campaign or work-package state merely because health was observed;
- implement the Continuous Momentum Engine decision loop assigned to WP-0700.

## Acceptance Criteria

WP-0691 is complete only when:

1. existing canonical resident and service health evidence is consumed without creating a duplicate health system;
2. normalized output is deterministic for unchanged evidence;
3. every normalized signal includes source provenance and freshness treatment;
4. missing evidence results in unknown or indeterminate health;
5. stale evidence is explicitly identified and cannot be silently treated as current;
6. contradictory evidence produces an explicit fail-closed result;
7. resident, service, runtime, provider/environment, and validation health remain distinguishable;
8. critical dependency degradation cannot be hidden by a healthy aggregate;
9. campaign and package impact is explained without becoming dispatch or execution authority;
10. outputs are consumable by WP-0692 and WP-0693;
11. recovery is shown only after authoritative evidence clears the degraded or failed condition;
12. tests prove that observation performs no unauthorized state mutation;
13. a conflict/reuse report and independently readable completion receipt exist;
14. all required validation commands pass before the bounded WP-0691 commit.

Completion requires Chief Architect review. It does not itself authorize protected actions, acceptance, merge, deployment, closure, staffing, budget use, or disclosure.

## Exact Validation Commands

Codex must create or update the targeted test file below and run these commands from the repository root before recording the WP-0691 bounded commit:

```powershell
python -m pytest -q tests/test_campaign_0681_health_signal_integration.py
python -m compileall -q src/estate/core
python -m pytest -q tests/test_steward_command_center.py
git diff --check
```

If a command cannot run because a required interpreter, dependency, fixture, or canonical successor is unavailable, Codex must stop WP-0691, record the exact blocker, and must not substitute an unapproved validation command.

The completion receipt must record:

- each exact command;
- exit code;
- concise output summary;
- changed paths;
- canonical seams reused;
- conflicts or contradictions found;
- limitations;
- unresolved blockers;
- commit SHA.

## Completion Evidence

Create independently readable completion evidence under the canonical completion-receipt path used by the Estate.

The receipt shall clearly state that WP-0691 provides normalized health observation and campaign-impact facts only. It shall not claim dispatch authority, execution authority, engineering acceptance, architectural acceptance, Steward acceptance, merge, deployment, or campaign closure.