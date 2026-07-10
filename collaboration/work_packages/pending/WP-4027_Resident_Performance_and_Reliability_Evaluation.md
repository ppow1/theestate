# WP-4027 — Resident Performance and Reliability Evaluation

Status: Pending
Workstream Mode: PARALLEL-INDEPENDENT
Owner: Resident Runtime Implementation Stream
Execution Target: Codex
Classification: Estate Internal

## Objective

Implement an isolated resident performance and reliability evaluation service that measures operational quality without directly changing active resident, Office, or model-control files.

## Conflict Surface

Expected source work is isolated under `collaboration/workstreams/WP-4027/`. Intended later integration targets are resident status, Helen workforce evidence, model evaluation, and Office reporting surfaces.

Conflict risk: low during staged development; medium during later installation.

## Staged Paths

Use only:

```text
collaboration/workstreams/WP-4027/
```

Create source, schemas, fixtures, tests, sample reports, integration notes, and `install_manifest.json`.

## Required Implementation

Evaluate:

- identity stability;
- role adherence;
- boundary compliance;
- unsupported claims;
- task-result quality;
- escalation quality;
- repeated failure patterns;
- response latency;
- provider fallback frequency;
- session recovery reliability;
- manual evaluator findings.

Separate measured evidence, interpretation, and recommended follow-up. Provide deterministic scoring only where justified; otherwise preserve categorical findings.

## Boundaries

Do not diagnose residents, impose workforce actions, change model assignments automatically, or convert evaluation into institutional acceptance. Do not require live providers for tests.

## Acceptance Criteria

- evaluation records are source-linked and reproducible;
- identity and boundary failures are visible;
- unsupported claims can be recorded distinctly from ordinary quality defects;
- Helen may consume evidence without automatic intervention;
- staged tests pass;
- manifest remains uninstalled.

## Required Install Handoff

WP-4031 installs only the approved reporting and evidence-consumption integrations.

## Codex Handoff

```text
Read collaboration/work_packages/pending/WP-4027_Resident_Performance_and_Reliability_Evaluation.md and do exactly what it says.
```
