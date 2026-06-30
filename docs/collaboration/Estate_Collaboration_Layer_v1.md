
Estate Collaboration Layer v1

Status: Version 1 Infrastructure Plan
Priority: Immediate
Owner: Chief Architect
Operational Coordinator: Alfred / Chief of Staff
Boundary Authority: Privacy and Boundary Office
Initial Shared Transport: GitHub repository
Initial Local Transport: Local filesystem

1. Purpose

The Estate Collaboration Layer exists to make parallel Estate work possible without increasing the Steward's workload.

The immediate bottleneck is the manual loop:

ChatGPT to Pat to copy to terminal to copy back to ChatGPT.

That loop creates latency, transcription risk, duplicated effort, excessive cognitive load, and prevents the Estate from scaling to multiple AI workers.

The Collaboration Layer is infrastructure.

It is not another governance package.

It is not GitHub integration.

It is the operational capability that allows multiple intelligences to communicate, claim work, produce artifacts, request review, and promote approved results into institutional memory.

2. Architectural Freeze

The Version 1 architecture is frozen.

Do not continue refining the architecture unless operational use reveals a material issue.

The approved direction is:

Do not create a new Collaboration Office.
Do not create a new Transport Office.
Strengthen existing constitutional Offices.
Alfred / Chief of Staff owns operational coordination and routing.
Privacy and Boundary Office owns classification, promotion, outbound approval, and default-deny enforcement.
Discovery observes collaboration infrastructure.
Audit validates message structure, lifecycle state, promotion records, and repository health.
GitHub is the first transport adapter, not the Communication Bus itself.
Local filesystem is the first local transport adapter.
3. Core Principle

Architect once. Automate many times.

The Estate should invest in stable architecture that can be automated repeatedly across different implementations.

GitHub may be replaced.

The local filesystem may be replaced.

Future transports may include REST, MCP, RabbitMQ, IPC, databases, email, or custom services.

The Communication Bus concept remains stable.

4. Institutional Ownership
Alfred / Chief of Staff

Alfred owns operational communication responsibilities:

Work intake.
Work routing.
Claim state.
Work package lifecycle.
Worker coordination.
Status visibility.
Handoff flow.
Future automated routing.

Alfred does not own privacy permission.

Alfred does not override boundary authority.

Privacy and Boundary Office

The Privacy and Boundary Office owns:

Classification.
Promotion approval.
Outbound permission.
Boundary review.
Default-deny policy.
Promotion history.
Security event records.

This Office is permanent.

Its initial occupant may be a temporary implementation under Steward authority.

Its future occupant may be Ingrid.

No architecture should depend on Ingrid already being implemented.

Discovery

Discovery observes:

Collaboration folders.
Message queues.
Transport availability.
Local worker readiness.
GitHub readiness when integrated.
Backlog state.
Promotion queues.

Discovery does not route messages.

Audit

Audit validates:

Message envelope structure.
Required message fields.
Work package lifecycle state.
Promotion record shape.
Classification presence.
Repository cleanliness.
History continuity.

Audit does not decide whether content may leave the Estate.

Steward

The Steward is final authority.

The Steward should not be used as the routine router.

The Steward is involved for final approval, constitutional decisions, strategic direction, exceptions, unresolved preference, or high-trust boundary decisions.

5. Core Operational Flow
Work is created.
Work receives a message envelope.
Work enters an inbox.
A worker claims the work.
The worker executes within scope.
The worker reports completion.
Review occurs.
Privacy and Boundary Office classifies and approves or rejects promotion.
Approved material is promoted to shared institutional space.
GitHub or another transport receives only intentionally promoted material.
6. Participant Types

Participants may include:

Pat / Steward.
Alfred.
Chief Architect.
ChatGPT workers.
Local 4090 workers.
Documentation workers.
Discovery workers.
Audit workers.
Visual workers.
Estate residents.
Future local services.
Future APIs.
Future external integrations.
7. V1 Implementation

Version 1 uses simple durable materials:

Markdown for human-readable work packages.
JSON for canonical message envelopes.
Git for versioned collaboration state.
Local filesystem for local-only work.
GitHub as the first shared transport.
Manual promotion approval until automation is justified.
8. Repository Collaboration Surface

The repository now contains:

docs/collaboration
collaboration/messages
collaboration/work_packages
collaboration/promotions
collaboration/status
collaboration/templates

Runtime-only collaboration state lives under:

runtime/collaboration/local_only
runtime/collaboration/outbox
runtime/collaboration/dead_letter
9. Classification Model

All collaboration artifacts should carry one of these classifications:

Public
Estate Internal
Restricted
Steward Only
Local Only

Default classification is Local Only unless explicitly promoted.

10. Default-Deny Outbound Policy

Nothing leaves the Estate unless intentionally promoted.

The following default to Local Only:

Generated images.
Generated video.
Generated audio.
Prompts.
Prompt history.
Intermediate artifacts.
Generated summaries.
Metadata describing private artifacts.
Runtime state.
Local caches.
Personal data.
Confidential project material.
11. GitHub Role

GitHub is the first shared transport adapter.

GitHub provides:

Versioned communication.
Shared work packages.
Institutional documents.
Standards.
Architecture.
Review workflow.
Future issue and pull request integration.

GitHub does not own:

The Communication Bus.
Privacy classification.
Promotion authority.
Local-only artifacts.
Runtime state.
Prompts.
Generated media by default.
12. Local Filesystem Role

The local filesystem provides:

Local-only execution state.
Pre-promotion work areas.
Local worker handoff.
Safe staging before external sharing.
Local 4090 worker outputs.
Dead-letter handling.

The local filesystem is not a weaker transport.

It is the safest initial transport for private and pre-review material.

13. Work Package Lifecycle

Work package states:

open
claimed
in_progress
blocked
review
completed
rejected
archived

A work package should include:

Mission.
Scope.
Do-not-touch boundaries.
Required reading.
Local context script.
Deliverables.
Acceptance criteria.
Definition of done.
14. Promotion Lifecycle

Promotion states:

pending
approved
rejected

Promotion record fields should include:

promotion_id.
source_path.
target_path.
classification.
requested_by.
approved_by.
approved_at.
reason.
risks.
redactions.
audit_reference.
15. Alfred Future Automation

Alfred can later automate:

Inbox watching.
Message routing.
Work claiming.
Worker assignment.
Status aggregation.
Promotion record preparation.
Review routing.
GitHub sync preparation.

Automation should occur after operational flow is stable.

16. V1 Success Criteria

Version 1 succeeds when:

A ChatGPT worker can receive a bounded work package from the repository.
A local 4090 worker can use the same communication protocol.
Work can be claimed.
Work can be completed.
Review state is visible.
Promotion decisions are explicit.
GitHub receives only approved institutional material.
Alfred can later replace manual routing without redesigning the institution.
