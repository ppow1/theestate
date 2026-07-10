# WP-4014 — Historian Office Runtime and Institutional Timeline

Status: Pending
Owner: Resident Runtime Implementation Stream
Execution Target: Codex
Depends On: WP-4012
Classification: Estate Internal

## Objective

Implement the Historian Office as a local institutional-history service that records inflection points, decision history, doctrine evolution, constitutional changes, major operational transitions, and cited historical summaries.

## Required Implementation

- Create versioned historical-event, source-citation, timeline, and historical-summary schemas.
- Link every historical claim to repository artifacts, receipts, decisions, or preserved records.
- Build a deterministic local timeline index with filtering by date, office, project, resident, artifact type, and significance.
- Add CLI commands for event creation, timeline generation, source inspection, and historical query.
- Integrate with the Estate knowledge index rather than duplicating search infrastructure.
- Support generated summaries that clearly distinguish source fact, interpretation, and unresolved uncertainty.
- Provide Office read-only timeline and historical context surfaces.
- Add tests for chronology, citation integrity, duplicate-event handling, correction, and source disappearance.

## Deliverables

- Historian runtime module and local store;
- schemas and examples;
- CLI and existing Office integration;
- initial timeline generated from existing accepted Estate artifacts;
- `operations/validation/reports/WP-4014_historian_office_runtime.md`;
- `collaboration/work_packages/completions/WP-4014_codex_done.json`.

## Boundaries

Do not rewrite institutional history, infer acceptance from implementation, create facts without sources, or replace constitutional records. Do not create a second search index.

## Acceptance Criteria

- timeline entries are source-linked and auditable;
- corrections preserve prior history;
- summaries distinguish fact from interpretation;
- existing knowledge retrieval is reused;
- all focused tests pass.

## Codex Handoff

```text
Read collaboration/work_packages/pending/WP-4014_Historian_Office_Runtime_and_Institutional_Timeline.md and do exactly what it says.
```
