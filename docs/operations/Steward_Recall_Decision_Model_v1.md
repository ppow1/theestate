# Steward Recall Decision Model v1

## Purpose

This decision model defines when Alfred should coordinate recall of the Steward instead of allowing autonomous Estate work to continue. It implements the Steward recall principle described in the Autonomous Estate Operations Charter v1 without expanding Alfred's authority.

This model is a governance and audit document. It does not implement notifications, create a final security clearance policy, bypass the Steward, or grant Alfred independent constitutional authority.

## Source Charter

The governing source is `docs/operations/Autonomous_Estate_Operations_Charter_v1.md`. That charter states that the Estate should continue autonomously until it encounters a decision that constitutionally belongs to the Steward, at which point Alfred should coordinate Steward recall through an approved transport adapter and preserve the audit trail.

## Recall Principle

Steward recall is required when the next blocked decision belongs to the Steward and cannot be resolved through existing work-package instructions, standing operating documents, approved policy, or prior Steward authorization.

The Estate should continue autonomous execution for independent work that remains procedural, delegated, validation-oriented, routing-oriented, observational, or report-generating. Recall stops or pauses only the affected decision path unless the same issue creates a broader Estate-wide risk.

## Alfred's Role

Alfred is the coordinator of recall assessment, not the sovereign authority over the Estate.

Alfred may:

- observe work-package, mailbox, completion, validation, report, and policy artifacts;
- classify an event against this approved recall model;
- request missing evidence from workers when the event is unclear;
- prepare a concise recall recommendation;
- issue a recall only when the event matches an approved recall reason and the required evidence is present;
- preserve audit fields for later Steward, Chief Architect, or CA review.

Alfred must not:

- make constitutional decisions for the Steward;
- invent new recall authority outside approved policy;
- approve merges, spending, publication, governance changes, or security clearance decisions;
- treat notification delivery as Steward approval;
- bypass the Steward when the decision belongs to the Steward.

## Worker Recall Requests

Workers may request Steward recall when they believe a work item has reached a Steward-only decision boundary.

A worker recall request should include:

- work package, mailbox, branch, report, or artifact path involved;
- proposed recall reason;
- the blocked decision;
- why existing instructions are insufficient;
- relevant evidence;
- urgency and consequence of waiting;
- whether unrelated work may safely continue.

A worker request is a recall candidate, not an automatic recall. Alfred must validate the request against this approved model before issuing recall.

## Approved Recall Reasons

Alfred may issue recall only for approved recall reasons. Version 1 supports these initial reasons.

### 1. Constitutional

Use when the blocked decision could alter Estate governance, Steward authority, role boundaries, approval powers, mission authority, or constitutional operating principles.

Examples include:

- changing who may approve or merge work;
- granting Alfred or another worker new authority;
- redefining Steward-only decisions;
- accepting a governance conflict that cannot be resolved from existing documents.

### 2. Architectural

Use when the blocked decision requires selecting or changing foundational architecture beyond delegated implementation details.

Examples include:

- choosing between incompatible platform directions;
- introducing a new durable subsystem without prior approval;
- changing canonical data, routing, or coordination models in a way that affects multiple future packages;
- resolving an architecture conflict not covered by an approved design.

### 3. Operational

Use when ordinary Estate operation is blocked by a decision that requires Steward prioritization, tradeoff acceptance, external commitment, or exception handling.

Examples include:

- choosing which critical work should pause or proceed when resources conflict;
- accepting a known operational risk not already authorized;
- deciding whether to continue after repeated validation or process failures;
- approving an exception to a documented operating procedure.

### 4. Security

Use when the blocked decision involves security, privacy, secrets, access, trust boundaries, data exposure, or incident response beyond approved routine handling.

Examples include:

- suspected credential exposure;
- proposed changes to security clearance or access policy;
- uncertainty about publishing sensitive information;
- deciding whether a security incident requires external or Steward-directed action.

This model does not create the final security clearance policy.

### 5. HR

Use when the blocked decision involves personnel, worker trust, conduct, role assignment, accountability, conflict, performance, or human-sensitive information that requires Steward judgment.

Examples include:

- assigning or removing a human-facing role;
- escalating conduct or trust concerns;
- resolving worker conflict that cannot be addressed procedurally;
- handling sensitive personal information or HR implications.

## Events That Shall Not Trigger Recall

The following events shall not trigger Steward recall by themselves:

- routine mail;
- completed work;
- normal validation;
- normal board updates;
- parking lot additions;
- successful Codex runs;
- informational status changes.

These events may be included in routine reports, board updates, completion artifacts, or morning briefings. They become recall candidates only if paired with an approved recall reason and evidence that the next decision belongs to the Steward.

## Required Evidence for Recall

Every recall must be supported by evidence sufficient for later review. Alfred should not issue recall on vague concern alone.

Required evidence:

1. **Triggering artifact** — path or identifier for the work package, mailbox item, validation result, report, policy entry, branch, or other artifact that caused the assessment.
2. **Blocked decision** — concise statement of the decision that cannot proceed autonomously.
3. **Recall reason** — one approved reason: constitutional, architectural, operational, security, or HR.
4. **Steward-only rationale** — explanation of why existing authority is insufficient and why the decision belongs to the Steward.
5. **Options or recommended next action** — known choices if available, clearly marked as recommendation rather than approval.
6. **Consequence of waiting** — impact of pausing the affected decision path.
7. **Continuity assessment** — whether unrelated work may continue safely while waiting for the Steward.
8. **Supporting references** — relevant paths, message ids, commit ids, validation logs, or reports.

## Recall Decision Flow

1. Detect a recall candidate from worker request, validation result, mailbox event, work-package state, report, or policy check.
2. Confirm the event is not solely a non-recall event.
3. Identify the blocked decision.
4. Match the blocked decision to exactly one primary approved recall reason; add secondary reasons only when necessary for audit clarity.
5. Verify required evidence is present.
6. If evidence is missing, request clarification or record the candidate as blocked pending evidence rather than issuing recall.
7. If evidence is sufficient and the policy reason applies, Alfred may issue a recall through an approved transport adapter when such an adapter exists.
8. Record the required audit fields regardless of whether recall was issued, deferred, or rejected.

## Audit Fields Required for Every Recall

Every issued recall record must include:

- recall_id;
- created_at;
- created_by;
- coordinator;
- recall_status;
- primary_recall_reason;
- secondary_recall_reasons, if any;
- triggering_artifact;
- related_work_package_id, if any;
- related_mailbox_path, if any;
- branch, if any;
- blocked_decision;
- steward_only_rationale;
- evidence_summary;
- supporting_references;
- options_or_recommended_next_action;
- consequence_of_waiting;
- continuity_assessment;
- non_recall_events_checked;
- policy_version;
- transport_adapter, if used;
- notification_attempt_id, if used;
- steward_response_required;
- steward_response_received_at, if applicable;
- final_resolution, if known;
- reviewer_notes, if any.

Candidate events that do not become recalls should still preserve enough notes to explain why recall was rejected or deferred when the event was significant.

## Version 1 Limitations

- This model does not implement notification transport.
- This model does not define the final security clearance policy.
- This model does not authorize Alfred to make constitutional decisions.
- This model does not allow Alfred or workers to bypass the Steward.
- This model is intended for CA verification before operational use.
