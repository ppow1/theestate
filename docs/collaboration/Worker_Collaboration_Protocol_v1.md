
Worker Collaboration Protocol v1

Status: Operational Protocol
Owner: Alfred / Chief of Staff
Review Authority: Chief Architect
Boundary Authority: Privacy and Boundary Office

1. Purpose

This protocol explains how ChatGPT workers, local 4090 workers, Alfred, and future services participate in Estate work.

2. Worker Intake

A worker begins by reading:

AI_HINTS.md
AI_START_HERE.md
docs/governance/Estate_Orientation_Handbook.md
Assigned work package
Related message envelope
Required reading listed in the work package
3. Claiming Work

A worker claims work by creating or updating claim metadata.

Minimum claim fields:

worker_id
worker_type
claimed_at
work_package_id
message_id
expected_output
current_status
4. Worker Types

Allowed v1 worker types:

chatgpt_worker
chief_architect
alfred
local_4090_worker
documentation_worker
audit_worker
discovery_worker
visual_worker
governance_worker
5. Work States

Allowed v1 work states:

open
claimed
in_progress
blocked
review
completed
rejected
archived
6. Completion Report

A completion report must include:

Summary.
Files changed.
Artifacts created.
Commands run.
Audit status.
Unresolved risks.
Promotion recommendation.
Follow-up work.
7. Review

Review asks:

Did the worker stay in scope?
Did the worker touch forbidden files?
Are outputs complete?
Are artifacts available?
Is audit clean?
Is classification correct?
Should anything be promoted?
Is Pat required?
8. ChatGPT Workers

ChatGPT workers may still receive copied work packages today.

The Collaboration Layer exists to reduce that manual loop over time.

ChatGPT workers should return complete outputs and avoid fragmenting work.

9. Local 4090 Workers

Local workers use the same message envelope.

Local worker outputs should remain under runtime/collaboration/local_only until promotion is approved.

10. Alfred Future Role

Alfred will eventually:

Watch inboxes.
Route work.
Assign workers.
Track claims.
Request review.
Prepare promotion records.
Report status to Pat.

V1 keeps enough manual control to learn the operational flow before automating.
