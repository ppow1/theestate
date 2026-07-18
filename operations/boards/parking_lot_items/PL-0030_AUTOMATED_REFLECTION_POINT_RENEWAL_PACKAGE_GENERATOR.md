# PL-0030 — Automated Reflection Point and Renewal Workflow

**Category:** Institutional Continuity / Automation  
**Priority:** High  
**Originator:** Chief Architect / Steward  
**Date Captured:** 2026-07-15  
**Integrated design approved:** 2026-07-18
**Status:** Approved design; automation not implemented
**Target milestone:** Reflection-point process operationalization

## Status and authority boundary

This item specifies a governed orchestrator for the adopted process in
`docs/operations/ChatGPT_Worker_Reflection_and_Continuity_Process_v1.md`. The manual process is the authority and judgment framework. This approved design does **not** prove an executable orchestrator, natural-language routing, mailbox delivery, Communication Bus publication, notification, lifecycle tracker, or conversation-creation capability exists. Until repository implementation and validation evidence prove an operation available, use the documented manual fallback and label its evidence manual. Opening a conversation is never an implied operation.

When an official capability is implemented and available, it is the preferred execution path for deterministic collection, validation, packaging, hashing, delivery, notification, and state tracking. It never decides a protected institutional question.

| Actor | Final responsibility |
|---|---|
| Steward | Final institutional authority to direct, defer, or accept reflection where judgment is required; may define the bounded first assignment and success evidence. |
| Helen/designated continuity reviewer | Reviews identity, corpus, worker artifacts, warnings, and package sufficiency; alone approves progression into renewed onboarding; confirms renewal before retirement. |
| Reflecting worker | Assesses degradation, verifies claims, labels uncertainty, and authors/approves the Reflection Point Continuity Package and Execution Handoff. |
| Grace | Supplies operational evidence, schedules, coordinates, surfaces status, and checks that notices occur; cannot warrant reflection, approve/alter continuity, confirm onboarding, or retire an implementation. |
| Automation | Executes only deterministic operations and records evidence; it cannot assess, authorize, approve, accept, or retire. |
| Renewed implementation | Verifies the package, completes onboarding, reports discrepancies, and performs the bounded first assignment. |

The office and officeholder identity persist; only the implementation changes. The prior implementation and evidence remain available read-only until onboarding and the bounded first assignment succeed and renewal is confirmed.

## Initiation paths

### Evaluation request

An uncertain or exploratory request (for example, “Please evaluate Chief Architect 6”) creates `evaluation_requested`, not authorization to renew.

1. Helen or the Steward records the request and automation or the manual operator resolves office, officeholder, current implementation, and mailbox without guessing.
2. The current implementation performs the assessment in `AI_REFLECTION_HINTS.md`, distinguishing workload pressure from operational degradation using verified evidence.
3. Grace may supply operational observations, but does not decide the result.
4. The worker returns a recommendation to Helen and/or the Steward: renew, monitor/defer with conditions, or continue.
5. Packaging cannot begin until the appropriate authority records authorization. An authorized recommendation then enters the direct flow; a recommendation alone is not authorization.

### Direct reflection directive

An explicit authoritative direction (for example, “Begin reflection”) creates `reflection_authorized`.

1. Record the directive, source, reason, scope, and time; resolve office, officeholder, implementation, and mailbox without guessing.
2. Begin available automated preparation immediately, or activate the recorded manual fallback.
3. In parallel, instruct the current implementation to author the two required continuity deliverables. Automation may prepare templates and ingest/validate artifacts but may not write or silently change the worker's judgments.
4. Preserve the prior implementation through reviewed onboarding and the successful bounded first assignment.

No intake surface may reinterpret an evaluation as a directive. Conversation and natural-language command surfaces remain design-only unless separately implemented and evidenced.

## Worker recommendation before manual assembly

Before manually assembling a renewal package, the worker must recommend the official automation when repository evidence shows it is implemented and available. The recommendation records the officeholder, initiation type, reason/degradation evidence, current assignment and operational risk, repository and branch, and known blockers. It does not authorize reflection. If availability is not proven, record that fact and use manual fallback rather than claiming an automated run.

## Approved orchestration sequence

Following recorded authorization, an implemented orchestrator must perform these ordered, auditable operations:

1. Resolve office, officeholder, current implementation, mailbox, and governing office documents; stop on ambiguity.
2. Verify repository identity, branch, remote, working tree, relevant commit, and freshness.
3. Capture the evaluation authorization or direct directive and authority source.
4. Collect the bounded institutional onboarding corpus and its reading order.
5. Collect current implementation continuity material; require or ingest the worker-authored Reflection Point Continuity Package and Execution Handoff.
6. Validate existence, non-emptiness, readability/encoding, required headings and fields, complete endings, placeholders, exact manifest membership, hashes, duplicates, stale/nonexistent paths, and suspected truncation.
7. Produce a versioned manifest, SHA-256 hashes, validation report, package, and ZIP without overwriting an earlier successful version.
8. Deliver to the resolved mailbox, publish the Communication Bus notice, and notify Helen and Grace, recording evidence for each operation. An unavailable adapter triggers fallback; it must not be reported as successful.
9. Provide renewed-worker startup instructions and move to Helen's mandatory review. Delivery is not reading, approval, onboarding, or conversation creation.
10. After Helen approves progression, track onboarding, the bounded first assignment, confirmation, and only then institutionally authorized retirement of the prior implementation.

Every run produces or references: run ID; office and officeholder; prior and renewed implementation IDs when known; initiation type and authority source; repository, branch, remote, commit, and working-tree evidence; onboarding-corpus manifest; both worker deliverables; structural report; file manifest and hashes; package/ZIP locations; mailbox evidence; Bus message ID/path; notification evidence; lifecycle state; warnings, uncertainties, blockers, last successful action; and exact next action. An unavailable output is recorded as unavailable, never fabricated.

## Startup instruction contract

The package must tell the renewed implementation to: (1) read `AI_REFLECTION_HINTS.md`; (2) read the adopted process; (3) read the office corpus; (4) read the Reflection Point Continuity Package; (5) read the Execution Handoff; (6) verify repository and evidence claims; (7) report discrepancies, stale/missing evidence, and uncertainty; (8) report onboarding completion to Helen/designated reviewer; and (9) accept only the identified bounded first assignment until continuity is confirmed. Merely opening or receiving a package does not complete onboarding or renewal.

## Mandatory Helen review

After packaging and evidenced delivery, and before `approved_for_onboarding`, Helen/designated reviewer confirms the correct officeholder/mailbox, appropriate complete corpus, both worker artifacts, structural pass or explicitly approved exceptions, visible warnings, clear startup instructions, identified bounded first assignment, and preservation of the prior implementation. Helen may reject, return for correction, or approve progression. Grace may coordinate the response but cannot perform this approval.

## Manual fallback

Use `manual_fallback_active` whenever automation is unimplemented, unavailable, fails, or cannot safely resolve an entity. Record the reason and last attempted action. A named operator then performs the same bounded collection, two worker deliverables, structural checks, corpus, manifest and hashes where technically possible, versioned package, manual mailbox delivery evidence, manual Bus notice, notifications, lifecycle log, and exact next action. Helen reviews before onboarding, and the prior implementation remains read-only until success. If mailbox or Bus operations themselves are unavailable, record the unavailable capability and an approved alternate handoff/notice with receipt; do not claim the unavailable operation occurred. Manual execution is governed and evidence-equivalent, not an undocumented exception.

## Lifecycle and transition evidence

| State | Responsible actor and evidence required for entry/exit |
|---|---|
| `evaluation_requested` | Helen/Steward records requester, intent, reason, target, and time. |
| `assessment_in_progress` | Worker acknowledges assessment; identity and evidence sources are recorded. |
| `reflection_recommended` | Worker submits evidence-based recommendation; Helen/Steward must authorize before packaging. |
| `reflection_authorized` | Steward or applicable institutional authority records directive/approval and source. |
| `package_building` | Automation or named manual operator records run/version, resolved identities, repository state, and progress. |
| `package_validation_failed` | Validator records failed checks, partial artifacts, last success, owner, and retry action; no delivery as ready. |
| `package_ready_for_review` | Executor records a complete versioned package, manifest, hashes, validation result, and actual delivery/notice evidence or explicit approved exception. |
| `helen_review_required` | Executor routes the evidence to Helen; no later protected state is implied. |
| `approved_for_onboarding` | Helen records approval, exceptions, startup instructions, bounded assignment, and preservation check. |
| `onboarding_in_progress` | Renewed worker records reading ledger, verification, discrepancies, and acknowledgement. |
| `first_assignment_in_progress` | Helen/Steward records bounded assignment and success evidence; renewed worker records execution. |
| `renewal_confirmed` | Helen and, where required, Steward record onboarding and assignment success. |
| `previous_implementation_retired` | Authorized actor records retirement only after `renewal_confirmed`, preserving audit evidence. |
| `manual_fallback_active` | Operator records unavailable/failed capability, reason, alternate procedure, receipts, and current step. |
| `renewal_blocked` | Actor at the failed gate records blocker, owner, evidence, prior state, and exact recovery action. |

Transitions append to history; they do not erase prior states. `manual_fallback_active` records an execution mode and may return to the appropriate lifecycle gate. A failed/incomplete run can never imply approval, confirmation, or retirement.

## Failure, retry, versioning, and idempotency

- Fail closed instead of guessing unresolved officeholder, mailbox, repository, authority, or conflicting evidence.
- Allocate an immutable run ID and monotonically versioned output before side effects. Never overwrite a successful package; changed inputs or worker artifacts require a new version and hashes.
- Persist inputs, partial output, failed checks, timestamps, actor, last successful action, next action, and errors so a run can resume or be repeated.
- Give each mailbox delivery, Bus publication, and notification a deterministic idempotency key derived from case/run, package version, operation, and recipient. Before retry, inspect the durable receipt; reuse it if successful and retry only missing/failed operations. Never duplicate a successful side effect.
- Preserve failed-run evidence. Mark incomplete output non-ready and prevent onboarding progression or prior-implementation retirement.

## Durable audit trail

Automated and manual cases retain an append-only lifecycle/actor log, directive or authorization, reason and evidence, identity resolution, implementation IDs, repository evidence, complete file inventory and hashes, validation results/exceptions, package/version locations, delivery/Bus/notification receipts or explicit unavailable status, Helen decision and corrections, renewed-worker reading/discrepancy record, first-assignment outcome, renewal confirmation, and any retirement authority/time. The trail must answer who, why, what state and files, which checks, where delivered, who reviewed, when success occurred, and when/why the predecessor was retired.

## Promotion and implementation acceptance

Future implementation work must demonstrate independently tested evaluation and direct paths, canonical identity resolution, deterministic packages, durable idempotent adapters, Helen's protected gate, fallback behavior, onboarding/first-assignment tracking, and failure recovery. Only evidenced capabilities may change this item's status from approved design. The adopted manual workflow remains operational throughout promotion.
