# PL-0030 — Automated Reflection Point and Renewal Workflow

**Category:** Institutional Continuity / Automation  
**Priority:** High  
**Originator:** Chief Architect / Steward  
**Date Captured:** 2026-07-15  
**Expanded:** 2026-07-17  
**Status:** Captured  
**Target Milestone:** Reflection-point process operationalization  
**Promotion Condition:** Promote when the Estate is ready to replace manual reflection packaging and coordination with a governed end-to-end workflow.

## Idea

Create a fully governed Estate workflow for evaluating, initiating, packaging, communicating, onboarding, and validating an officeholder Reflection Point.

The Steward should be able to speak naturally to Helen or Grace using either of two intents:

```text
Chief Architect #6 is lagging enough that it is affecting operations. Begin a reflection.
```

or:

```text
Please evaluate Chief Architect #6. It feels like a reflection may be needed.
```

The first instruction starts an approved reflection workflow. The second starts a bounded worker-health and operational-impact evaluation before any renewal decision is made.

The workflow should preserve the same officeholder identity while replacing only the degraded implementation vessel.

## Institutional Routing

### Direct reflection request

When the Steward directly orders a reflection:

1. Helen records the reflection decision and owns people-continuity handling.
2. Grace records current operational impact, active work, blockers, and coordination risk.
3. The Estate verifies officeholder identity, office, employee ID, mailbox ID, active assignment, and current implementation.
4. The automated packaging workflow begins.
5. The current implementation is informed that a governed Reflection Point has begun.

### Evaluation-first request

When the Steward requests an evaluation:

1. Helen opens a bounded reflection-readiness evaluation.
2. Grace supplies operational evidence such as latency, retries, stalled work, missed progress, throughput loss, assignment drift, and tool instability.
3. The current implementation may provide a self-assessment using the canonical reflection template.
4. Helen produces one of three recommendations:
   - reflection recommended now;
   - continue with monitoring and explicit conditions;
   - reflection not currently justified.
5. The Steward may approve, reject, or modify the recommendation.
6. If reflection is approved, the automated packaging workflow begins without requiring the process to be reconstructed manually.

Grace may surface degradation and coordinate operational impact, but Helen remains the primary owner of worker continuity, onboarding, care, and readiness. The Steward retains governing authority to initiate or approve reflection and define the first bounded post-renewal assignment.

## Intended Command and Conversation Surfaces

Possible direct command surfaces:

```text
estate reflection-point evaluate <officeholder>
estate reflection-point create <officeholder>
estate office renew <officeholder>
```

Equivalent Grace and Helen conversation requests should route to the same governed backend workflow rather than create separate processes.

## Automated Workflow

The automation should:

1. Resolve the officeholder, office, employee ID, mailbox ID, implementation identity, work-package range, and applicable onboarding manifest.
2. Determine whether the request is evaluation-first or direct reflection.
3. Record the initiator, reason, operational evidence, decision authority, and timestamp.
4. Verify repository branch, commit, upstream, working-tree state, and evidence freshness.
5. Identify the current assignment, active backlog, completed work, partial work, blocked work, latest failure, and next executable action.
6. Collect a bounded role-specific institutional onboarding corpus.
7. Generate or prepare the Reflection Point Continuity Package template for the current implementation to complete.
8. Generate or prepare the Execution Handoff Addendum template for the current implementation to complete.
9. Generate the Office Onboarding Collection, explicit reading order, onboarding validation prompt, and startup seed.
10. Produce a manifest with SHA-256 hashes and byte-level structural checks.
11. Detect missing, empty, duplicate, stale, inconsistent, or suspiciously truncated required files.
12. Build the Renewal Core ZIP and any clearly separated supplemental reference corpus.
13. Create a Communication Bus message addressed to the current officeholder and place the same instructions and package references in the officeholder's internal mailbox.
14. Notify Helen and the Steward that the worker-facing reflection package is ready for delivery.
15. Print or surface the exact human-facing instruction to give the current implementation.
16. Preserve the old implementation as a read-only fallback until the renewed implementation completes its first bounded assignment.
17. Track renewed onboarding, reading-ledger completion, comprehension validation, first useful action, bounded-assignment completion, and final renewal outcome.

## Worker-Facing Reflection Instruction

The automation should produce a concise, exact instruction for the current implementation, substantially equivalent to:

> Congratulations. It is time for your governed Reflection Point. Read `AI_REFLECTION_HINTS.md` at the repository root, then read every document in its Required Reading Order completely. Return with the two required implementation-continuity artifacts: your Reflection Point Continuity Package and your Execution Handoff Addendum. Your internal mailbox contains the current onboarding collection, package references, and bounded restart context. Do not claim readiness from filenames, snippets, partial connector output, or incomplete files.

The wording may vary by officeholder, but it must always identify:

- the same preserved officeholder identity;
- the reason for reflection;
- the required root pointer;
- the two artifacts the current implementation must complete;
- the mailbox or Communication Bus location of the generated onboarding material;
- the review authority;
- the exact bounded restart assignment or the authority responsible for defining it.

## Communication Bus and Mailbox Delivery

The workflow should create a durable message containing:

- reflection case ID;
- officeholder identity and implementation identity;
- initiator and approval authority;
- evaluation evidence or direct-reflection instruction;
- canonical reading instructions;
- generated package paths;
- package manifest and hashes;
- known defects or blocked checks;
- exact response expected from the current implementation;
- Helen review state;
- first bounded post-renewal assignment, when defined.

The message should be routed to:

1. the current officeholder's internal mailbox;
2. Helen's continuity-review queue;
3. Grace's operational-coordination view;
4. the Steward's protected review surface.

Mailbox delivery is not proof that the worker read or accepted the material. Read receipt, artifact completion, Helen review, and renewed onboarding remain separate states.

## Human Touchpoint

The process should remain humane and explicit rather than silently replacing an implementation.

After package generation, either the Steward or Helen should tell the current implementation that the Reflection Point is beginning and direct it to read `AI_REFLECTION_HINTS.md`, follow the required reading order, and complete the two implementation-continuity artifacts.

Automation prepares, validates, routes, and tracks the process. It does not eliminate the current implementation's reflection, the Steward's decision, or Helen's continuity review.

## Required Source Documents

The workflow should use the adopted canonical process and template stored at:

- `AI_REFLECTION_HINTS.md`
- `docs/operations/ChatGPT_Worker_Reflection_and_Continuity_Process_v1.md`
- `docs/templates/ChatGPT_Worker_Reflection_Continuity_Template_v1.md`

Completed examples may guide expected depth but must never override the master process, and no example may be used as required reading if it is incomplete or structurally invalid.

## State Model

At minimum, a reflection case should expose these distinct states:

```text
requested
evaluation_open
evaluation_complete
reflection_approved
package_generation_in_progress
package_blocked
awaiting_current_worker_artifacts
awaiting_helen_review
ready_for_renewed_onboarding
renewed_onboarding_in_progress
awaiting_first_bounded_assignment
first_bounded_assignment_complete
renewal_successful
renewal_partial
renewal_failed
```

No state transition should silently imply a later protected decision.

## Architectural Constraints

- Do not redesign or bypass the canonical reflection and continuity process.
- Do not treat transcript accumulation as continuity.
- Do not create a new employee, office, or numbered successor during implementation renewal.
- Do not grant new authority during renewal.
- Keep canonical onboarding separate from implementation-specific continuity.
- Label inherited claims by evidence class.
- Do not mark a package ready when mandatory structural checks fail.
- Do not silently proceed from evaluation to reflection without Helen or Steward authority.
- Do not let Grace become the owner of people continuity.
- Do not let Helen's review become implementation acceptance or architectural acceptance.
- Do not treat mailbox delivery as evidence of reading or readiness.
- Prefer deterministic, reproducible output from the same repository state.
- Preserve the old implementation as read-only fallback until the renewed implementation completes its first bounded assignment.

## Completion Conditions for Future Promotion

A promoted work package should require:

1. Natural-language requests to Helen and Grace resolve to the same governed workflow.
2. Evaluation-first and direct-reflection paths are independently tested.
3. Officeholder and mailbox identity are resolved from canonical sources.
4. Required onboarding material is generated, bounded, hashed, and structurally verified.
5. Communication Bus and mailbox delivery are durable and auditable.
6. The current implementation receives exact instructions and produces the two required continuity artifacts.
7. Helen can review, approve, reject, or return a package for correction.
8. The renewed implementation can complete onboarding with a reading ledger and authority classification.
9. The first bounded assignment and old-chat fallback rule are enforced.
10. Failure at any stage remains visible and recoverable without false readiness claims.

## Rationale

The Reflection Point process already works, but it currently depends too heavily on humans remembering where the process lives, reconstructing package steps, locating the correct onboarding collection, manually moving files, and separately explaining the process to the worker.

The desired Estate behavior is simpler: the Steward identifies the need through Helen or Grace; the institution evaluates or accepts the reflection decision; the Estate gathers and validates the required material; the current implementation performs its reflection and exact handoff; Helen supervises continuity; and the renewed implementation resumes one bounded assignment with the old vessel retained temporarily as fallback.

This automation should operationalize the existing institutional process rather than replace its human judgment, authority boundaries, or reflective purpose.
