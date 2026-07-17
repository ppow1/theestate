# CAMPAIGN-0681 — Estate Operationalization

Status: Launch authorized — ready for Codex execution  
Parent authority: Steward direction to operationalize the Estate after campaign-level execution capability is available  
Architecture and acceptance owner: Chief Architect  
Operational owner: Grace, within existing authority boundaries  
Priority: High  
Risk class: Elevated — cross-office operational integration without authority transfer

## Approved intent

- Intake source kind: Steward directive.
- Canonical intake reference: Steward direction following CAMPAIGN-0670 and WP-0678 review.
- Disposition: Execute one large dependency-aware operationalization campaign through the WP-0678 campaign-level Codex capability.

## Objective

Make the Estate behave as one governed operating institution rather than a collection of individually functional systems.

The campaign connects existing offices, residents, services, campaigns, work packages, mailboxes, health signals, staffing, validation, escalation, continuity, and Steward review into one observable operational flow. It must not create a parallel constitution, office structure, scheduler, dispatch queue, mailbox, validator, state store, dashboard authority, or acceptance mechanism.

Successful completion means the Estate can observe canonical state, reconcile dependencies and readiness, identify the next permitted action, coordinate through existing offices and communications, perform only authorized mechanical actions, verify results, record durable evidence, recover from interruption, and stop at protected gates.

## Constitutional precedence

Accepted Estate constitutional, office, campaign, engineering, communication, mailbox, PTM, Dispatch, validation, readiness, evidence, acceptance, reflection, and continuity standards remain authoritative.

If this campaign conflicts with an accepted canonical artifact, the accepted canonical artifact prevails. Any constitutional or office-authority change must be isolated and separately approved.

## Required authoritative inputs

Before execution, discover and read the canonical successors of at least:

- `AI_HINTS.md`
- `AI_START_HERE.md`
- `AI_COMMUNICATION_HINTS.md`
- `collaboration/campaigns/CAMPAIGN_0670_ACCEPTANCE_PACKAGE.md`
- WP-0670 through WP-0675 completion receipts and accepted deliverables
- WP-0678 specification, completion evidence, and protected acceptance
- office charters for Grace, Helen, Alfred, Chief Architect, and Steward
- canonical PTM, Dispatch, mailbox, repository-message, resident, service-health, validation, readiness, evidence, acceptance, reflection, and continuity specifications
- CAMPAIGN-0680 artifacts where decision-support outputs or dashboards overlap
- `collaboration/campaigns/CAMPAIGN_0681_WORK_PACKAGE_NAMESPACE_RESOLUTION.md`

A moved path is not permission to invent a replacement.

## Scope

The campaign includes implementation, integration, validation, and bounded documentation necessary to establish:

- canonical operational state and event normalization;
- campaign and work-package momentum observation;
- dependency, readiness, health, staffing, validation, evidence, communication, and authority-aware coordination;
- resident and service health integration;
- blocker classification and escalation;
- explicit office interaction contracts through existing mechanisms;
- staffing and capability request flows;
- mailbox and repository-message routing integration;
- pause, resume, retry, recovery, and fail-closed behavior;
- bounded policy and guardrail enforcement;
- durable audit, explainability, checkpoint, replay, notebook, reflection, and continuity evidence;
- Steward visibility and protected decision surfaces;
- a bounded Continuous Momentum Engine;
- one real but bounded institutional pilot;
- campaign-level integration and protected acceptance evidence.

## Non-goals and protected surfaces

This campaign shall not:

- create a new office or department when an existing office can own the function;
- transfer final authority away from the Steward;
- grant Grace architectural, staffing, merge, deployment, engineering-acceptance, or final institutional authority;
- grant Helen engineering-priority, architectural, or acceptance authority;
- grant Alfred execution or acceptance authority;
- treat Codex, a local model, or any provider as an office or institutional authority;
- bypass PTM, Dispatch, mailbox, repository-message, validation, readiness, evidence, or acceptance mechanisms;
- silently merge, deploy, accept, close, spend, staff, or disclose protected information;
- conceal degraded residents, stale evidence, failed validation, blocked authority, or partial failure;
- build an unconstrained autonomous-agent loop.

## Campaign execution policy

CAMPAIGN-0681 shall use:

- one campaign handoff;
- one campaign branch;
- one bounded commit per atomic work package;
- dependency-aware execution;
- only the manifest’s explicit parallel groups;
- durable checkpoints and resumability;
- fail-closed partial-failure handling;
- per-package completion evidence;
- aggregated campaign evidence;
- one campaign pull request;
- no automatic merge or acceptance.

## Authoritative work-package graph

The authored package set and exact manifest paths are authoritative. Earlier summary labels superseded by the namespace-resolution record are non-authoritative.

| Package | Objective | Depends on | Gate |
|---|---|---|---|
| WP-0688 | Estate operational current-state and canonical-reuse map | none | G1 |
| WP-0689 | Operational state, event, and transition contract | WP-0688 | G1 |
| WP-0690 | Authority-aware operational action taxonomy | WP-0688, WP-0689 | G1 |
| WP-0691 | Resident and service health signal integration | WP-0688, WP-0689 | G2 |
| WP-0692 | Campaign and work-package momentum observer | WP-0688, WP-0689 | G2 |
| WP-0693 | Operational blocker and escalation classifier | WP-0690, WP-0691, WP-0692 | G2 |
| WP-0694 | Grace operational coordination surface | WP-0690, WP-0692, WP-0693 | G3 |
| WP-0695 | Helen staffing and capability request integration | WP-0690, WP-0693 | G3 |
| WP-0696 | Alfred communication and mailbox routing integration | WP-0690, WP-0693 | G3 |
| WP-0697 | Engineering Department operational integration | WP-0688, WP-0689, WP-0690, WP-0692, WP-0693 | G3 |
| WP-0698 | Readiness, validation, and evidence signal unification | WP-0688 through WP-0693 | G4 |
| WP-0699 | Operational pause, resume, retry, and recovery controls | WP-0689 through WP-0693, WP-0698 | G4 |
| WP-0700 | Continuous Momentum Engine bounded decision loop | WP-0689 through WP-0699 as declared in the manifest | G5 |
| WP-0701 | Operational policy and guardrail enforcement | WP-0689, WP-0690, WP-0693, WP-0699, WP-0700 | G5 |
| WP-0702 | Operational audit trail and decision explainability | WP-0689, WP-0690, WP-0698, WP-0700, WP-0701 | G5 |
| WP-0703 | Operational dashboard and Steward visibility surface | WP-0693, WP-0698, WP-0702 | G6 |
| WP-0704 | Operational acceptance, graduation, and campaign closeout | WP-0691 through WP-0703 as declared in the manifest | G6 |
| WP-0705 | Failure-mode, authority-boundary, and degraded-service validation | WP-0700 through WP-0704 | G7 |
| WP-0706 | Bounded real-work pilot campaign | WP-0705 | G7 |
| WP-0707 | Estate Operationalization integration and acceptance | all prior CAMPAIGN-0681 packages | G8 |

For CAMPAIGN-0681, the canonical WP-0697 is only `WP-0697_ENGINEERING_DEPARTMENT_OPERATIONAL_INTEGRATION.md`. The legacy WP-0697 and its completion receipt belong to another campaign lineage and provide no CAMPAIGN-0681 completion evidence.

## Milestones and release authority

| Gate | Prerequisites | Release authority |
|---|---|---|
| G0 | WP-0678 accepted; manifest valid; namespace reconciled; launch baseline verified | Chief Architect and Steward where protected |
| G1 | WP-0688 through WP-0690 | Chief Architect |
| G2 | WP-0691 through WP-0693 | Chief Architect |
| G3 | WP-0694 through WP-0697 | Chief Architect plus office acknowledgements where required |
| G4 | WP-0698 and WP-0699 | Chief Architect |
| G5 | WP-0700 through WP-0702 | Chief Architect; Steward for protected action classes |
| G6 | WP-0703 and WP-0704 | Steward review |
| G7 | WP-0705 and WP-0706 | Chief Architect and Steward |
| G8 | WP-0707 and aggregate evidence | Protected acceptance lane; no automatic acceptance |

## Required behavioral model

The resulting operational flow must:

1. Observe canonical state and new events.
2. Reconcile dependencies, readiness, health, evidence, staffing, validation, communication state, and authority.
3. Classify work as eligible, blocked, degraded, failed, or protected.
4. Explain the next permitted action.
5. Perform only explicitly delegated mechanical actions.
6. Verify the result.
7. Record recommendations, actions, refusals, transitions, failures, retries, and escalations.
8. Resume deterministically from the last safe checkpoint.
9. Stop at review, merge, deployment, acceptance, budget, privacy, staffing, architectural, and Steward gates.

Observation, recommendation, coordination, execution request, mechanical action, office decision, protected decision, and acceptance must remain distinct.

## Shared-file and collision rules

- Exact manifest paths control package identity.
- Canonical registries and office charters are read-only unless a package explicitly grants modification authority.
- Shared operational state and dashboard surfaces are integrated only through designated packages.
- Packages touching the same runtime seam must be sequenced unless the manifest proves collision-free parallel execution.
- No package may rewrite another package’s completion receipt.
- WP-0707 owns final campaign aggregation and acceptance-package updates.

## Pilot requirement

WP-0706 must demonstrate one bounded workflow crossing multiple existing Estate capabilities, including readiness, dependency, health, staffing, validation, authority, Grace coordination, Helen and Alfred interaction through their existing lanes, Engineering execution, interruption recovery, protected escalation, Steward visibility, and truthful evidence. It must not automatically merge, deploy, or accept.

## Acceptance criteria

CAMPAIGN-0681 is complete only when the Estate truthfully demonstrates an end-to-end governed operational cycle through the WP-0678 execution capability, reuses canonical systems rather than duplicating them, recovers from interruption, stops at protected gates, completes the bounded pilot, and presents one campaign pull request with aggregate evidence. Merge, deployment, and institutional acceptance remain protected human actions.

## Required deliverables

1. Complete machine-readable execution manifest.
2. Atomic work packages WP-0688 through WP-0707.
3. Implementation and tests in existing canonical seams.
4. Independent per-package completion receipts.
5. Gate evidence and authority decisions.
6. Failure-mode and degraded-service validation reports.
7. Pilot evidence.
8. Operational documentation for affected offices.
9. Campaign aggregate evidence.
10. `collaboration/campaigns/CAMPAIGN_0681_ACCEPTANCE_PACKAGE.md`.
11. One campaign pull request awaiting protected review.

## Amendment history

| Version/time | Action | Authority/reference | Effect |
|---|---|---|---|
| Draft 1 | Initial campaign charter | Steward direction; Chief Architect drafting | Campaign remained unlaunched pending prerequisites |
| 2026-07-16 G0 activation | WP-0678 acceptance and launch authorization recorded | WP-0678 protected acceptance; CAMPAIGN-0681 G0 authorization | Campaign moved to launch-authorized state |
| 2026-07-17 topology reconciliation | Resolved WP-0697 collision and reconciled WP-0701 through WP-0704 to the authored package set | `CAMPAIGN_0681_WORK_PACKAGE_NAMESPACE_RESOLUTION.md` | Exact manifest paths and amended authored objectives control execution |