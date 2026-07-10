# Institutional Operations Doctrine

Status: Proposed for Chief Architect / Steward review  
Owner: Chief Architect #5  
Coordinating Offices: Chief Architect #6 / Operations Architecture, Character Architecture, Steward  
Boundary Authority: Ingrid / Privacy and Boundary Office  
Classification: Estate Internal  
Created: 2026-07-10  
Source Work Package: WP-0502

## Purpose

This doctrine records the institutional operating principles that govern the Estate's operations, runtime, Traffic Controller, execution-provider, resident, validation, and Steward boundaries.

It exists so future work packages inherit the same boundary model instead of rediscovering it through conversation history or individual package reports.

## Canonical Operating Stack

```text
Runtime computes.
Operations conducts.
Traffic Controller constrains.
Execution Providers implement.
Steward governs.
```

Practical meaning:

- Runtime may compute state, run watches, evaluate dependencies, produce telemetry, and generate governed requests.
- Operations may conduct approved operational work and coordinate movement within delegated governance.
- Traffic Controller constrains movement and enforces authorization according to governance.
- Execution Providers implement assigned work through provider seams after governed handoff.
- Steward governs doctrine, exceptions, final authority, and institutional acceptance.

Allowed interpretation:

- A runtime cycle notices stale validation evidence and creates a governed request for review.
- Operations uses authorized procedures to move approved work forward.
- Traffic Controller blocks or permits movement based on governance constraints.
- Dispatch hands approved implementation work to an execution-provider adapter.
- Steward or delegated Chief Architect authority accepts institutional truth after reviewing evidence.

Prohibited interpretation:

- Runtime approves, dispatches, assigns, executes, or accepts work.
- Operations bypasses Traffic Controller or Dispatch because a runtime produced useful telemetry.
- Provider recommendations become automatic movement decisions.
- Validation output becomes institutional acceptance without Chief Architect / Steward review.

## Institutional Layer Model

The Estate separates institutional responsibility into layers:

1. **Governance and doctrine** define what is allowed, who may decide, and how exceptions are handled.
2. **Movement authorization** constrains whether work may advance.
3. **Operations** conducts authorized movement and coordinates approved operational work.
4. **Dispatch** holds governed implementation candidates and preserves the handoff path.
5. **Execution-provider infrastructure** translates governed records into provider-specific implementation handoffs.
6. **Runtime infrastructure** observes, computes, requests, reports, and produces evidence.
7. **Residents and character systems** operate within role boundaries and never become mechanical runtime infrastructure.

Violations of this layering are boundary findings, not local style preferences.

## Movement Authority Model

```text
Operations conducts movement.
Traffic Controller authorizes movement according to governance.
```

Practical meaning:

- Operations may execute approved operational procedures.
- Traffic Controller authorizes or blocks movement by applying governance constraints.
- Operations Manager acts as an operational executive within delegated governance, not as an unconstrained authority.
- Dispatch remains the governed implementation path once movement is authorized.

Allowed interpretation:

- Operations Manager reviews advisory evidence, checks Traffic Controller constraints, and moves work through Dispatch when authorized.
- Background Operations creates a request that asks for a movement decision but does not make that decision.

Prohibited interpretation:

- Background Operations opens a dispatch record directly because a watch fired.
- A provider-routing panel schedules a provider because it identified a good fit.
- Operations treats a missing blocker as permission to bypass governance.

## Authority Downward / Evidence Upward Model

```text
Authority flows downward.
Evidence flows upward.
```

Practical meaning:

- Steward-approved governance delegates authority downward to Chief Architect, Traffic Controller, Operations Manager, Dispatch, and provider seams.
- Runtime, audit, validation, Background Operations, provider recommendations, and Office panels produce evidence upward for decision-makers.
- Evidence informs decisions; it does not replace the authority chain.

Allowed interpretation:

- Validation evidence is attached to a review request for Chief Architect / Steward acceptance.
- Provider-routing evidence is visible in an Office panel for Traffic Controller / Operations Manager review.

Prohibited interpretation:

- A passing validation command automatically marks a package institutionally accepted.
- A runtime status panel grants itself approval controls.
- A recommendation artifact assigns a worker or provider.

## Resident / Runtime Separation Model

```text
The runtime never becomes the resident.
The resident never becomes the runtime.
```

Practical meaning:

- Runtime infrastructure may compute, observe, evaluate watches, and write governed requests or telemetry.
- Residents may express role-specific judgment, continuity, voice, and institutional function within their boundaries.
- Runtime must not claim resident identity, persona continuity, private judgment, or character authority.
- Residents must not become daemons, queues, provider adapters, schedulers, event systems, or mechanical execution loops.

Allowed interpretation:

- A resident-facing integration document describes how Alfred or Helen consumes Background Operations evidence.
- Background Operations flags resident-sensitive subjects for review instead of acting on them.

Prohibited interpretation:

- A resident profile owns a competing event loop.
- A runtime artifact speaks as a resident or claims resident continuity.
- A resident persona directly dispatches provider work as infrastructure.

## Recommendation / Decision Separation Model

```text
Recommendations are evidence, not decisions.
```

Practical meaning:

- Provider Routing Recommendations identify provider fit and constraints.
- Provider Routing Office panels are visibility surfaces.
- A recommendation may inform Traffic Controller / Operations Manager decisions, but it is not itself a decision, schedule, dispatch, assignment, approval, provider call, or execution.

Allowed interpretation:

- A recommendation says `codex_cloud_web` is appropriate because work is documentation and deterministic validation.
- An Office panel exposes `advisory_only: true` and warns that movement still requires authorization.

Prohibited interpretation:

- Recommendation generation automatically schedules work.
- A provider-routing artifact mutates Dispatch Queue records.
- A panel turns advisory status into an approval button or provider execution command.

## Validation / Acceptance Separation Model

```text
Validation results are evidence, not institutional acceptance.
```

Practical meaning:

- Audit and validation produce deterministic evidence, findings, receipts, reports, and risk signals.
- Chief Architect and Steward acceptance remain distinct from validation output.
- A validation pass means required checks passed; it does not mean doctrine, governance, architecture, or institutional truth was accepted.

Allowed interpretation:

- A work package receipt reports validation commands and declares readiness for Chief Architect review.
- An audit verdict records evidence and non-blocking findings.

Prohibited interpretation:

- A validation recipe closes a work package by itself.
- Runtime validation evidence is treated as source-controlled institutional truth.
- A passing test suite overrides Steward or Chief Architect review.

## Dispatch Integrity

```text
Dispatch remains the governed implementation path.
```

Practical meaning:

- Dispatch Queue is the single governed implementation path for candidate work that is ready for provider handoff.
- Execution-provider adapters implement through provider seams beneath Dispatch.
- Background Operations, provider recommendations, Office panels, validation recipes, and runtime service loops may not replace Dispatch.

Allowed interpretation:

- Authorized work enters Dispatch and is translated to provider-neutral adapter requests.
- A deterministic dry-run adapter validates handoff shape while recording that no live provider was called.

Prohibited interpretation:

- Background Operations writes directly to provider adapters.
- A new package creates a second dispatch queue for convenience.
- Runtime service loops execute providers, repair code, approve merges, or stash active tree dirtiness.

## Provider Infrastructure Beneath Operations

Execution Providers implement. They do not govern, authorize, accept, or decide institutional truth.

Provider infrastructure is an implementation substrate beneath Operations and Dispatch. It may translate governed records into provider-specific handoffs through adapter contracts. It may not create a provider catalog, routing authority, office, queue, event system, or autonomous decision layer unless Steward-approved governance explicitly supersedes this doctrine.

## Background Operations Boundary

Background Operations is mechanical infrastructure, not institutional authority.

It may:

- observe durable artifacts;
- evaluate watches;
- create events, governed requests, status, and reports;
- flag review needs and boundary risks;
- publish Office-readable evidence.

It may not:

- approve movement;
- dispatch work;
- assign workers;
- execute providers;
- become a routing authority;
- accept institutional truth;
- become a resident or character authority.

## Operations Manager, Traffic Controller, and Steward

The Operations Manager is an operational executive acting within delegated governance. The role may coordinate approved movement and operational execution, but must honor Traffic Controller constraints, Dispatch integrity, and Steward doctrine.

Traffic Controller is the movement constraint and authorization enforcement layer. It applies governance to authorize, block, or require review for movement.

Steward is the doctrine, governance, exception, and final authority layer. Steward-approved governance may supersede this doctrine explicitly; absent such approval, future work packages inherit this doctrine.

## Inheritance Guidance for Future Work Packages

Future work packages inherit this doctrine unless explicitly superseded by Steward-approved governance.

Every future package that touches runtime, operations, provider routing, Dispatch, Background Operations, residents, validation, audit, Office surfaces, or governance should ask:

1. Does this preserve the canonical operating stack?
2. Does movement remain authorized by Traffic Controller according to governance?
3. Does authority flow downward and evidence upward?
4. Does runtime remain separate from residents?
5. Do recommendations remain evidence rather than decisions?
6. Do validation and audit remain evidence rather than acceptance?
7. Does Dispatch remain the governed implementation path?
8. Are provider systems implementation substrate beneath Operations?
9. Are any apparent violations recorded as boundary findings?

Packages that need exceptions must name the exception, cite the superseding Steward-approved governance, and record the boundary impact in their completion receipt.

## Boundary Finding Treatment

A breach or ambiguity in this doctrine should be treated as a boundary finding. It is not a matter of local implementation preference.

Examples of boundary findings include:

- a runtime becoming a dispatcher, provider, resident, governance authority, or acceptance authority;
- Operations bypassing Traffic Controller constraints or Dispatch;
- recommendation artifacts acting as decisions;
- validation artifacts acting as institutional acceptance;
- residents owning runtime infrastructure;
- provider infrastructure creating new autonomous authority layers.

Boundary findings should be escalated through Chief Architect / Steward review and, where privacy or resident boundaries are implicated, Ingrid / Privacy and Boundary Office review.
