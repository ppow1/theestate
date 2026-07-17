# WP-0693 — Operational Blocker and Escalation Classifier

Status: Pending  
Priority: High  
Owner: Chief Architect  
Execution lane: Codex  
Primary campaign: CAMPAIGN-0681 — Estate Operationalization  
Depends on: WP-0690, WP-0691, WP-0692  
Integration gate: G2 — Observation Truth

## Objective

Implement a repository-grounded classifier that converts observed campaign, work-package, resident, service, readiness, validation, staffing, evidence, communication, and authority conditions into explicit blocker and escalation classes without inventing authority, bypassing canonical lanes, or treating uncertainty as permission to proceed.

## Required behavior

The classifier shall distinguish at minimum:

- dependency blocker;
- readiness blocker;
- resident-health blocker;
- service-health blocker;
- staffing or capability blocker;
- provider or environment blocker;
- evidence or validation blocker;
- communication or acknowledgement blocker;
- architectural blocker;
- acceptance blocker;
- protected Steward decision;
- transient operational failure;
- recoverable execution failure;
- contradictory-state blocker;
- stale-evidence blocker;
- unknown-authority blocker.

For every classification, produce:

- affected campaign or work package;
- observed facts and canonical evidence references;
- blocker class and severity;
- whether work may continue in unaffected lanes;
- responsible office or authority lane;
- recommended next action;
- escalation destination;
- acknowledgement requirement;
- reevaluation trigger;
- fail-closed reason when classification is uncertain.

## Authority rules

- Classification is observation and recommendation, not authority.
- The classifier shall not assign staff, dispatch work, approve architecture, accept deliverables, merge, deploy, close, or waive a gate.
- Protected decisions must stop progression in the affected lane and identify the correct decision authority.
- Ambiguous or conflicting authority must classify as blocked and fail closed.
- Grace may receive operational coordination output but does not inherit the authority of the destination office.
- Helen, Alfred, Engineering, Chief Architect, and Steward remain within their accepted lanes.

## Canonical reuse requirements

Discover and reuse the canonical blocker, escalation, readiness, validation, health, mailbox, repository-message, PTM, Dispatch, campaign, work-package, and office-authority mechanisms. Do not create a parallel blocker registry or escalation queue where an accepted mechanism exists.

## Deliverables

1. blocker and escalation classification schema;
2. deterministic classification rules;
3. evidence-reference requirements;
4. escalation routing contract;
5. reevaluation and declassification rules;
6. tests for every blocker class;
7. tests proving ambiguous authority fails closed;
8. tests proving unaffected work can continue only when canonical dependency and collision rules allow it;
9. completion receipt and G2 evidence contribution.

## Acceptance criteria

WP-0693 is complete when observed conditions from WP-0691 and WP-0692 can be classified deterministically, routed to the correct office or protected authority, explained with evidence, reevaluated after state changes, and prevented from silently becoming execution permission.

## Non-goals

- no new office or department;
- no autonomous remediation loop;
- no automatic acceptance, merge, deployment, or closure;
- no replacement of canonical messages, mailboxes, PTM, Dispatch, readiness, validation, or authority systems;
- no mutation of authoritative campaign state merely because a blocker was classified.
## Executable Validation Commands

Run the following commands from the repository root after implementation and
after creating this package's completion receipt:

    pwsh -NoProfile -File scripts/validation/Validate-Campaign0681Package.ps1 -PackageId WP-0693
    git diff --check

Run all additional affected-subsystem tests discovered during implementation.
Record every exact command, result, environment, unresolved gap, and failure
disposition in the package completion receipt.

A prose expected outcome is not a substitute for executing the commands above.
