
Canonical Message Envelope v1

Status: Message Contract

1. Purpose

Every Collaboration Layer message should use a shared envelope.

Payloads may differ.

The envelope remains stable.

2. Required Fields

Required fields:

id
version
created_at
created_by
source
destination
classification
message_type
priority
status
requires_ack
payload
3. Optional Fields

Optional fields:

thread_id
related_work_package
related_commit
related_artifact
audit_ref
promotion_ref
expires_at
blocked_by
reviewed_by
4. Message Types

Allowed v1 message types:

work_package
directive
request
response
status
notification
event
escalation
approval
audit_record
promotion_request
promotion_decision
5. Status Values

Allowed v1 status values:

draft
open
claimed
in_progress
blocked
review
approved
rejected
completed
archived
6. Priority Values

Allowed v1 priority values:

low
normal
high
immediate
steward_attention
7. Classifications

Allowed v1 classifications:

Public
Estate Internal
Restricted
Steward Only
Local Only
8. Example JSON Shape

Indented example:

{
  "id": "msg_YYYYMMDD_HHMMSS_slug",
  "version": 1,
  "created_at": "YYYY-MM-DDTHH:MM:SS",
  "created_by": "Pat",
  "source": "Steward",
  "destination": "Alfred",
  "classification": "Estate Internal",
  "message_type": "work_package",
  "priority": "normal",
  "status": "open",
  "requires_ack": true,
  "payload": {}
}

