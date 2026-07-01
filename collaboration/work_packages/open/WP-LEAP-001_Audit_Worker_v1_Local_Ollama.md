# Work Package WP-LEAP-001

Title: Implement Estate Audit Worker v1 Local Execution Adapter
Status: Open
Priority: High
Classification: Estate Internal
Assigned To: Local Ollama Worker
Created By: Chief Architect #2
Date: 2026-06-30
Branch: audit/audit-worker-v1

## Mission

Implement the Estate Audit Worker v1 as the first Local Execution Adapter Protocol implementation.

This worker should complete the repository files needed for a manual one-shot local audit adapter that processes GitHub audit requests, runs the authoritative local Estate audit, and publishes non-private results back through GitHub.

GitHub is the transport. The local Estate audit remains authoritative.

## Required Reading

1. AI_HINTS.md
2. AI_START_HERE.md
3. docs/governance/Estate_Orientation_Handbook.md
4. docs/governance/Estate_Manual.md
5. docs/collaboration/Estate_Collaboration_Layer_v1.md
6. docs/collaboration/Worker_Collaboration_Protocol_v1.md
7. docs/collaboration/Local_Execution_Adapter_Protocol_v1.md
8. workers/audit/README.md
9. workers/audit/audit_request_schema.md

## Existing Branch State

The following files and directories have already been started on branch audit/audit-worker-v1:

- docs/collaboration/Local_Execution_Adapter_Protocol_v1.md
- workers/audit/README.md
- workers/audit/audit_request_schema.md
- collaboration/audit/pending/.gitkeep
- collaboration/audit/active/.gitkeep
- collaboration/audit/results/.gitkeep
- collaboration/audit/archive/.gitkeep
- collaboration/audit/failed/.gitkeep

## Required Deliverables

Create or complete:

1. workers/audit/run_audit_worker_once.ps1
2. workers/audit/audit_result_schema.md
3. collaboration/audit/pending/sample_audit_request.json
4. collaboration/audit/results/sample_audit_result.json
5. Any minimal README or usage note needed so Pat can run the worker.

## Required Behavior for run_audit_worker_once.ps1

The script must:

1. Begin with Clear-Host.
2. Operate from A:\theestate.
3. Pull latest repo state.
4. Detect pending JSON request files under collaboration/audit/pending.
5. If no pending requests exist, print a clear message and exit successfully.
6. Select one pending request.
7. Move it to collaboration/audit/active.
8. Capture request_id, requested_by, work_package_id, target_commit, reason, classification, expected_checks, and promotion_context when available.
9. Run .\estate.bat audit locally.
10. Capture stdout, stderr, exit code, start timestamp, finish timestamp, current branch, and current commit SHA.
11. Determine status as pass, fail, or error.
12. Detect whether audit output mentions history drift or latest git/ledger mismatch.
13. Write a JSON result file to collaboration/audit/results.
14. Move the active request to collaboration/audit/archive if audit execution completed, or collaboration/audit/failed if the worker itself errored.
15. Commit and push result files back to GitHub.
16. Never modify estate_ledger/ledger.md or development/devlog.md.

## Constraints

- Manual one-shot script only. Do not build a daemon.
- Do not run constantly.
- Do not make GitHub authoritative.
- Do not publish private Local Only artifact details.
- Do not bypass Privacy and Boundary rules.
- Do not directly edit canonical history files.
- Keep implementation simple and reliable.

## PowerShell Style Requirements

- Full executable script.
- Clear-Host at the top.
- Use plain ASCII.
- Avoid nested markdown fences.
- Include clear operator output.
- Fail loudly on true execution errors.

## Audit Request Schema

A request includes:

- request_id
- requested_by
- work_package_id
- target_commit
- reason
- requested_at
- classification
- expected_checks
- promotion_context

## Audit Result Schema

A result includes:

- request_id
- status: pass / fail / error
- local_commit
- branch
- audit_started_at
- audit_finished_at
- command_run
- exit_code
- summary
- full_audit_output
- stderr
- follow_up_required
- history_drift_detected
- classification

## Acceptance Criteria

1. A worker can create an audit request in collaboration/audit/pending.
2. Pat or a local operator can run workers/audit/run_audit_worker_once.ps1.
3. The local machine runs .\estate.bat audit.
4. The result is written to collaboration/audit/results.
5. The request is archived or failed.
6. The result is committed and pushed back to GitHub.
7. Canonical ledger/devlog are not edited.
8. Audit drift is reported but not repaired by this worker.

## Completion Report

When complete, write a status report to:

collaboration/status/WP-LEAP-001_status.md

Include:

- summary
- files changed
- commands run
- audit status
- known limitations
- next recommended step
