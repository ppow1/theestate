
Communication Bus v1 Operational Flow

Status: Operational Design
Owner: Alfred / Chief of Staff
Boundary Authority: Privacy and Boundary Office

1. Purpose

The Communication Bus is the structured flow of work, messages, routing, acknowledgement, and state between Estate participants.

It is not GitHub.

It is not a new Office.

It is an institutional capability implemented through existing Offices and replaceable transports.

2. Responsibilities

The Communication Bus supports:

Message intake.
Routing.
Addressing.
Work package lifecycle.
Acknowledgement.
Status reporting.
Escalation.
Review routing.
Promotion request routing.
Completion reporting.
3. Non-Responsibilities

The Communication Bus does not own:

Privacy permission.
Classification authority.
Public release approval.
Final Steward decisions.
The GitHub implementation.
Local runtime content.
Media artifacts by default.
4. Lifecycle
Intake

A message enters through one of these paths:

Pat creates a work package.
Chief Architect creates a worker assignment.
Alfred creates a task.
A ChatGPT worker returns output.
A local worker reports status.
Discovery reports state.
Audit reports failure.
A worker requests review.
A worker requests promotion.
Envelope

Every message receives a canonical envelope.

The payload may differ, but the envelope remains stable.

Routing

Alfred determines operational destination.

The Privacy and Boundary Office determines whether content may cross a boundary.

Routing and permission are separate decisions.

Claim

A worker claims work by creating or updating claim metadata.

In v1 this may be represented by moving or copying files between collaboration folders.

Execution

The worker performs the assignment within scope.

Outputs remain local unless explicitly promoted.

Completion

The worker submits:

Summary.
Files changed.
Artifacts created.
Commands run.
Audit state.
Unresolved risks.
Promotion recommendation.
Review

Review may involve:

Chief Architect.
Alfred.
Audit.
Privacy and Boundary Office.
Steward when required.
Promotion

Promotion moves approved information from local or working state into shared institutional state.

Archive

Closed messages and completed work packages are archived.

5. State Directories

Message lifecycle:

collaboration/messages/inbox
collaboration/messages/claimed
collaboration/messages/in_progress
collaboration/messages/review
collaboration/messages/completed
collaboration/messages/archive

Work package lifecycle:

collaboration/work_packages/open
collaboration/work_packages/claimed
collaboration/work_packages/completed

Promotion lifecycle:

collaboration/promotions/pending
collaboration/promotions/approved
collaboration/promotions/rejected

Local-only state:

runtime/collaboration/local_only
runtime/collaboration/outbox
runtime/collaboration/dead_letter
6. Operational Rule

If a message may leave local-only state, it must pass through the Privacy and Boundary Office.

The Communication Bus must never publish directly to an external transport.
