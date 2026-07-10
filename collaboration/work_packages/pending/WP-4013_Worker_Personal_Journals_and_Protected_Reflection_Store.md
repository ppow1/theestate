# WP-4013 — Worker Personal Journals and Protected Reflection Store

Status: Pending
Owner: Resident Runtime Implementation Stream
Execution Target: Codex
Depends On: WP-4004, WP-4007
Classification: Estate Internal

## Objective

Implement protected local personal journals for workers and residents as private working memory and reflection aids, without converting them into institutional truth or unrestricted operational telemetry.

## Required Implementation

- Create versioned journal-entry and journal-summary schemas.
- Store journals under deterministic per-employee or per-resident paths linked to existing personnel identity.
- Support entry creation, listing, reading, redaction, archival, and bounded export.
- Separate raw journal entries from approved summaries and continuity artifacts.
- Enforce classification, reader, writer, and export restrictions using Ingrid boundary rules.
- Allow Helen to request or receive only governed summaries or explicitly authorized evidence.
- Support worker-authored "cheat sheet" and reflection notes without automatically publishing them.
- Add audit records for reads, writes, redactions, exports, and summary approvals.
- Add CLI commands and reusable APIs.
- Integrate only privacy-safe status into existing Office surfaces.

## Deliverables

- protected journal store and schemas;
- CLI integration;
- audit integration;
- tests for authorization, redaction, export restrictions, summary promotion, and public-surface leakage;
- `operations/validation/reports/WP-4013_worker_personal_journals.md`;
- `collaboration/work_packages/completions/WP-4013_codex_done.json`.

## Boundaries

Do not make journals institutional truth. Do not expose journal bodies on task boards, search, status, or routine workforce telemetry. Do not grant Helen or Grace unrestricted journal access. Do not create cloud storage.

## Acceptance Criteria

- journal ownership and access are deterministic;
- raw entries remain private by default;
- approved summaries are distinct artifacts;
- redaction and audit behavior work;
- public and operational surfaces cannot leak protected content;
- all focused tests pass.

## Codex Handoff

```text
Read collaboration/work_packages/pending/WP-4013_Worker_Personal_Journals_and_Protected_Reflection_Store.md and do exactly what it says.
```
