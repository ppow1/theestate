# WP-0710 — Reflection Automation Integration

## Status
Pending

## Priority
High

## Owner
Chief Architect

## Execution Lane
Codex

## Purpose
Integrate the adopted manual reflection and continuity process with the automated renewal generator so that reflection remains institutionally governed while packaging, delivery, notification, and renewal preparation become fast, repeatable, and verifiable.

## Problem Statement
The repository currently separates two related mechanisms:

- the manual reflection and continuity process, which governs judgment, authority, worker assessment, and continuity requirements;
- the proposed automated renewal generator described in `operations/boards/parking_lot_items/PL-0030_AUTOMATED_REFLECTION_POINT_RENEWAL_PACKAGE_GENERATOR.md`, which is intended to assemble, validate, package, deliver, and track renewal materials.

Without an explicit integration model, these mechanisms can compete rather than cooperate. A worker may manually package materials even when automation is available, automation may be treated as having authority it does not possess, Helen may be bypassed, or a generated package may be delivered without a completed worker assessment and required handoff artifacts.

The target process is a governed reflection orchestrator, not an autonomous authority. Automation performs deterministic operational work. The reflecting worker, Helen, and the Steward retain their institutional responsibilities.

## Governing Principle
Automation may prepare and move evidence, but it may not decide institutional questions that require judgment.

The authority model must be:

- **Steward:** final authority to direct, defer, or accept reflection when institutional judgment is required;
- **Helen or designated continuity reviewer:** continuity review, staffing/renewal coordination, package sufficiency review, and approval to proceed into renewed onboarding;
- **Reflecting worker:** assessment of degradation, completion of the two required continuity deliverables, uncertainty labeling, and verification of implementation claims;
- **Automation/orchestrator:** repository inspection, collection, validation, packaging, hashing, mailbox delivery, Communication Bus publication, status tracking, and repeatable launch preparation;
- **Renewed implementation:** consume the delivered onboarding and continuity package, verify evidence, complete onboarding, and execute a bounded first assignment.

Automation must never silently promote itself above this authority chain.

## Required Work

### 1. Integrate the adopted process with PL-0030
Update `operations/boards/parking_lot_items/PL-0030_AUTOMATED_REFLECTION_POINT_RENEWAL_PACKAGE_GENERATOR.md` and the governing reflection documents so they describe one complementary workflow.

The integrated documents must state that:

- the manual process is the authority and judgment framework;
- automation is the preferred execution path for deterministic package operations when available;
- the manual fallback remains approved when automation is unavailable or fails validation;
- both paths produce the same required artifacts, validation evidence, review points, and lifecycle records.

### 2. Define two initiation paths
The workflow must support two distinct trigger classes.

#### Evaluation path
Used when the request is uncertain or exploratory, such as:

> Please evaluate Chief Architect 6 because it feels like he may need a reflection.

Required behavior:

1. Resolve the office, officeholder identity, current implementation, and mailbox.
2. Ask the current implementation to perform a reflection assessment using `AI_REFLECTION_HINTS.md`.
3. Require the assessment to distinguish normal workload pressure from operational degradation.
4. Return a recommendation to Helen and/or the Steward.
5. Do not start renewal packaging until authorized.

#### Direct-reflection path
Used when the direction is explicit, such as:

> Chief Architect 6 is lagging enough to affect operations. Begin reflection.

Required behavior:

1. Record the directive and authority source.
2. Resolve the office, officeholder identity, implementation, and mailbox.
3. Begin automated renewal preparation immediately.
4. Instruct the current implementation to complete the required reflection deliverables in parallel.
5. Preserve the previous implementation until renewed onboarding and first bounded assignment succeed.

The system must not reinterpret an evaluation request as an automatic reflection directive.

### 3. Require the worker's automation recommendation
Update the adopted reflection process so that, before manually assembling a package, the reflecting worker must recommend execution of the official automation when it is available.

The worker recommendation must include:

- the officeholder being renewed;
- whether the request is evaluation or direct reflection;
- the reason for reflection or observed degradation;
- the current assignment and operational risk;
- known repository location and branch;
- any known blockers that automation must account for.

The recommendation is not authorization by itself. Authorization remains with the appropriate institutional authority.

### 4. Define the automated orchestration sequence
The automation design must cover the complete renewal workflow, not merely ZIP creation.

At minimum, the orchestrator must:

1. Resolve office, officeholder identity, current implementation identifier, mailbox identifier, and governing office documents.
2. Verify repository identity, branch, remote, working-tree state, and relevant commit.
3. Capture or reference the reflection directive or evaluation authorization.
4. Collect the institutional onboarding corpus.
5. Collect the current implementation continuity materials.
6. Require or ingest the worker-produced Reflection Point Continuity Package.
7. Require or ingest the worker-produced Execution Handoff.
8. Validate required documents structurally.
9. Generate a manifest and cryptographic hashes.
10. Detect missing, empty, duplicate, unreadable, stale-path, placeholder, and truncated files.
11. Build a renewal package and ZIP archive.
12. Deliver the package into the correct officeholder mailbox.
13. Publish a Communication Bus message with package location, status, and next action.
14. Notify Helen and Grace, or their designated successors, without transferring approval authority to Grace.
15. Prepare clear startup instructions for the renewed implementation.
16. Track lifecycle state through review, onboarding, first bounded assignment, and retirement of the previous implementation.
17. Preserve the previous implementation and its evidence as read-only until renewal success is confirmed.

### 5. Define required automation outputs
Each automation run must produce or reference:

- run identifier;
- office and officeholder identity;
- prior and renewed implementation identifiers when known;
- initiation type: evaluation or direct reflection;
- authority source;
- repository, branch, remote, and commit evidence;
- working-tree status;
- institutional onboarding corpus manifest;
- Reflection Point Continuity Package;
- Execution Handoff;
- structural-validation report;
- file manifest;
- file hashes;
- package and ZIP locations;
- mailbox delivery evidence;
- Communication Bus message identifier or file path;
- notification evidence;
- lifecycle state;
- unresolved warnings, uncertainties, and blockers;
- exact next action.

### 6. Define the renewed-worker startup instructions
The delivered renewal package must include an explicit startup instruction that tells the renewed implementation to:

1. Read `AI_REFLECTION_HINTS.md` first.
2. Read the adopted reflection and continuity process.
3. Read the office's institutional onboarding corpus.
4. Read the Reflection Point Continuity Package.
5. Read the Execution Handoff.
6. Verify repository and evidence claims before acting.
7. Identify discrepancies, stale material, missing evidence, and uncertainties.
8. Report onboarding completion to Helen or the designated reviewer.
9. Accept only a bounded first assignment until continuity is confirmed.

The startup instruction must not imply that opening the package alone completes renewal.

### 7. Define Helen's mandatory review point
The integrated process must include a mandatory Helen review after automation completes packaging and delivery but before the renewal is declared operational.

Helen's review must confirm:

- the correct officeholder and mailbox were resolved;
- the onboarding corpus is appropriate and complete;
- both required worker deliverables are present;
- structural validation passed or exceptions are explicitly approved;
- unresolved warnings are visible;
- the renewed implementation has clear startup instructions;
- a bounded first assignment is identified;
- the previous implementation remains preserved until success.

Helen may reject the package, return it for correction, or approve progression to renewed onboarding.

### 8. Define Grace's role without moving authority
Grace may coordinate operational steps, surface status, and ensure notifications or scheduling occur. Grace must not:

- decide whether reflection is institutionally warranted;
- approve continuity sufficiency in Helen's place;
- alter worker-produced continuity content;
- retire the prior implementation;
- declare renewed onboarding successful.

Update the documents to make this distinction explicit.

### 9. Define the approved manual fallback
When automation is unavailable, errors, or cannot safely resolve required entities, the process must fall back to a governed manual workflow.

The manual fallback must require:

1. Explicit recording of why automation was unavailable or rejected.
2. The same two worker deliverables.
3. The same onboarding corpus.
4. The same structural-validation checks.
5. The same manifest and hash expectations where technically possible.
6. Manual mailbox delivery evidence.
7. Manual Communication Bus notice.
8. Helen review before onboarding.
9. Preservation of the previous implementation until renewal succeeds.

Manual fallback must not be treated as an undocumented exception.

### 10. Define failure behavior and idempotency
The automation specification must define safe failure behavior.

It must:

- stop rather than guess when officeholder, mailbox, repository, or authority cannot be resolved;
- avoid overwriting a prior successful package without explicit versioning;
- produce resumable or repeatable runs where practical;
- record partial progress and the last successful action;
- avoid duplicate Communication Bus messages and mailbox deliveries on retry;
- mark incomplete runs clearly;
- preserve failed-run evidence for diagnosis;
- prevent retirement of the previous implementation on a failed or incomplete run.

### 11. Define lifecycle states
Update PL-0030 and governing documents with an explicit lifecycle model. At minimum:

- `evaluation_requested`
- `assessment_in_progress`
- `reflection_recommended`
- `reflection_authorized`
- `package_building`
- `package_validation_failed`
- `package_ready_for_review`
- `helen_review_required`
- `approved_for_onboarding`
- `onboarding_in_progress`
- `first_assignment_in_progress`
- `renewal_confirmed`
- `previous_implementation_retired`
- `manual_fallback_active`
- `renewal_blocked`

Transitions must identify the responsible actor and required evidence.

### 12. Preserve auditability
Every automated or manual renewal must leave a durable audit trail sufficient to answer:

- who initiated or authorized reflection;
- why it was initiated;
- which implementation was renewed;
- what repository state was captured;
- which files were packaged;
- which validation checks passed or failed;
- where the package was delivered;
- who reviewed it;
- when onboarding and first assignment succeeded;
- when the prior implementation was retired.

### 13. Update governing cross-references
Update the adopted reflection documents, `AI_REFLECTION_HINTS.md`, PL-0030, and any directly affected operational guidance so references are consistent.

The documents must not describe automation as implemented if the code does not yet exist. Use clear status language distinguishing:

- adopted process;
- approved automation design;
- implemented capability;
- unavailable capability requiring manual fallback.

## Files Expected to Change
At minimum, inspect and update as necessary:

- `operations/boards/parking_lot_items/PL-0030_AUTOMATED_REFLECTION_POINT_RENEWAL_PACKAGE_GENERATOR.md`
- `AI_REFLECTION_HINTS.md`
- `docs/processes/ChatGPT_Worker_Reflection_and_Continuity_Process_v1.md`
- `docs/templates/ChatGPT_Worker_Reflection_Continuity_Template_v1.md`
- directly related operational, mailbox, Communication Bus, onboarding, or continuity guidance discovered during implementation

This work package defines integration and operational requirements. Implement executable automation only where the repository's existing architecture and PL-0030 status make that work explicitly in scope. Do not falsely mark unimplemented behavior as operational.

## Constraints

- Automation is an executor and orchestrator, not an institutional authority.
- The Steward's authority must remain protected.
- Helen's continuity-review role must not be bypassed.
- Grace may coordinate but may not approve continuity.
- The reflecting worker must still produce or approve the required continuity content.
- The manual fallback must remain valid.
- The previous implementation must remain available and read-only until renewal is confirmed.
- Do not require transcript transfer.
- Do not silently infer unresolved officeholder, mailbox, repository, or authority data.
- Do not claim that a new conversation was opened unless the system actually has that capability and evidence.
- Do not broaden this work into unrelated staffing, mailbox, or Communication Bus redesign.

## Acceptance Criteria

1. PL-0030 and the adopted reflection process describe one complementary workflow.
2. Evaluation and direct-reflection initiation paths are explicitly distinguished.
3. The reflecting worker is required to recommend official automation before manual packaging when automation is available.
4. The authority model clearly separates Steward, Helen, worker, Grace, and automation responsibilities.
5. The full orchestration sequence includes collection, validation, packaging, delivery, notification, review, onboarding, first assignment, and prior-implementation retirement.
6. Required outputs and evidence are explicitly defined.
7. Helen review is mandatory before operational renewal.
8. Grace's coordination role is defined without transferring approval authority.
9. The manual fallback is fully specified and evidence-equivalent.
10. Failure, retry, versioning, and idempotency behavior are documented.
11. Lifecycle states and responsible transition actors are defined.
12. Audit-trail requirements are complete.
13. Documents distinguish approved design from implemented capability.
14. All affected files are structurally complete and cross-references resolve.
15. Repository documentation validation passes.

## Validation Evidence
Codex must provide:

- list of files changed;
- summary of the integrated authority model;
- documented evaluation and direct-reflection flows;
- lifecycle-state table or equivalent evidence;
- manual-fallback flow;
- structural-validation results for changed files;
- evidence that all referenced paths exist or are explicitly marked as future/conditional;
- search results showing no conflicting statements remain about automation authority or implementation status;
- relevant documentation tests or repository validation results.

## Completion Condition
This work package is complete when the adopted reflection process and PL-0030 define one coherent, institutionally governed renewal workflow in which automation performs deterministic orchestration, the worker provides continuity judgment and artifacts, Helen reviews sufficiency, the Steward's authority is preserved, Grace coordinates without approving, the manual fallback remains viable, and the full renewal lifecycle is auditable.

## Out of Scope

- Replacing Helen's institutional role with software.
- Giving Grace continuity-approval authority.
- Autonomous retirement of an implementation without successful onboarding evidence.
- Transcript migration as a continuity mechanism.
- General redesign of the Communication Bus or mailbox architecture.
- Claiming conversation-launch capability that is not implemented.

## Dependencies

- WP-0708 — Repair Reflection Execution Handoff Reference
- WP-0709 — Reflection and Continuity Process Adoption

## Related Item

- `operations/boards/parking_lot_items/PL-0030_AUTOMATED_REFLECTION_POINT_RENEWAL_PACKAGE_GENERATOR.md`
