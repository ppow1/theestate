# WP-4031 — Resident Runtime Install Handoff and Operational Acceptance

Status: Pending
Workstream Mode: INSTALL-HANDOFF
Owner: Resident Runtime Implementation Stream
Execution Target: Codex
Depends On: WP-4022, WP-4023, WP-4024, WP-4025, WP-4026, WP-4027, WP-4028, WP-4029, WP-4030
Classification: Estate Internal

## Objective

Review, order, install, and validate the staged resident-runtime workstreams WP-4022 through WP-4030, then run a full multi-resident operational exercise.

Staged work is not installed work. This package is the only authorized installer for the shared active-file integrations in this group.

## Required Pre-Install Review

For every workstream:

1. inspect `collaboration/workstreams/WP-XXXX/install_manifest.json`;
2. verify all staged paths exist;
3. verify `staged_work_is_installed` is `false`;
4. run staged tests;
5. identify missing dependencies;
6. inspect intended final install paths;
7. build a cross-package conflict matrix;
8. classify each package as ready, ready with conditions, or blocked;
9. leave blocked work staged.

## Required Conflict Matrix

At minimum analyze collisions involving:

- `src/estate/core/resident_interaction.py`;
- `src/estate/core/resident_authority.py`;
- model-control modules;
- AI-service control modules;
- assignment, Dispatch, and Traffic Controller modules;
- mailbox and conversation modules;
- `src/estate/cli/main.py`;
- Office resident, model, service, task, and attachment surfaces;
- shared tests and validation registration.

## Required Install Sequence

Determine the final order from actual manifests and current repository state. The expected dependency order is:

```text
WP-4022 capability resolution
WP-4024 context assembly
WP-4025 session recovery
WP-4026 model assignment and failover
WP-4023 delegation and handoffs
WP-4027 performance evaluation
WP-4028 service supervision
WP-4029 attachment exchange
WP-4030 backup and recovery
```

Change this order only when evidence requires it, and record the reason.

## Installation Requirements

- Install isolated modules first.
- Consolidate shared-file changes once instead of applying competing patches sequentially.
- Preserve current main-branch behavior and compatibility.
- Register CLI commands in one controlled edit.
- Register Office UI/status integrations in one controlled edit per shared surface.
- Merge overlapping schemas, diagnostics, and status payloads into one canonical implementation.
- Run validation after each install phase.
- Record exact files changed and rollback points.
- Do not install a package whose manifest is incomplete or whose staged tests fail.

## Multi-Resident Operational Exercise

After installation, demonstrate:

1. the Steward issues an approved objective;
2. Alfred filters and routes Steward attention;
3. Grace forms a lawful operational sequence;
4. Helen evaluates staffing or readiness constraints;
5. resident-specific capabilities and model assignments resolve;
6. context assembly supplies source-linked bounded context;
7. a governed delegation is issued and acknowledged;
8. residents exchange messages and attachments;
9. a local AI service failure is detected and reported truthfully;
10. session recovery survives a simulated restart;
11. performance evidence is recorded without automatic personnel action;
12. backup and selective restore are demonstrated in an isolated root;
13. Grace coordinates operational closure;
14. Alfred produces a concise final executive briefing.

Use fake providers, fake service runners, and isolated roots where live execution is not appropriate.

## Required Outputs

- `collaboration/workstreams/WP-4031/conflict_matrix.json`
- `collaboration/workstreams/WP-4031/install_order.json`
- `collaboration/workstreams/WP-4031/install_report.md`
- `runtime/residents/multi_resident_operational_exercise.json`
- `operations/residents/Multi_Resident_Operational_Exercise.md`
- `operations/validation/reports/WP-4031_resident_runtime_install_and_acceptance.md`
- `collaboration/work_packages/completions/WP-4031_codex_done.json`

## Validation

Run:

- each staged workstream's validation commands;
- post-install focused tests for every installed package;
- resident interaction and gateway tests;
- Helen, Grace, Alfred, mailbox, model-control, AI-service, task, attachment, and continuity regressions;
- workstream inspect and validate commands;
- full suite if practical.

Record unrelated pre-existing failures precisely.

## Boundaries

Do not install blocked work. Do not erase staged artifacts after installation. Do not grant institutional acceptance automatically. Do not create parallel active implementations to avoid resolving conflicts. Do not activate unauthorized residents or execute cloud providers.

## Acceptance Criteria

- all nine manifests are inspected;
- a conflict matrix and evidence-based install order exist;
- ready staged work is installed through consolidated shared-file edits;
- blocked work remains staged and explicit;
- post-install tests pass for installed work;
- the operational exercise completes or produces a narrow truthful defect list;
- rollback information is complete;
- completion receipt distinguishes staged, installed, blocked, and validated packages.

## Codex Handoff

```text
Read collaboration/work_packages/pending/WP-4031_Resident_Runtime_Install_Handoff_and_Operational_Acceptance.md and do exactly what it says.
```
