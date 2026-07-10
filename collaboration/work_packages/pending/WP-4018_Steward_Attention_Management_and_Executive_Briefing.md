# WP-4018 — Steward Attention Management and Executive Briefing

Status: Pending
Owner: Resident Runtime Implementation Stream
Execution Target: Codex
Depends On: WP-4016, WP-4017
Classification: Estate Internal

## Objective

Extend Alfred's Chief of Staff function into a practical local attention-management system that batches routine information, prioritizes exceptions, and produces decision-ready briefings for the Steward.

## Required Implementation

- Aggregate signals from resident task status, mail, validation, operations, workforce, services, projects, and work packages.
- Classify items as routine, watch, attention soon, decision required, urgent, or informational.
- Preserve source links, timestamps, classification, owner, requested Steward action, and deadline.
- Deduplicate repeated signals and collapse related updates into one attention item.
- Produce morning, on-demand, and exception briefings.
- Add snooze, acknowledge, delegate, dismiss, and resolve actions using existing Office action transport.
- Separate "Steward should know" from "Steward must decide."
- Keep Alfred as attention gate and briefing owner without making Alfred the underlying event bus, task queue, or authority source.
- Add CLI and Office UI integration.
- Add deterministic tests for prioritization, deduplication, batching, stale items, and action persistence.

## Deliverables

- attention aggregation and briefing service;
- versioned attention-item and briefing schemas;
- Alfred and Office integration;
- tests and local demonstration;
- `operations/validation/reports/WP-4018_steward_attention_management.md`;
- `collaboration/work_packages/completions/WP-4018_codex_done.json`.

## Boundaries

Do not create a second notification router, task queue, event runtime, or authority system. Do not expose private workforce records in executive briefings. Do not auto-approve decisions.

## Acceptance Criteria

- routine noise is batched;
- genuine exceptions are visible and decision-ready;
- duplicate signals collapse safely;
- every item remains source-linked;
- Steward actions persist and refresh correctly;
- all focused tests pass.

## Codex Handoff

```text
Read collaboration/work_packages/pending/WP-4018_Steward_Attention_Management_and_Executive_Briefing.md and do exactly what it says.
```
