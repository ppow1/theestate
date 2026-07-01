# Estate Audit Worker v1

Status: Version 1 Implementation Plan
Owner: Audit
Operational Coordinator: Alfred / Chief of Staff
Transport: GitHub collaboration audit queue
Authority: Local Estate machine at A:\theestate
Classification: Estate Internal

## Purpose

The Estate Audit Worker v1 removes Pat from the audit transport loop.

GitHub workers can request local validation by creating audit request files. The local Estate machine remains the audit authority and publishes non-private result state back through GitHub.

GitHub carries intent and results.

The local Estate audit remains authoritative.

## Required Flow

Worker / ChatGPT / Chief Architect

-> GitHub audit request queue

-> Local Audit Worker on A:\theestate

-> .\estate.bat audit

-> Audit result written to collaboration/audit/results

-> All workers can read verified result

## Directories

- collaboration/audit/pending
- collaboration/audit/active
- collaboration/audit/results
- collaboration/audit/archive
- collaboration/audit/failed

Worker files:

- workers/audit/README.md
- workers/audit/run_audit_worker_once.ps1
- workers/audit/audit_request_schema.md
- workers/audit/audit_result_schema.md

## Minimum v1 Behavior

The one-shot worker should:

1. Pull latest repo state.
2. Detect pending audit request files.
3. Move one request to active.
4. Run .\estate.bat audit locally.
5. Capture stdout, stderr, exit code, timestamp, branch, and commit SHA.
6. Write a result file to collaboration/audit/results.
7. Move completed request to archive or failed.
8. Commit and push the result back to GitHub.
9. Avoid modifying estate_ledger/ledger.md and development/devlog.md except through the approved history queue/drain workflow.

## Constraints

- Start with a manual one-shot script, not a daemon.
- Do not build a complex service yet.
- Do not run audits constantly.
- Do not make GitHub authoritative.
- Do not require Pat to copy/paste audit output.
- Do not bypass Privacy and Boundary rules.
- Do not publish private local artifact details.
- Do not let routine workers directly edit ledger/devlog.

## Trigger

A worker creates an audit request in collaboration/audit/pending.

Pat or a local authorized operator runs:

    .\workers\audit\run_audit_worker_once.ps1

Later this may become a scheduled task or watcher.

## Success Criteria

- A GitHub worker can request an audit without asking Pat to paste terminal output.
- The local machine can run the audit and return results through GitHub.
- Other workers can read the result from the repository.
- The result distinguishes pass, fail, and execution error.
- History drift is reported but repaired only through the history queue/drain system.
- Pat's manual role is reduced to running or approving the local worker, not transporting output.

## Reusable Pattern

This is the first local execution adapter of the Collaboration Layer.

It proves:

- GitHub carries intent.
- Local Estate performs local-only authority work.
- GitHub carries non-private result state back to the institution.

Future local workers may use the same pattern for Discovery refresh, model inventory, local 4090 task runners, and Alfred-controlled execution.
