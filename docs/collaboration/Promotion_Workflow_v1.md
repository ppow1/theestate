
Promotion Workflow v1

Status: Boundary Process
Owner: Privacy and Boundary Office
Initial Implementation: Manual review under Steward authority
Future Occupant: Ingrid

1. Purpose

Promotion is the process of moving information from local execution into shared institutional repositories or external transports.

Promotion is never automatic by default.

2. Authority

The Privacy and Boundary Office owns promotion authority.

Initial implementations may include:

Manual Steward approval.
Chief Architect review.
Repository policies.
Collaboration standards.
Promotion records.
Local validation scripts.

Future implementations may include:

Ingrid.
Automated policy engines.
Classification engines.
Data loss prevention systems.
Security services.
AI policy enforcement.
3. Default Policy

Default deny.

Nothing leaves local/private execution unless intentionally promoted.

4. Classifications
Public

Approved for public sharing.

Estate Internal

Approved for institutional repository sharing.

Restricted

Approved only for limited Estate participants.

Steward Only

Only Pat may access or approve.

Local Only

Must remain local and must not be pushed to GitHub or external transports.

5. Local Only Defaults

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
6. Promotion Record

Every promotion should record:

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
7. Workflow
Worker produces output.
Output remains local.
Worker recommends promotion if appropriate.
Privacy and Boundary Office reviews classification.
Approval or rejection is recorded.
Approved content is moved to shared repository path.
Git commit records promoted institutional material.
Audit validates where possible.
8. GitHub Rule

GitHub receives only intentionally promoted institutional information.

GitHub must not receive private runtime artifacts by accident.

9. Future Automation

Automation may later help classify, redact, approve, reject, route, or audit promotion.

Automation must not remove the constitutional authority of the Privacy and Boundary Office.
