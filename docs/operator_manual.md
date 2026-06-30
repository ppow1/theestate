# Estate Operator Manual

## Purpose

The Estate is a local institutional AI operating system. Its purpose is to let Alfred understand the local AI environment, route work to available services, execute safe jobs, preserve runtime artifacts, and give the Steward a reliable operating surface.

## Layers

1. Inventory / Discovery — what exists locally.
2. Audit / Integrity — whether the Estate is healthy and internally consistent.
3. Services — what capabilities are available.
4. Alfred — planning, jobs, execution, artifacts, requests, and briefings.

## Core Commands

- `estate audit`
- `estate audit --save`
- `estate audit-summary`
- `estate discover`
- `estate discovery-refresh`
- `estate service-status`
- `estate service-route <capability>`
- `estate alfred-capabilities`
- `estate alfred-plan "<goal>"`
- `estate alfred-run "<goal>"`
- `estate alfred-execute <job_id>`
- `estate alfred-result <job_id>`
- `estate alfred-inspect <job_id>`
- `estate alfred-jobs`
- `estate alfred-policy`
- `estate alfred-status`
- `estate alfred-task "<goal>"`
- `estate alfred-request "<goal>"`
- `estate alfred-requests`
- `estate alfred-promote <request_id>`
- `estate alfred-briefing`

## Standard Operating Flow

1. Run `estate audit`.
2. Run `estate service-status`.
3. Use `estate alfred-capabilities` to see what Alfred can route.
4. Use `estate alfred-plan "<goal>"` before execution.
5. Use `estate alfred-task "<goal>"` for safe end-to-end work.
6. Inspect artifacts under `runtime/alfred/jobs`.

## Runtime Artifacts

Runtime artifacts are mutable operational state and should not be committed.

Important runtime locations:

- `runtime/audit`
- `runtime/discovery`
- `runtime/services`
- `runtime/alfred/jobs`
- `runtime/alfred/requests`

## Do Not Edit Manually

Avoid manual edits to:

- runtime job JSON files while Alfred is running
- ledger/devlog EC records except through explicit Estate Changes
- registry JSON unless the change is intentional and audited

## Power Interruption Recovery

After interruption:

1. Open PowerShell.
2. Run `cls`.
3. `cd A:\theestate`
4. Run `git status`.
5. Run `estate audit`.
6. If Git is dirty, inspect before committing or deleting anything.

## Steward Principles

- The Steward is sovereign.
- The Estate must not pretend to know what it has not observed or been told.
- Repairs are historical facts.
- Do not rewrite history to hide defects.
- Prefer subsystem milestones over small isolated tweaks.
