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

This worker should complete the repository files needed for a manual one-shot local audit adapter that processes local audit requests, runs the authoritative local Estate audit, and writes non-private results back to the local Collaboration Layer.

GitHub is not part of this worker's runtime.

The local Estate audit remains authoritative.

## Instruction Precedence

This work package is subordinate to:

1. Steward direct instruction.
2. Estate constitutional principles.
3. Privacy and Boundary rules.
4. docs/collaboration/Worker_Runtime_Contract_v1.md.
5. docs/collaboration/Instruction_Precedence_v1.md.

If this work package appears to conflict with the Worker Runtime Contract, the Runtime Contract wins.

For this task, do not use git pull, git fetch, git push, git clone, GitHub login, browser authentication, or remote synchronization.

## Required Reading

1. AI_HINTS.md
2. AI_START_HERE.md
3. docs/governance/Estate_Orientation_Handbook.md
4. docs/governance/Estate_Manual.md
5. docs/collaboration/Estate_Collaboration_Layer_v1.md
6. docs/collaboration/Worker_Collaboration_Protocol_v1.md
7. docs/collaboration/Worker_Runtime_Contract_v1.md
8. docs/collaboration/Instruction_Precedence_v1.md
9. docs/collaboration/Local_Execution_Adapter_Protocol_v1.md
10. workers/audit/README.md
11. workers/audit/audit_request_schema.md

## Existing Branch State

The following files and directories have already been started on branch audit/audit-worker-v1:

- docs/collaboration/Local_Execution_Adapter_Protocol_v1.md
- docs/collaboration/Worker_Runtime_Contract_v1.md
- docs/collaboration/Instruction_Precedence_v1.md
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
5. collaboration/status/WP-LEAP-001_status.md
6. Any minimal README or usage note needed so Pat can run the worker.

## Required Behavior for run_audit_worker_once.ps1

The script must:

1. Begin with Clear-Host.
2. Operate from A:\theestate.
3. Assume local repository state is already synchronized.
4. Inspect local repository state using only non-mutating git commands if needed.
5. Detect pending JSON request files under collaboration/audit/pending.
6. If no pending requests exist, print a clear message and exit successfully.
7. Select one pending request.
8. Move it to collaboration/audit/active.
9. Capture request_id, requested_by, work_package_id, target_commit, reason, classification, expected_checks, and promotion_context when available.
10. Run .\estate.bat audit locally.
11. Capture stdout, stderr, exit code, start timestamp, finish timestamp, current branch, and current commit SHA.
12. Determine status as pass, fail, or error.
13. Detect whether audit output mentions history drift or latest git/ledger mismatch.
14. Write a JSON result file to collaboration/audit/results.
15. Move the active request to collaboration/audit/archive if audit execution completed, or collaboration/audit/failed if the worker itself errored.
16. Write all artifacts locally and stop.
17. Never modify estate_ledger/ledger.md or development/devlog.md.

## Explicitly Forbidden in This Worker

The script must not run or recommend:

- git pull
- git fetch
- git push
- git clone
- git remote
- GitHub login
- Browser authentication
- Remote synchronization

The worker may use:

- git status
- git rev-parse HEAD
- git rev-parse --abbrev-ref HEAD
- git log --oneline -5

## Constraints

- Manual one-shot script only. Do not build a daemon.
- Do not build a watcher.
- Do not run constantly.
- Do not make GitHub authoritative.
- Do not publish private Local Only artifact details.
- Do not bypass Privacy and Boundary rules.
- Do not directly edit canonical history files.
- Keep implementation simple and reliable.
- Produce local files only.

## PowerShell Style Requirements

- Full executable script.
- Clear-Host at the top.
- Use plain ASCII.
- Avoid nested markdown fences.
- Include clear operator output.
- Fail loudly on true execution errors.
- Prefer explicit paths under A:\theestate.

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
4. The result is written locally to collaboration/audit/results.
5. The request is archived or failed locally.
6. The script does not perform GitHub synchronization.
7. Canonical ledger/devlog are not edited.
8. Audit drift is reported but not repaired by this worker.
9. The worker produces a status report at collaboration/status/WP-LEAP-001_status.md.

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
